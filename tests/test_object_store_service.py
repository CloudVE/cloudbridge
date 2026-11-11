import filecmp
import os
import tempfile
from datetime import datetime
from io import BytesIO
from unittest import mock
from unittest import skip

import requests

from cloudbridge.base import helpers as cb_helpers
from cloudbridge.base.resources import BaseBucketObject
from cloudbridge.interfaces.exceptions import DuplicateResourceException
from cloudbridge.interfaces.exceptions import InvalidPartException
from cloudbridge.interfaces.provider import TestMockHelperMixin
from cloudbridge.interfaces.resources import Bucket
from cloudbridge.interfaces.resources import BucketObject
from cloudbridge.interfaces.resources import TransferConfig

from tests import helpers
from tests.helpers import ProviderTestBase
from tests.helpers import standard_interface_tests as sit

# S3 (and Swift) require every part except the last to be >= 5 MiB. Tests use
# this size so they remain valid against real cloud providers, not just moto.
MIN_PART_SIZE = 5 * 1024 * 1024


def _send(request, data):
    """Send ``data`` as a client holding nothing but the presigned ``request``."""
    return requests.request(request.method, request.url,
                            headers=request.headers, data=data)


def _remove_upload(bucket, name, upload):
    """Remove what an upload left: the object once completed, else its parts."""
    obj = bucket.objects.get(name)
    if obj:
        obj.delete()
    else:
        upload.abort()


class CloudObjectStoreServiceTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    @helpers.skipIfNoService(['storage._bucket_objects', 'storage.buckets'])
    def test_storage_services_event_pattern(self):
        # pylint:disable=protected-access
        self.assertEqual(
            self.provider.storage.buckets._service_event_pattern,
            "provider.storage.buckets",
            "Event pattern for {} service should be '{}', "
            "but found '{}'.".format("buckets",
                                     "provider.storage.buckets",
                                     self.provider.storage.buckets.
                                     _service_event_pattern))
        # pylint:disable=protected-access
        self.assertEqual(
            self.provider.storage._bucket_objects._service_event_pattern,
            "provider.storage._bucket_objects",
            "Event pattern for {} service should be '{}', "
            "but found '{}'.".format("bucket_objects",
                                     "provider.storage._bucket_objects",
                                     self.provider.storage._bucket_objects.
                                     _service_event_pattern))

    @helpers.skipIfNoService(['storage.buckets'])
    def test_crud_bucket(self):

        def create_bucket(name):
            return self.provider.storage.buckets.create(name)

        def cleanup_bucket(bucket):
            if bucket:
                bucket.delete()

        def extra_tests(bucket):
            # Recreating existing bucket should raise an exception
            with self.assertRaises(DuplicateResourceException):
                self.provider.storage.buckets.create(name=bucket.name)

        sit.check_crud(self, self.provider.storage.buckets, Bucket,
                       "cb-crudbucket", create_bucket, cleanup_bucket,
                       extra_test_func=extra_tests)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_crud_bucket_object(self):
        test_bucket = None

        def create_bucket_obj(name):
            obj = test_bucket.objects.create(name)
            # TODO: This is wrong. We shouldn't have to have a separate
            # call to upload some content before being able to delete
            # the content. Maybe the create_object method should accept
            # the file content as a parameter.
            obj.upload("dummy content")
            return obj

        def cleanup_bucket_obj(bucket_obj):
            if bucket_obj:
                bucket_obj.delete()

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            name = "cb-crudbucketobj-{0}".format(helpers.get_uuid())
            test_bucket = self.provider.storage.buckets.create(name)

            sit.check_crud(self, test_bucket.objects, BucketObject,
                           "cb-bucketobj", create_bucket_obj,
                           cleanup_bucket_obj, skip_name_check=True)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_crud_bucket_object_properties(self):
        # Create a new bucket, upload some contents into the bucket, and
        # check whether list properly detects the new content.
        # Delete everything afterwards.
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        # ensure that the bucket is empty
        objects = test_bucket.objects.list()
        self.assertEqual([], objects)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name_prefix = "hello"
            obj_name = obj_name_prefix + "_world.txt"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                # TODO: This is wrong. We shouldn't have to have a separate
                # call to upload some content before being able to delete
                # the content. Maybe the create_object method should accept
                # the file content as a parameter.
                obj.upload("dummy content")
                objs = test_bucket.objects.list()

                self.assertTrue(
                    isinstance(objs[0].size, int),
                    "Object size property needs to be a int, not {0}".format(
                        type(objs[0].size)))
                # GET an object as the size property implementation differs
                # for objects returned by LIST and GET.
                obj = test_bucket.objects.get(objs[0].id)
                self.assertTrue(
                    isinstance(objs[0].size, int),
                    "Object size property needs to be an int, not {0}".format(
                        type(obj.size)))
                self.assertTrue(
                    datetime.strptime(objs[0].last_modified[:23],
                                      "%Y-%m-%dT%H:%M:%S.%f"),
                    "Object's last_modified field format {0} not matching."
                    .format(objs[0].last_modified))

                # check iteration
                iter_objs = list(test_bucket.objects)
                self.assertListEqual(iter_objs, objs)

                obj_too = test_bucket.objects.get(obj_name)
                self.assertTrue(
                    isinstance(obj_too, BucketObject),
                    "Did not get object {0} of expected type.".format(obj_too))

                prefix_filtered_list = test_bucket.objects.list(
                    prefix=obj_name_prefix)
                self.assertTrue(
                    len(objs) == len(prefix_filtered_list) == 1,
                    'The number of objects returned by list function, '
                    'with and without a prefix, are expected to be equal, '
                    'but its detected otherwise.')

            sit.check_delete(self, test_bucket.objects, obj)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_upload_download_bucket_content(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "hello_upload_download.txt"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                content = b"Hello World. Here's some content."
                # TODO: Upload and download methods accept different parameter
                # types. Need to make this consistent - possibly provider
                # multiple methods like upload_from_file, from_stream etc.
                obj.upload(content)
                target_stream = BytesIO()
                obj.save_content(target_stream)
                self.assertEqual(target_stream.getvalue(), content)
                target_stream2 = BytesIO()
                for data in obj.iter_content():
                    target_stream2.write(data)
                self.assertEqual(target_stream2.getvalue(), content)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_iter_content_honours_chunk_size(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj = test_bucket.objects.create("chunked_binary.bin")

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                # Binary content with no newline in it at all: a reader that
                # chunks by line rather than by size hands this back as one
                # buffer, however large the object is.
                content = bytes(
                    b for b in range(256) if b != 0x0A) * 256   # ~64 KiB
                obj.upload(content)

                chunk_size = 4096
                chunks = list(obj.iter_content(chunk_size=chunk_size))

                self.assertEqual(
                    b"".join(chunks), content,
                    "Chunked read must reassemble to the original content.")
                self.assertTrue(
                    all(len(c) <= chunk_size for c in chunks),
                    "No chunk may exceed the requested chunk_size of {0}, but "
                    "sizes were {1}.".format(
                        chunk_size, sorted({len(c) for c in chunks})))
                self.assertGreaterEqual(
                    len(chunks), len(content) // chunk_size,
                    "A {0} byte object read at chunk_size={1} should yield at "
                    "least {2} chunks, but yielded {3}.".format(
                        len(content), chunk_size,
                        len(content) // chunk_size, len(chunks)))

    @helpers.skipIfNoService(['storage.buckets'])
    def test_iter_content_chunks_by_size_not_by_line(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj = test_bucket.objects.create("chunked_lines.txt")

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                # Newline every 10 bytes. Line-oriented chunking yields 10
                # byte chunks regardless of chunk_size; size-oriented
                # chunking fills each chunk.
                content = b"123456789\n" * 1000
                obj.upload(content)

                chunk_size = 1024
                chunks = list(obj.iter_content(chunk_size=chunk_size))

                self.assertEqual(b"".join(chunks), content)
                self.assertTrue(all(len(c) <= chunk_size for c in chunks))
                # Sizing by chunk_size needs ~10 chunks here; splitting on
                # newlines needs 1000. Allow slack for short reads, but not
                # two orders of magnitude of it.
                self.assertLessEqual(
                    len(chunks), 2 * -(-len(content) // chunk_size),
                    "A {0} byte object read at chunk_size={1} yielded {2} "
                    "chunks, far more than size-based chunking needs - "
                    "content is being split on newlines.".format(
                        len(content), chunk_size, len(chunks)))

    @helpers.skipIfNoService(['storage.buckets'])
    def test_iter_content_default_chunk_size(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj = test_bucket.objects.create("default_chunked.bin")

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                # Spans two default chunks, so the default actually reaches
                # the wire rather than being hidden by a one-chunk object.
                default = BaseBucketObject.CB_ITER_CHUNK_SIZE
                content = b"\x00\xff" * default   # 2 x the default chunk
                obj.upload(content)

                chunks = list(obj.iter_content())

                self.assertEqual(b"".join(chunks), content)
                self.assertTrue(
                    all(len(c) <= default for c in chunks),
                    "Chunks must not exceed the default chunk size.")
                self.assertLessEqual(
                    len(chunks), 2 * (len(content) // default),
                    "A {0} byte object should come back in about {1} chunks "
                    "at the {2} byte default, but came back in {3}.".format(
                        len(content), len(content) // default, default,
                        len(chunks)))

    @helpers.skipIfNoService(['storage.buckets'])
    def test_save_content_honours_chunk_size(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj = test_bucket.objects.create("saved_chunked.bin")

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                content = bytes(range(256)) * 100   # 25 KiB
                obj.upload(content)

                target_stream = BytesIO()
                obj.save_content(target_stream, chunk_size=1024)
                self.assertEqual(target_stream.getvalue(), content)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_generate_url(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "hello_upload_download.txt"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                content = b"Hello World. Generate a url."
                obj.upload(content)
                target_stream = BytesIO()
                obj.save_content(target_stream)

                url = obj.generate_url(100)
                if isinstance(self.provider, TestMockHelperMixin):
                    raise self.skipTest(
                        "Skipping rest of test - mock providers can't"
                        " access generated url")
                self.assertEqual(requests.get(url).content, content)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_generate_url_write_permissions(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "hello_upload_download.txt"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                content = b"Hello World. Generate a url."

                url = obj.generate_url(100, writable=True)
                if isinstance(self.provider, TestMockHelperMixin):
                    raise self.skipTest(
                        "Skipping rest of test - mock providers can't"
                        " access generated url")

                # Only Azure requires the x-ms-blob-type header to be present, but there's no harm
                # in sending this in for all providers.
                headers = {'x-ms-blob-type': 'BlockBlob'}
                response = requests.put(url, headers=headers, data=content)
                response.raise_for_status()

                obj = test_bucket.objects.get(obj_name)
                target_stream = BytesIO()
                obj.save_content(target_stream)
                self.assertEqual(target_stream.getvalue(), content)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_generate_url_with_response_headers(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "hello_response_headers.txt"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                content = b"Hello World. Serve me with response headers."
                obj.upload(content)

                disposition = 'attachment; filename="hello.txt"'
                content_type = "application/octet-stream"
                url = obj.generate_url(100,
                                       content_disposition=disposition,
                                       content_type=content_type)
                if isinstance(self.provider, TestMockHelperMixin):
                    # Presigned URLs are constructed client-side, so the
                    # response-header overrides can be asserted on the query
                    # string without a network round trip.
                    self.assertIn('response-content-disposition', url)
                    self.assertIn('response-content-type', url)
                    raise self.skipTest(
                        "Skipping rest of test - mock providers can't"
                        " access generated url")
                response = requests.get(url)
                self.assertEqual(response.content, content)
                got_disposition = response.headers.get(
                    'Content-Disposition', '')
                self.assertTrue(got_disposition.startswith('attachment'),
                                "Expected attachment disposition, got: "
                                f"{got_disposition}")
                self.assertIn('hello.txt', got_disposition)
                if self.provider.PROVIDER_ID != 'openstack':
                    # Swift's tempurl middleware cannot override Content-Type
                    # (it only honors the filename portion of the disposition
                    # via its `filename` query parameter).
                    self.assertEqual(response.headers.get('Content-Type'),
                                     content_type)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_generate_url_writable_ignores_response_headers(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "hello_response_headers.txt"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                url = obj.generate_url(
                    100, writable=True,
                    content_disposition='attachment; filename="hello.txt"',
                    content_type="application/octet-stream")
                # Response-header overrides only make sense for reads; a
                # writable URL must not carry them (across all providers:
                # AWS/GCP query params, Azure SAS rscd/rsct, Swift filename).
                self.assertNotIn('response-content-disposition', url)
                self.assertNotIn('rscd=', url)
                self.assertNotIn('filename=', url)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_upload_download_bucket_content_from_file(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "hello_upload_download.txt"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                test_file = os.path.join(
                    helpers.get_test_fixtures_folder(), 'logo.jpg')
                obj.upload_from_file(test_file)
                target_stream = BytesIO()
                obj.save_content(target_stream)
                with open(test_file, 'rb') as f:
                    self.assertEqual(target_stream.getvalue(), f.read())

    @helpers.skipIfNoService(['storage.buckets'])
    def test_explicit_multipart_upload_roundtrip(self):
        name = "cbtest-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "mpu-roundtrip.bin"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                part1 = b"a" * MIN_PART_SIZE
                part2 = b"b" * MIN_PART_SIZE
                part3 = b"c" * 1024  # final part may be smaller than the min
                expected = part1 + part2 + part3

                upload = obj.create_multipart_upload()
                parts = [upload.upload_part(1, part1),
                         upload.upload_part(2, part2),
                         upload.upload_part(3, part3)]
                upload.complete(parts)

                stored = test_bucket.objects.get(obj_name)
                self.assertIsNotNone(
                    stored, "Object should exist after multipart completion")
                self.assertEqual(stored.size, len(expected))
                target_stream = BytesIO()
                stored.save_content(target_stream)
                self.assertEqual(target_stream.getvalue(), expected)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_multipart_upload_out_of_order_parts(self):
        name = "cbtest-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "mpu-ooo.bin"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                part1 = b"1" * MIN_PART_SIZE
                part2 = b"2" * MIN_PART_SIZE
                part3 = b"3" * 1024
                expected = part1 + part2 + part3

                upload = obj.create_multipart_upload()
                # Upload and collect parts out of order; complete must
                # assemble them in ascending part-number order regardless.
                p3 = upload.upload_part(3, part3)
                p1 = upload.upload_part(1, part1)
                p2 = upload.upload_part(2, part2)
                upload.complete([p3, p1, p2])

                stored = test_bucket.objects.get(obj_name)
                target_stream = BytesIO()
                stored.save_content(target_stream)
                self.assertEqual(target_stream.getvalue(), expected)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_multipart_upload_abort(self):
        name = "cbtest-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "mpu-abort.bin"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                upload = obj.create_multipart_upload()
                upload.upload_part(1, b"a" * MIN_PART_SIZE)
                upload.abort()

                # Aborting must not commit any part data. Some providers
                # pre-materialise an empty placeholder on objects.create(), so
                # the target may be absent or empty afterwards -- but it must
                # never hold the uploaded part.
                stored = test_bucket.objects.get(obj_name)
                self.assertTrue(
                    stored is None or stored.size == 0,
                    "Aborted multipart upload must not commit any part data")

    @helpers.skipIfNoService(['storage.buckets'])
    def test_presigned_multipart_upload_roundtrip(self):
        name = "cbtest-presigned-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "presigned-mpu.bin"
            contents = [b"a" * MIN_PART_SIZE, b"b" * MIN_PART_SIZE, b"c" * 1024]
            upload = test_bucket.objects.create_multipart_upload(obj_name)

            with cb_helpers.cleanup_action(
                    lambda: _remove_upload(test_bucket, obj_name, upload)):
                etags = {}
                for part_number, content in enumerate(contents, start=1):
                    request = upload.generate_part_url(part_number, 300,
                                                       size=len(content))
                    response = _send(request, content)
                    response.raise_for_status()
                    etags[part_number] = response.headers.get('ETag')
                # Nobody sees the object until its upload completes.
                self.assertIsNone(test_bucket.objects.get(obj_name))

                # Completed later, as by another process, from the upload's id
                # and the ETags its uploader reported.
                reopened = test_bucket.objects.get_multipart_upload(
                    obj_name, upload.id)
                self.assertEqual(
                    [(part.part_number, part.size)
                     for part in reopened.list_parts()],
                    [(part_number, len(content)) for part_number, content
                     in enumerate(contents, start=1)])
                reopened.complete([reopened.reported_part(part_number, etag)
                                   for part_number, etag in etags.items()])

                stored = test_bucket.objects.get(obj_name)
                target_stream = BytesIO()
                stored.save_content(target_stream)
                self.assertEqual(target_stream.getvalue(), b"".join(contents))

    @helpers.skipIfNoService(['storage.buckets'])
    def test_presigned_part_replaced_after_its_upload_is_refused(self):
        # A part URL works until it expires, so the part its uploader sent
        # may have been replaced by the time the upload is completed.
        name = "cbtest-presigned-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "presigned-mpu-replaced.bin"
            upload = test_bucket.objects.create_multipart_upload(obj_name)

            with cb_helpers.cleanup_action(
                    lambda: _remove_upload(test_bucket, obj_name, upload)):
                request = upload.generate_part_url(1, 300)
                sent = _send(request, b"what the uploader sent")
                sent.raise_for_status()
                if sent.headers.get('ETag') is None:
                    self.skipTest("This provider's part uploads return no ETag"
                                  " to compare")
                _send(request, b"what replaced it").raise_for_status()

                with self.assertRaises(InvalidPartException):
                    upload.complete(
                        [upload.reported_part(1, sent.headers['ETag'])])
                self.assertIsNone(test_bucket.objects.get(obj_name))

    @helpers.skipIfNoService(['storage.buckets'])
    def test_reported_part_the_store_does_not_hold_is_refused(self):
        name = "cbtest-presigned-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "presigned-mpu-missing.bin"
            upload = test_bucket.objects.create_multipart_upload(obj_name)

            with cb_helpers.cleanup_action(
                    lambda: _remove_upload(test_bucket, obj_name, upload)):
                # Part 2 is uploaded; part 1 never is.
                sent = _send(upload.generate_part_url(2, 300), b"last part")
                sent.raise_for_status()
                etag = sent.headers.get('ETag')

                with self.assertRaises(InvalidPartException):
                    upload.complete([upload.reported_part(1, etag),
                                     upload.reported_part(2, etag)])
                self.assertIsNone(test_bucket.objects.get(obj_name))

    @helpers.skipIfNoService(['storage.buckets'])
    def test_part_reported_without_its_etag_is_refused(self):
        name = "cbtest-presigned-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "presigned-mpu-no-etag.bin"
            upload = test_bucket.objects.create_multipart_upload(obj_name)

            with cb_helpers.cleanup_action(
                    lambda: _remove_upload(test_bucket, obj_name, upload)):
                sent = _send(upload.generate_part_url(1, 300), b"only part")
                sent.raise_for_status()
                if sent.headers.get('ETag') is None:
                    self.skipTest("This provider's part uploads return no ETag"
                                  " to compare")

                with self.assertRaises(InvalidPartException):
                    upload.complete([upload.reported_part(1, None)])

    @helpers.skipIfNoService(['storage.buckets'])
    def test_presigned_upload_url_writes_a_new_object(self):
        name = "cbtestbucketobjs-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "presigned-upload.txt"
            content = b"Uploaded by a client without credentials."
            request = test_bucket.objects.generate_upload_url(
                obj_name, 300, size=len(content))
            # Signing the URL creates nothing.
            self.assertIsNone(test_bucket.objects.get(obj_name))
            # The signature stays out of logs.
            self.assertNotIn(request.url.split('?', 1)[1], repr(request))

            _send(request, content).raise_for_status()
            stored = test_bucket.objects.get(obj_name)
            with cb_helpers.cleanup_action(lambda: stored.delete()):
                target_stream = BytesIO()
                stored.save_content(target_stream)
                self.assertEqual(target_stream.getvalue(), content)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_presigned_urls_binding_a_size_refuse_another_size(self):
        if isinstance(self.provider, TestMockHelperMixin):
            self.skipTest("Mock providers don't check signatures")
        name = "cbtest-presigned-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "presigned-sized.bin"
            upload = test_bucket.objects.create_multipart_upload(obj_name)

            with cb_helpers.cleanup_action(
                    lambda: _remove_upload(test_bucket, obj_name, upload)):
                sized = [request for request in (
                    test_bucket.objects.generate_upload_url(obj_name, 300,
                                                            size=5),
                    upload.generate_part_url(1, 300, size=5))
                    if request.enforces_size]
                if not sized:
                    self.skipTest("This provider's presigned URLs can't bind"
                                  " a size")
                for request in sized:
                    self.assertFalse(_send(request, b"more than five").ok)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_transparent_upload_large_stream_uses_multipart(self):
        name = "cbtest-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "transparent.bin"
            obj = test_bucket.objects.create(obj_name)

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                content = b"x" * (MIN_PART_SIZE * 2 + 1024)

                # Lower the threshold/part size so a modest stream crosses it,
                # and assert the multipart path is taken (each provider routes
                # its own way underneath) and the object round-trips exactly.
                with mock.patch.object(
                        BaseBucketObject, 'CB_MULTIPART_THRESHOLD',
                        MIN_PART_SIZE), \
                    mock.patch.object(
                        BaseBucketObject, 'CB_MULTIPART_PART_SIZE',
                        MIN_PART_SIZE), \
                    mock.patch.object(
                        obj, '_upload_multipart',
                        wraps=obj._upload_multipart) as spy:
                    obj.upload(BytesIO(content))

                spy.assert_called_once()
                stored = test_bucket.objects.get(obj_name)
                self.assertEqual(stored.size, len(content))
                target_stream = BytesIO()
                stored.save_content(target_stream)
                self.assertEqual(target_stream.getvalue(), content)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_small_upload_stays_single_shot(self):
        name = "cbtest-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj = test_bucket.objects.create("small.txt")

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                content = b"a small payload below the multipart threshold"

                # A payload below the threshold must not trigger multipart.
                svc = self.provider.storage._bucket_objects
                with mock.patch.object(
                        svc, 'create_multipart_upload',
                        wraps=svc.create_multipart_upload) as spy:
                    obj.upload(content)

                spy.assert_not_called()
                target_stream = BytesIO()
                obj.save_content(target_stream)
                self.assertEqual(target_stream.getvalue(), content)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_upload_from_file_uses_multipart_config(self):
        # AWS drives boto3's TransferManager with CloudBridge's multipart
        # knobs (not boto3's own defaults). This wiring is AWS-specific.
        if self.provider.PROVIDER_ID not in ('aws', 'mock'):
            self.skipTest("TransferConfig wiring is specific to AWS")
        from boto3.s3.transfer import TransferConfig as S3TransferConfig

        name = "cbtest-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj = test_bucket.objects.create("config.bin")

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                test_file = os.path.join(
                    helpers.get_test_fixtures_folder(), 'logo.jpg')
                # pylint:disable=protected-access
                with mock.patch.object(
                        BaseBucketObject, 'CB_MULTIPART_PART_SIZE',
                        7 * 1024 * 1024), \
                    mock.patch.object(
                        BaseBucketObject, 'CB_MULTIPART_MAX_CONCURRENCY', 3), \
                    mock.patch.object(
                        obj._obj, 'upload_file',
                        wraps=obj._obj.upload_file) as spy:
                    obj.upload_from_file(test_file)

                spy.assert_called_once()
                config = spy.call_args.kwargs['Config']
                self.assertIsInstance(config, S3TransferConfig)
                self.assertEqual(config.multipart_chunksize, 7 * 1024 * 1024)
                self.assertEqual(config.max_concurrency, 3)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_per_call_upload_config_overrides_defaults(self):
        # A per-call TransferConfig takes precedence over the global knobs.
        if self.provider.PROVIDER_ID not in ('aws', 'mock'):
            self.skipTest("TransferConfig wiring is specific to AWS")
        from boto3.s3.transfer import TransferConfig as S3TransferConfig

        name = "cbtest-mpu-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj = test_bucket.objects.create("percall.bin")

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                test_file = os.path.join(
                    helpers.get_test_fixtures_folder(), 'logo.jpg')
                cfg = TransferConfig(part_size=8 * 1024 * 1024,
                                     max_concurrency=2)
                # pylint:disable=protected-access
                with mock.patch.object(
                        obj._obj, 'upload_file',
                        wraps=obj._obj.upload_file) as spy:
                    obj.upload_from_file(test_file, config=cfg)

                config = spy.call_args.kwargs['Config']
                self.assertIsInstance(config, S3TransferConfig)
                self.assertEqual(config.multipart_chunksize, 8 * 1024 * 1024)
                self.assertEqual(config.max_concurrency, 2)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_download_to_file_roundtrip(self):
        name = "cbtest-dl-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj = test_bucket.objects.create("roundtrip.txt")

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                content = b"a small payload below the download threshold"
                obj.upload(content)

                stored = test_bucket.objects.get("roundtrip.txt")
                fd, path = tempfile.mkstemp()
                os.close(fd)
                with cb_helpers.cleanup_action(lambda: os.remove(path)):
                    stored.download_to_file(path)
                    with open(path, 'rb') as f:
                        self.assertEqual(f.read(), content)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_transparent_download_large_uses_ranged(self):
        name = "cbtest-dl-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj = test_bucket.objects.create("ranged.bin")

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                # Distinct byte pattern so out-of-order reassembly would show.
                content = bytes(range(256)) * ((MIN_PART_SIZE * 2) // 256)
                obj.upload(BytesIO(content),
                           TransferConfig(threshold=MIN_PART_SIZE,
                                          part_size=MIN_PART_SIZE))

                stored = test_bucket.objects.get("ranged.bin")
                fd, path = tempfile.mkstemp()
                os.close(fd)
                with cb_helpers.cleanup_action(lambda: os.remove(path)):
                    # Lower the threshold so the download crosses it (each
                    # provider routes its own way underneath) and assert the
                    # content round-trips exactly.
                    stored.download_to_file(
                        path, TransferConfig(threshold=MIN_PART_SIZE,
                                             part_size=MIN_PART_SIZE,
                                             max_concurrency=2))
                    with open(path, 'rb') as f:
                        self.assertEqual(f.read(), content)

    @helpers.skipIfNoService(['storage.buckets'])
    def test_download_to_file_uses_transfer_config(self):
        # AWS drives boto3's TransferManager with CloudBridge's transfer
        # knobs (not boto3's own defaults). This wiring is AWS-specific.
        if self.provider.PROVIDER_ID not in ('aws', 'mock'):
            self.skipTest("TransferConfig wiring is specific to AWS")
        from boto3.s3.transfer import TransferConfig as S3TransferConfig

        name = "cbtest-dl-{0}".format(helpers.get_uuid())
        test_bucket = self.provider.storage.buckets.create(name)

        with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
            obj = test_bucket.objects.create("dlconfig.bin")

            with cb_helpers.cleanup_action(lambda: obj.delete()):
                obj.upload(b"some downloadable content")
                stored = test_bucket.objects.get("dlconfig.bin")

                fd, path = tempfile.mkstemp()
                os.close(fd)
                with cb_helpers.cleanup_action(lambda: os.remove(path)):
                    cfg = TransferConfig(part_size=8 * 1024 * 1024,
                                         max_concurrency=2)
                    # pylint:disable=protected-access
                    with mock.patch.object(
                            stored._obj.meta.client, 'download_file',
                            wraps=stored._obj.meta.client
                            .download_file) as spy:
                        stored.download_to_file(path, config=cfg)

                    spy.assert_called_once()
                    config = spy.call_args.kwargs['Config']
                    self.assertIsInstance(config, S3TransferConfig)
                    self.assertEqual(
                        config.multipart_chunksize, 8 * 1024 * 1024)
                    self.assertEqual(config.max_concurrency, 2)
                    with open(path, 'rb') as f:
                        self.assertEqual(
                            f.read(), b"some downloadable content")

    @skip("Skip unless you want to test objects bigger than 5GB")
    @helpers.skipIfNoService(['storage.buckets'])
    def test_upload_download_bucket_content_with_large_file(self):
        # Creates a 6 Gig file in the temp directory, then uploads it to
        # Swift. Once uploaded, then downloads to a new file in the temp
        # directory and compares the two files to see if they match.
        temp_dir = tempfile.gettempdir()
        file_name = '6GigTest.tmp'
        six_gig_file = os.path.join(temp_dir, file_name)
        with open(six_gig_file, "wb") as out:
            out.truncate(6 * 1024 * 1024 * 1024)  # 6 Gig...
        with cb_helpers.cleanup_action(lambda: os.remove(six_gig_file)):
            download_file = "{0}/cbtestfile-{1}".format(temp_dir, file_name)
            bucket_name = "cbtestbucketlargeobjs-{0}".format(
                                                            helpers.get_uuid())
            test_bucket = self.provider.storage.buckets.create(bucket_name)
            with cb_helpers.cleanup_action(lambda: test_bucket.delete()):
                test_obj = test_bucket.objects.create(file_name)
                with cb_helpers.cleanup_action(lambda: test_obj.delete()):
                    file_uploaded = test_obj.upload_from_file(six_gig_file)
                    self.assertTrue(file_uploaded, "Could not upload object?")
                    with cb_helpers.cleanup_action(
                            lambda: os.remove(download_file)):
                        with open(download_file, 'wb') as f:
                            test_obj.save_content(f)
                            self.assertTrue(
                                filecmp.cmp(six_gig_file, download_file),
                                "Uploaded file != downloaded")
