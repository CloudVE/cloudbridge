import StringIO
import uuid

from test.helpers import ProviderTestBase
import test.helpers as helpers


class ProviderObjectStoreServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderObjectStoreServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_crud_container(self):
        """
        Create a new container, check whether the expected values are set,
        and delete it
        """
        name = "cbtestcreatecontainer-{0}".format(uuid.uuid4())
        test_container = self.provider.object_store.create_container(name)
        with helpers.exception_action(lambda x: test_container.delete()):
            containers = self.provider.object_store.list_containers()
            found_containers = [c for c in containers if c.name == name]
            self.assertTrue(
                len(found_containers) == 1,
                "List containers does not return the expected container %s" %
                name)
            test_container.delete()

    def test_crud_container_objects(self):
        """
        Create a new container, upload some contents into the container, and
        check whether list properly detects the new content.
        Delete everything afterwards.
        """
        name = "cbtestcontainerobjs-{0}".format(uuid.uuid4())
        test_container = self.provider.object_store.create_container(name)

        # ensure that the container is empty
        objects = test_container.list()
        self.assertEqual([], objects)

        with helpers.exception_action(lambda x: test_container.delete()):
            obj_name = "hello_world.txt"
            obj = test_container.create_object(obj_name)

            with helpers.exception_action(lambda x: obj.delete()):
                # TODO: This is wrong. We shouldn't have to have a separate
                # call to upload some content before being able to delete
                # the content. Maybe the create_object method should accept
                # the file content as a parameter.
                obj.upload("dummy content")
                objs = test_container.list()
                found_objs = [o for o in objs if o.name == obj_name]
                print "FOUND: ", found_objs
                self.assertTrue(
                    len(found_objs) == 1,
                    "List container objects does not return the expected"
                    " object %s" % obj_name)
                obj.delete()
            test_container.delete()

    def test_upload_download_container_content(self):

        name = "cbtestcontainerobjs-{0}".format(uuid.uuid4())
        test_container = self.provider.object_store.create_container(name)

        with helpers.exception_action(lambda x: test_container.delete()):
            obj_name = "hello_upload_download.txt"
            obj = test_container.create_object(obj_name)

            with helpers.exception_action(lambda x: obj.delete()):
                content = "Hello World. Here's some content"
                # TODO: Upload and download methods accept different parameter
                # types. Need to make this consistent - possibly provider
                # multiple methods like upload_from_file, from_stream etc.
                obj.upload(content)
                target_stream = StringIO.StringIO()
                obj.download(target_stream)
                self.assertEqual(target_stream.getvalue(), content)
                obj.delete()
            test_container.delete()