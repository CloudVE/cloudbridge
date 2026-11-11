"""Which key Swift temporary URLs are signed with.

Swift accepts a temporary URL signed with one of the keys set on the account.
cloudbridge signs with the key the operator set, and sets a key of its own only
on an account without one. Earlier versions set the same published key on every
account they signed a URL for, replacing the operator's, so that anyone could
sign URLs for that account: an account still holding that key gets a new one.
Nothing here touches a network: the Swift account is held in memory.
"""

import hashlib
import hmac
import unittest
from unittest import mock
from urllib.parse import parse_qs
from urllib.parse import unquote
from urllib.parse import urlsplit

from cloudbridge.providers.openstack.provider import OpenStackCloudProvider
from cloudbridge.providers.openstack.resources import OpenStackBucket
from cloudbridge.providers.openstack.resources import OpenStackBucketObject

KEY = 'x-account-meta-temp-url-key'
KEY_2 = 'x-account-meta-temp-url-key-2'
# The key cloudbridge 4.4 and earlier set on every account.
PUBLISHED_KEY = 'cloudbridge-tmp-url-key'


class _SwiftAccount(object):
    """The account calls of a swiftclient Connection, on an account in memory."""

    url = 'https://swift.example.org:8080/v1/AUTH_project'

    def __init__(self, **metadata):
        self.metadata = metadata

    def head_account(self):
        return dict(self.metadata)

    def post_account(self, headers):
        self.metadata.update({k.lower(): v for k, v in headers.items()})

    def get_service_auth(self):
        return self.url, 'token'


def _signed_with(url, method, key):
    """Whether Swift's tempurl middleware would accept ``url`` under ``key``."""
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    body = '\n'.join([method, query['temp_url_expires'][0],
                      unquote(parts.path)])
    expected = hmac.new(key.encode(), body.encode(), hashlib.sha256)
    return hmac.compare_digest(expected.hexdigest(),
                               query['temp_url_sig'][0])


class SwiftTempUrlKeyTestCase(unittest.TestCase):

    def _bucket(self, account):
        provider = OpenStackCloudProvider({
            'os_auth_url': 'https://keystone.example.org:5000/v3',
            'os_zone_name': 'nova'})
        patcher = mock.patch.object(OpenStackCloudProvider, 'swift',
                                    new_callable=mock.PropertyMock,
                                    return_value=account)
        patcher.start()
        self.addCleanup(patcher.stop)
        return OpenStackBucket(provider, {'name': 'outputs'})

    def _object_url(self, account):
        bucket = self._bucket(account)
        obj = OpenStackBucketObject(bucket._provider, bucket,
                                    {'name': 'dataset.dat'})
        return obj.generate_url(300)

    def test_urls_are_signed_with_the_key_the_operator_set(self):
        account = _SwiftAccount(**{KEY: 'operator-key'})

        url = self._object_url(account)

        self.assertTrue(_signed_with(url, 'GET', 'operator-key'))
        self.assertEqual(account.metadata, {KEY: 'operator-key'})

    def test_urls_are_signed_with_the_second_key_when_only_it_is_set(self):
        account = _SwiftAccount(**{KEY_2: 'operator-key'})

        url = self._object_url(account)

        self.assertTrue(_signed_with(url, 'GET', 'operator-key'))
        self.assertEqual(account.metadata, {KEY_2: 'operator-key'})

    def test_an_account_without_a_key_gets_a_random_one_kept_for_later(self):
        first_account, second_account = _SwiftAccount(), _SwiftAccount()

        urls = [self._object_url(first_account),
                self._object_url(first_account)]
        self._object_url(second_account)

        key = first_account.metadata[KEY]
        self.assertTrue(all(_signed_with(url, 'GET', key) for url in urls))
        self.assertNotEqual(key, PUBLISHED_KEY)
        self.assertNotEqual(key, second_account.metadata[KEY])

    def test_the_published_key_earlier_versions_set_is_replaced(self):
        account = _SwiftAccount(**{KEY: PUBLISHED_KEY,
                                   KEY_2: 'operator-key'})

        url = self._object_url(account)

        key = account.metadata[KEY]
        self.assertNotEqual(key, PUBLISHED_KEY)
        self.assertTrue(_signed_with(url, 'GET', key))
        self.assertEqual(account.metadata[KEY_2], 'operator-key')

    def test_presigned_uploads_are_signed_with_the_operators_key(self):
        account = _SwiftAccount(**{KEY: 'operator-key'})
        bucket = self._bucket(account)
        upload = bucket.objects.create_multipart_upload('dataset.dat')

        requests = [bucket.objects.generate_upload_url('dataset.dat', 300),
                    upload.generate_part_url(1, 300)]

        for request in requests:
            self.assertTrue(_signed_with(request.url, 'PUT', 'operator-key'))
        self.assertEqual(account.metadata, {KEY: 'operator-key'})
