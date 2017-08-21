import filecmp
import os
import tempfile
import uuid

from datetime import datetime
from io import BytesIO
from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit
from unittest import skip

from cloudbridge.cloud.interfaces.resources import BucketObject

import requests


class CloudObjectStoreServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['object_store'])
    def test_crud_bucket(self):
        """
        Create a new bucket, check whether the expected values are set,
        and delete it.
        """
        name = "cbtestcreatebucket-{0}".format(uuid.uuid4())
        test_bucket = self.provider.object_store.create(name)
        with helpers.cleanup_action(lambda: test_bucket.delete()):
            sit.check_standard_behaviour(
                self, self.provider.object_store, test_bucket)

        sit.check_delete(self, self.provider.object_store, test_bucket)

    @helpers.skipIfNoService(['object_store'])
    def test_crud_bucket_objects(self):
        """
        Create a new bucket, upload some contents into the bucket, and
        check whether list properly detects the new content.
        Delete everything afterwards.
        """
        name = "cbtestbucketobjs-{0}".format(uuid.uuid4())
        test_bucket = self.provider.object_store.create(name)

        # ensure that the bucket is empty
        objects = test_bucket.list()
        self.assertEqual([], objects)

        with helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name_prefix = "hello"
            obj_name = obj_name_prefix + "_world.txt"
            obj = test_bucket.create_object(obj_name)

            with helpers.cleanup_action(lambda: obj.delete()):
                # TODO: This is wrong. We shouldn't have to have a separate
                # call to upload some content before being able to delete
                # the content. Maybe the create_object method should accept
                # the file content as a parameter.
                obj.upload("dummy content")
                objs = test_bucket.list()

                self.assertTrue(
                    isinstance(objs[0].size, int),
                    "Object size property needs to be a int, not {0}".format(
                        type(objs[0].size)))
                self.assertTrue(
                    datetime.strptime(objs[0].last_modified[:23],
                                      "%Y-%m-%dT%H:%M:%S.%f"),
                    "Object's last_modified field format {0} not matching."
                    .format(objs[0].last_modified))

                # check iteration
                iter_objs = list(test_bucket)
                self.assertListEqual(iter_objs, objs)

                sit.check_standard_behaviour(self, test_bucket, obj)

                obj_too = test_bucket.get(obj_name)
                self.assertTrue(
                    isinstance(obj_too, BucketObject),
                    "Did not get object {0} of expected type.".format(obj_too))

                prefix_filtered_list = test_bucket.list(prefix=obj_name_prefix)
                self.assertTrue(
                    len(objs) == len(prefix_filtered_list) == 1,
                    'The number of objects returned by list function, '
                    'with and without a prefix, are expected to be equal, '
                    'but its detected otherwise.')

            sit.check_delete(self, test_bucket, obj)

    @helpers.skipIfNoService(['object_store'])
    def test_upload_download_bucket_content(self):
        name = "cbtestbucketobjs-{0}".format(uuid.uuid4())
        test_bucket = self.provider.object_store.create(name)

        with helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "hello_upload_download.txt"
            obj = test_bucket.create_object(obj_name)

            with helpers.cleanup_action(lambda: obj.delete()):
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

    @skip("Skip until OpenStack implementation is provided")
    @helpers.skipIfNoService(['object_store'])
    def test_generate_url(self):
        name = "cbtestbucketobjs-{0}".format(uuid.uuid4())
        test_bucket = self.provider.object_store.create(name)

        with helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "hello_upload_download.txt"
            obj = test_bucket.create_object(obj_name)

            with helpers.cleanup_action(lambda: obj.delete()):
                content = b"Hello World. Generate a url."
                obj.upload(content)
                target_stream = BytesIO()
                obj.save_content(target_stream)

                url = obj.generate_url(100)
                self.assertEqual(requests.get(url).content, content)

    @helpers.skipIfNoService(['object_store'])
    def test_upload_download_bucket_content_from_file(self):
        name = "cbtestbucketobjs-{0}".format(uuid.uuid4())
        test_bucket = self.provider.object_store.create(name)

        with helpers.cleanup_action(lambda: test_bucket.delete()):
            obj_name = "hello_upload_download.txt"
            obj = test_bucket.create_object(obj_name)

            with helpers.cleanup_action(lambda: obj.delete()):
                test_file = os.path.join(
                    helpers.get_test_fixtures_folder(), 'logo.jpg')
                obj.upload_from_file(test_file)
                target_stream = BytesIO()
                obj.save_content(target_stream)
                with open(test_file, 'rb') as f:
                    self.assertEqual(target_stream.getvalue(), f.read())

    @skip("Skip unless you want to test swift objects bigger than 5 Gig")
    @helpers.skipIfNoService(['object_store'])
    def test_upload_download_bucket_content_with_large_file(self):
        """
        Creates a 6 Gig file in the temp directory, then uploads it to
        Swift. Once uploaded, then downloads to a new file in the temp
        directory and compares the two files to see if they match.
        """
        temp_dir = tempfile.gettempdir()
        file_name = '6GigTest.tmp'
        six_gig_file = os.path.join(temp_dir, file_name)
        with open(six_gig_file, "wb") as out:
            out.truncate(6 * 1024 * 1024 * 1024)  # 6 Gig...
        with helpers.cleanup_action(lambda: os.remove(six_gig_file)):
            download_file = "{0}/cbtestfile-{1}".format(temp_dir, file_name)
            bucket_name = "cbtestbucketlargeobjs-{0}".format(uuid.uuid4())
            test_bucket = self.provider.object_store.create(bucket_name)
            with helpers.cleanup_action(lambda: test_bucket.delete()):
                test_obj = test_bucket.create_object(file_name)
                with helpers.cleanup_action(lambda: test_obj.delete()):
                    file_uploaded = test_obj.upload_from_file(six_gig_file)
                    self.assertTrue(file_uploaded, "Could not upload object?")
                    with helpers.cleanup_action(
                            lambda: os.remove(download_file)):
                        with open(download_file, 'wb') as f:
                            test_obj.save_content(f)
                            self.assertTrue(
                                filecmp.cmp(six_gig_file, download_file),
                                "Uploaded file != downloaded")
