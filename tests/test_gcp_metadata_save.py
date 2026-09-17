"""Retrying GCP common-metadata writes on a fingerprint conflict.

GCP keeps labels and key pairs in the project-wide common instance metadata,
which every write re-uploads under an optimistic fingerprint. A concurrent
writer makes the upload's *operation* fail with ``CONDITION_NOT_MET``; that
is a different path from an HTTP-level error, and the write has to be retried
with freshly fetched metadata on either. No SDK is involved: the compute
client is a fake and the provider's real ``wait_for_operation`` polls it.
"""

import unittest
from unittest import mock

import tenacity

from cloudbridge.providers.gcp.helpers import GCPOperationError
from cloudbridge.providers.gcp.helpers import gcp_metadata_save_op
from cloudbridge.providers.gcp.provider import GCPCloudProvider

FINGERPRINT_CONFLICT = {
    'errors': [{'code': 'CONDITION_NOT_MET',
                'message': 'Supplied fingerprint does not match current '
                           'metadata fingerprint.'}]}
OTHER_FAILURE = {
    'errors': [{'code': 'RESOURCE_NOT_FOUND',
                'message': "The resource 'projects/p' was not found"}]}


class _Call:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


class _FakeCompute:
    """Enough of the compute client for a metadata save: each save yields an
    operation whose outcome is the next entry in ``operation_results``."""

    def __init__(self, operation_results):
        self.operation_results = list(operation_results)
        self.fetches = 0
        self.saved_bodies = []

    # projects().get() / projects().setCommonInstanceMetadata()
    def projects(self):
        return self

    def get(self, project):
        self.fetches += 1
        return _Call({'commonInstanceMetadata': {
            'fingerprint': f'fp-{self.fetches}', 'items': []}})

    def setCommonInstanceMetadata(self, project, body):
        self.saved_bodies.append(body)
        return _Call({'name': f'op-{len(self.saved_bodies)}'})

    # globalOperations().get() - polled by wait_for_operation
    def globalOperations(self):
        return self

    def get_operation(self, project, operation):
        outcome = self.operation_results.pop(0)
        result = {'status': 'DONE'}
        if outcome is not None:
            result['error'] = outcome
        return _Call(result)


class _FakeProvider:
    project_name = 'p'
    wait_for_operation = GCPCloudProvider.wait_for_operation

    def __init__(self, operation_results):
        self.gcp_compute = _FakeCompute(operation_results)
        # wait_for_operation calls operations.get(**args); the fake's
        # get() is taken by projects().get(project=), so route it.
        self.gcp_compute.get = self._route_get

    def _route_get(self, **kwargs):
        if 'operation' in kwargs:
            return self.gcp_compute.get_operation(**kwargs)
        return _FakeCompute.get(self.gcp_compute, **kwargs)


def _save(provider, callback):
    # The production wait between attempts is exponential backoff; the test
    # is about whether a retry happens, not how long it waits.
    return gcp_metadata_save_op.retry_with(
        wait=tenacity.wait_none())(provider, callback)


class GCPMetadataSaveTestCase(unittest.TestCase):

    def test_fingerprint_conflict_is_retried_with_fresh_metadata(self):
        provider = _FakeProvider([FINGERPRINT_CONFLICT, None])
        callback = mock.Mock()

        _save(provider, callback)

        # Two attempts, each on metadata fetched anew so the retry carries
        # the fingerprint the conflict invalidated.
        self.assertEqual(provider.gcp_compute.fetches, 2)
        self.assertEqual(callback.call_count, 2)
        self.assertEqual(
            [body['fingerprint'] for body in provider.gcp_compute.saved_bodies],
            ['fp-1', 'fp-2'])

    def test_other_operation_failures_are_raised_as_typed_errors(self):
        provider = _FakeProvider([OTHER_FAILURE])
        callback = mock.Mock()

        with self.assertRaises(GCPOperationError) as raised:
            _save(provider, callback)

        self.assertEqual(callback.call_count, 1)
        self.assertEqual(raised.exception.codes, ['RESOURCE_NOT_FOUND'])
        self.assertIn("was not found", str(raised.exception))
