"""Uploads to GCS through signed requests.

A signed request must be signed as GCS checks it, the headers it signs
included. GCS has no multipart API: cloudbridge uploads each part as a temporary object
and composes the parts. A client without credentials uploads a part through a
signed URL, which it can send again until it expires, and reports the ETag GCS
returned: the part's MD5. Completing the upload checks each part against its
report, and composes only the generation it checked. Nothing here touches a
network: the storage client is the real one, over an HTTP layer that answers as
GCS's JSON API does, from objects held in memory.
"""

import base64
import hashlib
import itertools
import json
import re
import unittest
from unittest import mock
from urllib.parse import parse_qs
from urllib.parse import quote
from urllib.parse import unquote
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa

from google.oauth2.service_account import Credentials

from googleapiclient import discovery

import httplib2

from cloudbridge.interfaces.exceptions import InvalidPartException
from cloudbridge.providers.gcp import helpers
from cloudbridge.providers.gcp.provider import GCPCloudProvider
from cloudbridge.providers.gcp.resources import GCPBucket

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_SERVICE_ACCOUNT = {
    'type': 'service_account',
    'project_id': 'cb-test',
    'client_email': 'cloudbridge@cb-test.iam.gserviceaccount.com',
    'client_id': '1',
    'private_key_id': '1',
    'private_key': _KEY.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()).decode(),
    'token_uri': 'https://oauth2.googleapis.com/token',
}


def _signed_as_gcs_checks(url, method, headers):
    """Whether GCS would accept a V4 signed ``url`` sent with ``headers``."""
    parts = urlsplit(url)
    query = {k: v[0] for k, v in parse_qs(parts.query).items()}
    signature = query.pop('x-goog-signature')
    sent = dict({k.lower(): v for k, v in headers.items()},
                host=parts.hostname)
    signed = query['X-Goog-SignedHeaders'].split(';')
    canonical_request = '\n'.join([
        method, parts.path,
        '&'.join('{0}={1}'.format(quote(k, safe=''), quote(v, safe=''))
                 for k, v in sorted(query.items())),
        ''.join('{0}:{1}\n'.format(name, ' '.join(sent[name].split()))
                for name in signed),
        ';'.join(signed), 'UNSIGNED-PAYLOAD'])
    string_to_sign = '\n'.join([
        'GOOG4-RSA-SHA256', query['X-Goog-Date'],
        query['X-Goog-Credential'].split('/', 1)[1],
        hashlib.sha256(canonical_request.encode()).hexdigest()])
    try:
        _KEY.public_key().verify(bytes.fromhex(signature),
                                 string_to_sign.encode(), padding.PKCS1v15(),
                                 hashes.SHA256())
        return True
    except InvalidSignature:
        return False


_OBJECT_PATH = re.compile(r'/storage/v1/b/([^/]+)/o(?:/([^/]+))?(/compose)?$')


class _FakeGcs(object):
    """One GCS bucket, in memory.

    It answers the JSON API requests of a googleapiclient storage client, and
    ``put`` stores an object as a client sending a signed PUT would.
    """

    def __init__(self, bucket):
        self.bucket = bucket
        # name -> (data, generation)
        self.objects = {}
        self._generations = itertools.count(1)
        # Run once, as the next compose request arrives.
        self.before_compose = None

    def put(self, request, data):
        """Send ``request`` with ``data``; return the ETag GCS answers with."""
        url = urlsplit(request.url)
        assert url.hostname == self.bucket + '.storage.googleapis.com'
        self._store(unquote(url.path[1:]), data)
        return '"{0}"'.format(hashlib.md5(data).hexdigest())

    def request(self, uri, method='GET', body=None, headers=None, **kwargs):
        url = urlsplit(uri)
        match = _OBJECT_PATH.match(url.path)
        assert match and match.group(1) == self.bucket, uri
        name = unquote(match.group(2)) if match.group(2) else None
        if name is None:
            prefix = parse_qs(url.query).get('prefix', [''])[0]
            return self._answer(200, {'items': [
                self._resource(n) for n in sorted(self.objects)
                if n.startswith(prefix)]})
        if match.group(3):
            return self._compose(name, json.loads(body)['sourceObjects'])
        if name not in self.objects:
            return self._answer(404, {'error': {'code': 404}})
        if method == 'DELETE':
            del self.objects[name]
            return self._answer(204, None)
        return self._answer(200, self._resource(name))

    def _compose(self, destination, sources):
        if self.before_compose:
            before_compose, self.before_compose = self.before_compose, None
            before_compose()
        for source in sources:
            if source['name'] not in self.objects:
                return self._answer(404, {'error': {'code': 404}})
            generation = source.get('objectPreconditions', {}).get(
                'ifGenerationMatch')
            if (generation is not None and
                    int(generation) != self.objects[source['name']][1]):
                return self._answer(412, {'error': {'code': 412}})
        self._store(destination, b''.join(
            self.objects[source['name']][0] for source in sources))
        return self._answer(200, self._resource(destination))

    def _store(self, name, data):
        self.objects[name] = (data, next(self._generations))

    def _resource(self, name):
        data, generation = self.objects[name]
        return {'kind': 'storage#object', 'bucket': self.bucket,
                'name': name, 'size': str(len(data)),
                'generation': str(generation),
                'md5Hash': base64.b64encode(
                    hashlib.md5(data).digest()).decode()}

    @staticmethod
    def _answer(status, content):
        body = b'' if content is None else json.dumps(content).encode()
        return httplib2.Response({'status': str(status)}), body


