import os
import tempfile
import uuid

import integration_test.helpers as helpers


class AzureIntegrationObjectStoreServiceTestCase(helpers.ProviderTestBase):

    def __init__(self, methodName, provider):
        super(AzureIntegrationObjectStoreServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_service(self):
        container_name = '{0}'.format(uuid.uuid4())
        object_name = '{0}'.format(uuid.uuid4())

        containers_count1 = len(self.provider.object_store.list())

        container = self.provider.object_store.create(container_name)
        self.assertTrue(container is not None , 'Container {0} not created'.format(container_name))

        containers_count2 = len(self.provider.object_store.list())
        self.assertTrue(containers_count2 > containers_count1, 'Container {0} not present in list'.format(container_name))

        find_container = self.provider.object_store.find(container_name)
        self.assertTrue(len(find_container) == 1, 'Container {0} not found'.format(container_name))

        get_container = self.provider.object_store.get(container.id)
        self.assertTrue(get_container is not None, 'Unable to get the container {0}'.format(container_name))

        obj = container.create_object(object_name)
        self.assertTrue(obj is not None, 'Object {0} not created'.format(container_name))

        obj_count = len(container.list())
        self.assertTrue(obj_count == 1, 'Object count should be 1')

        get_obj = container.get(object_name)
        self.assertTrue(get_obj is not None, 'Unable to get object {0} from container {1}.'.format(object_name, container_name))

        exits = container.exists(object_name)
        self.assertTrue(exits, 'Object {0} not exists in container {1}'.format(object_name, container_name))

        obj_content = 'abc'
        obj.upload(obj_content)

        content = obj.iter_content()
        self.assertTrue(content == obj_content, 'Object {0} content should be {1}'.format(object_name, obj_content))

        file_name = 'mytest.txt'
        file_content = 'defaults'

        tmp = os.path.join(tempfile.gettempdir(), file_name)

        try:
            if not os.path.exists(tmp):
                with open(tmp, "w") as file:
                    file.write(file_content)

            obj.upload_from_file(tmp)

            content = obj.iter_content()
            self.assertTrue(content == file_content, 'Object {0} content should be {1}'.format(object_name, file_content))

        finally:
            print('Deleting file')
            os.remove(tmp)

        url = obj.generate_url()
        self.assertTrue(url is not None, 'Url should not be None')

        obj.delete()
        delete_obj = container.get(object_name)
        self.assertTrue(delete_obj is None, 'Object {0} not deleted from container {1}'.format(object_name,container_name))

        container.delete()
        deleted_container = self.provider.object_store.get(container.id)
        self.assertTrue(deleted_container is None, 'Container {0} not deleted'.format(container_name))
