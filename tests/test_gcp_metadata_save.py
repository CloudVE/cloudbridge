"""Making GCP common-metadata writes stick.

GCP keeps labels and key pairs in the project-wide common instance metadata,
which every write re-uploads under an optimistic fingerprint. Under
concurrent writers two things happen that a write has to survive: the
operation fails with ``CONDITION_NOT_MET`` (a different path from the
HTTP-level 412), and - observed in the live suite - the operation reports
``DONE`` yet the change is absent from the document afterwards. Both must
lead to the write being re-applied on freshly fetched metadata. No SDK is
involved: the compute client is a fake with a server-side document, and the
provider's real ``wait_for_operation`` polls it.
"""

import unittest
from unittest import mock

import tenacity

from cloudbridge.interfaces.exceptions import DuplicateResourceException
from cloudbridge.providers.gcp.helpers import GCPOperationError
from cloudbridge.providers.gcp.helpers import MetadataWriteNotApplied
from cloudbridge.providers.gcp.helpers import add_metadata_item
from cloudbridge.providers.gcp.helpers import gcp_metadata_save_op
from cloudbridge.providers.gcp.helpers import modify_or_add_metadata_item
from cloudbridge.providers.gcp.helpers import remove_metadata_item
from cloudbridge.providers.gcp.provider import GCPCloudProvider

FINGERPRINT_CONFLICT = {
    'errors': [{'code': 'CONDITION_NOT_MET',
                'message': 'Supplied fingerprint does not match current '
                           'metadata fingerprint.'}]}
OTHER_FAILURE = {
    'errors': [{'code': 'RESOURCE_NOT_FOUND',
                'message': "The resource 'projects/p' was not found"}]}

# Scripted outcomes for successive set operations.
APPLY = 'apply'        # the write lands and the fingerprint moves on
LOST = 'lost'          # reported DONE, but nothing changed
CONFLICT = 'conflict'  # CONDITION_NOT_MET, nothing changed


class _Call:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


class _FakeCompute:
    """A compute client holding one project metadata document.

    ``projects().get()`` returns a copy of the document; each
    ``setCommonInstanceMetadata()`` yields an operation whose fate is the
    next entry in ``outcomes``, resolved when ``wait_for_operation`` polls
    ``globalOperations().get()``.
    """

    def __init__(self, outcomes, items=None):
        self.outcomes = list(outcomes)
        self.document = {'fingerprint': 'fp-0',
                         'items': list(items or [])}
        self.version = 0
        self.fetches = 0
        self.saved_bodies = []
        self._pending = {}

    def projects(self):
        return self

    def globalOperations(self):
        return self

    def get(self, project, operation=None):
        if operation is not None:
            return self._resolve(operation)
        self.fetches += 1
        return _Call({'commonInstanceMetadata': {
            'fingerprint': self.document['fingerprint'],
            'items': [dict(i) for i in self.document['items']]}})

    def setCommonInstanceMetadata(self, project, body):
        self.saved_bodies.append(body)
        name = 'op-%d' % len(self.saved_bodies)
        self._pending[name] = body
        return _Call({'name': name})

    def _resolve(self, name):
        body = self._pending.pop(name)
        outcome = self.outcomes.pop(0)
        result = {'status': 'DONE'}
        if outcome == APPLY:
            self.version += 1
            self.document = {'fingerprint': 'fp-%d' % self.version,
                             'items': [dict(i) for i in body['items']]}
        elif outcome == CONFLICT:
            result['error'] = FINGERPRINT_CONFLICT
        elif outcome == LOST:
            pass
        else:
            result['error'] = outcome
        return _Call(result)

    def keys(self):
        return {i['key']: i['value'] for i in self.document['items']}


class _FakeProvider:
    project_name = 'p'
    wait_for_operation = GCPCloudProvider.wait_for_operation

    def __init__(self, outcomes, items=None):
        self.gcp_compute = _FakeCompute(outcomes, items)


