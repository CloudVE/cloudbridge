from io import BytesIO
import uuid

from test.helpers import ProviderTestBase
import test.helpers as helpers


class CloudObjectStoreServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(CloudObjectStoreServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_crud_bucket(self):
        """
        Create a new bucket, check whether the expected values are set,
        and delete it.
        """
        name = "cbtestcreatebucket-{0}".format(uuid.uuid4())
        test_bucket = self.provider.object_store.create(name)
        with helpers.cleanup_action(lambda: test_bucket.delete()):
            self.assertTrue(
                test_bucket.id in repr(test_bucket),
                "repr(obj) should contain the object id so that the object"
                " can be reconstructed, but does not. eval(repr(obj)) == obj")

            buckets = self.provider.object_store.list()

            list_buckets = [c for c in buckets if c.name == name]
            self.assertTrue(
                len(list_buckets) == 1,
                "List buckets does not return the expected bucket %s" %
                name)

            # check iteration
            iter_buckets = [c for c in self.provider.object_store
                            if c.name == name]
            self.assertTrue(
                len(iter_buckets) == 1,
                "Iter buckets does not return the expected bucket %s" %
                name)

            # check find
            find_buckets = self.provider.object_store.find(name=name)
            self.assertTrue(
                len(find_buckets) == 1,
                "Find buckets does not return the expected bucket %s" %
                name)

            get_bucket = self.provider.object_store.get(
                test_bucket.id)
            self.assertTrue(
                list_buckets[0] ==
                get_bucket == test_bucket,
                "Objects returned by list: {0} and get: {1} are not as "
                " expected: {2}" .format(list_buckets[0].id,
                                         get_bucket.id,
                                         test_bucket.name))

        buckets = self.provider.object_store.list()
        found_buckets = [c for c in buckets if c.name == name]
        self.assertTrue(
            len(found_buckets) == 0,
            "Bucket %s should have been deleted but still exists." %
            name)

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
            obj_name = "hello_world.txt"
            obj = test_bucket.create_object(obj_name)

            self.assertTrue(
                obj.id in repr(obj),
                "repr(obj) should contain the object id so that the object"
                " can be reconstructed, but does not. eval(repr(obj)) == obj")

            with helpers.cleanup_action(lambda: obj.delete()):
                # TODO: This is wrong. We shouldn't have to have a separate
                # call to upload some content before being able to delete
                # the content. Maybe the create_object method should accept
                # the file content as a parameter.
                obj.upload("dummy content")
                objs = test_bucket.list()

                # check iteration
                iter_objs = list(test_bucket)
                self.assertListEqual(iter_objs, objs)

                found_objs = [o for o in objs if o.name == obj_name]
                self.assertTrue(
                    len(found_objs) == 1,
                    "List bucket objects does not return the expected"
                    " object %s" % obj_name)

                self.assertTrue(
                    found_objs[0] == obj,
                    "Objects returned by list: {0} are not as "
                    " expected: {1}" .format(found_objs[0].id,
                                             obj.id))

            objs = test_bucket.list()
            found_objs = [o for o in objs if o.name == obj_name]
            self.assertTrue(
                len(found_objs) == 0,
                "Object %s should have been deleted but still exists." %
                obj_name)

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
                obj.download(target_stream)
                self.assertEqual(target_stream.getvalue(), content)