class GCSReportedPartsTestCase(unittest.TestCase):

    def setUp(self):
        self.gcs = _FakeGcs('outputs')
        for service in ('storage', 'compute'):
            patcher = mock.patch.object(
                GCPCloudProvider, 'gcp_' + service,
                new_callable=mock.PropertyMock,
                return_value=discovery.build(service, 'v1', http=self.gcs,
                                             static_discovery=True))
            patcher.start()
            self.addCleanup(patcher.stop)
        provider = GCPCloudProvider({
            'gcp_service_creds_dict': _SERVICE_ACCOUNT,
            'gcp_zone_name': 'us-central1-a'})
        self.bucket = GCPBucket(provider, {'name': 'outputs'})
        self.upload = self.bucket.objects.create_multipart_upload(
            'dataset.dat')

    def _upload_part(self, part_number, data):
        return self.gcs.put(self.upload.generate_part_url(part_number, 300),
                            data)

    def _complete(self, reports):
        self.upload.complete([self.upload.reported_part(part_number, etag)
                              for part_number, etag in reports])

    def test_parts_complete_into_the_object_their_uploaders_reported(self):
        reports = [(1, self._upload_part(1, b'first ')),
                   (2, self._upload_part(2, b'and second'))]
        self.assertEqual([(part.part_number, part.size)
                          for part in self.upload.list_parts()],
                         [(1, 6), (2, 10)])

        self._complete(reports)

        # The temporary part objects are gone.
        self.assertEqual(list(self.gcs.objects), ['dataset.dat'])
        self.assertEqual(self.gcs.objects['dataset.dat'][0],
                         b'first and second')

    def test_more_parts_than_one_compose_takes(self):
        contents = [str(n).encode() for n in range(1, 41)]
        reports = [(part_number, self._upload_part(part_number, content))
                   for part_number, content in enumerate(contents, start=1)]

        self._complete(reports)

        self.assertEqual(list(self.gcs.objects), ['dataset.dat'])
        self.assertEqual(self.gcs.objects['dataset.dat'][0],
                         b''.join(contents))

    def test_a_part_replaced_since_its_upload_is_refused(self):
        etag = self._upload_part(1, b'what the uploader sent')
        self._upload_part(1, b'what replaced it')

        with self.assertRaises(InvalidPartException):
            self._complete([(1, etag)])
        self.assertNotIn('dataset.dat', self.gcs.objects)

    def test_a_part_never_uploaded_is_refused(self):
        etag = self._upload_part(2, b'last part')

        with self.assertRaises(InvalidPartException):
            self._complete([(1, etag), (2, etag)])
        self.assertNotIn('dataset.dat', self.gcs.objects)

    def test_a_part_replaced_while_the_upload_completes_is_refused(self):
        request = self.upload.generate_part_url(1, 300)
        etag = self.gcs.put(request, b'what the uploader sent')
        # Replaced once cloudbridge has checked it, before GCS composes it.
        self.gcs.before_compose = lambda: self.gcs.put(
            request, b'what replaced it')

        with self.assertRaises(InvalidPartException):
            self._complete([(1, etag)])
        self.assertNotIn('dataset.dat', self.gcs.objects)


class GCSSignedRequestTestCase(unittest.TestCase):

    def test_upload_urls_sign_the_size_they_bind(self):
        provider = GCPCloudProvider({
            'gcp_service_creds_dict': _SERVICE_ACCOUNT,
            'gcp_zone_name': 'us-central1-a'})
        bucket = GCPBucket(provider, {'name': 'outputs'})

        request = bucket.objects.generate_upload_url('a dir/dataset.dat', 300,
                                                     size=5)

        self.assertTrue(request.enforces_size)
        self.assertTrue(_signed_as_gcs_checks(request.url, 'PUT',
                                              request.headers))
        self.assertFalse(_signed_as_gcs_checks(
            request.url, 'PUT', {'x-goog-content-length-range': '0,50'}))

    def test_signed_header_values_keep_their_case(self):
        headers = {'x-goog-meta-label': 'Mixed  Case'}

        url = helpers.generate_signed_url(
            Credentials.from_service_account_info(_SERVICE_ACCOUNT),
            'outputs', 'dataset.dat', expiration=300, http_method='PUT',
            headers=dict(headers))

        self.assertTrue(_signed_as_gcs_checks(url, 'PUT', headers))