class GCPMetadataSaveTestCase(unittest.TestCase):

    def setUp(self):
        # The production wait between attempts is exponential backoff; these
        # tests are about whether a retry happens, not how long it waits.
        patcher = mock.patch.object(gcp_metadata_save_op.retry, 'wait',
                                    tenacity.wait_none())
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_fingerprint_conflict_is_retried_with_fresh_metadata(self):
        provider = _FakeProvider([CONFLICT, APPLY])
        callback = mock.Mock(side_effect=lambda md: md['items'].append(
            {'key': 'k', 'value': 'v'}))

        gcp_metadata_save_op(provider, callback)

        # Two attempts, each on metadata fetched anew so the retry carries
        # the fingerprint the conflict invalidated.
        self.assertEqual(callback.call_count, 2)
        self.assertEqual(
            [b['fingerprint'] for b in provider.gcp_compute.saved_bodies],
            ['fp-0', 'fp-0'])
        self.assertEqual(provider.gcp_compute.keys(), {'k': 'v'})

    def test_write_reported_done_but_absent_is_reapplied(self):
        # The live suite showed operations completing as DONE with the
        # change missing from the document. A write is only finished once
        # it can be read back.
        provider = _FakeProvider([LOST, APPLY])

        modify_or_add_metadata_item(provider, 'k', 'v')

        self.assertEqual(len(provider.gcp_compute.saved_bodies), 2)
        self.assertEqual(provider.gcp_compute.keys(), {'k': 'v'})

    def test_write_that_never_lands_is_reported_after_retries(self):
        provider = _FakeProvider([LOST] * 10)

        with self.assertRaises(MetadataWriteNotApplied) as raised:
            modify_or_add_metadata_item(provider, 'k', 'v')

        self.assertIn('k', str(raised.exception))
        self.assertEqual(len(provider.gcp_compute.saved_bodies), 10)

    def test_other_operation_failures_are_raised_as_typed_errors(self):
        provider = _FakeProvider([OTHER_FAILURE])
        callback = mock.Mock(side_effect=lambda md: md['items'].append(
            {'key': 'k', 'value': 'v'}))

        with self.assertRaises(GCPOperationError) as raised:
            gcp_metadata_save_op(provider, callback)

        self.assertEqual(callback.call_count, 1)
        self.assertEqual(raised.exception.codes, ['RESOURCE_NOT_FOUND'])
        self.assertIn("was not found", str(raised.exception))

    def test_a_write_that_changes_nothing_is_not_sent(self):
        # Every set re-uploads the whole document and moves the fingerprint,
        # so a no-op (removing an absent key, re-setting the current value)
        # would only add contention for other writers.
        provider = _FakeProvider([], items=[{'key': 'k', 'value': 'v'}])

        self.assertFalse(remove_metadata_item(provider, 'absent'))
        modify_or_add_metadata_item(provider, 'k', 'v')

        self.assertEqual(provider.gcp_compute.saved_bodies, [])

    def test_remove_is_reapplied_until_the_key_is_gone(self):
        provider = _FakeProvider([LOST, APPLY],
                                 items=[{'key': 'k', 'value': 'v'}])

        self.assertTrue(remove_metadata_item(provider, 'k'))

        self.assertEqual(len(provider.gcp_compute.saved_bodies), 2)
        self.assertEqual(provider.gcp_compute.keys(), {})

    def test_add_is_satisfied_by_its_own_value_already_present(self):
        # A retry must not append a second copy if the earlier attempt did
        # land after all.
        provider = _FakeProvider([], items=[{'key': 'k', 'value': 'v'}])

        add_metadata_item(provider, 'k', 'v')

        self.assertEqual(provider.gcp_compute.saved_bodies, [])

    def test_add_rejects_a_key_someone_else_holds(self):
        provider = _FakeProvider([], items=[{'key': 'k', 'value': 'theirs'}])

        with self.assertRaises(DuplicateResourceException):
            add_metadata_item(provider, 'k', 'mine')

        self.assertEqual(provider.gcp_compute.saved_bodies, [])
