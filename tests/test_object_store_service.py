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
from cloudbridge.interfaces.provider import TestMockHelperMixin
from cloudbridge.interfaces.resources import Bucket
from cloudbridge.interfaces.resources import BucketObject

from tests import helpers
from tests.helpers import ProviderTestBase
from tests.helpers import standard_interface_tests as sit

# S3 (and Swift) require every part except the last to be >= 5 MiB. Tests use
# this size so they remain valid against real cloud providers, not just moto.
MIN_PART_SIZE = 5 * 1024 * 1024


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

            upload = obj.create_multipart_upload()
            upload.upload_part(1, b"a" * MIN_PART_SIZE)
            upload.abort()

            # Aborting must not materialise the target object.
            self.assertIsNone(
                test_bucket.objects.get(obj_name),
                "Object should not exist after a multipart upload is aborted")

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
