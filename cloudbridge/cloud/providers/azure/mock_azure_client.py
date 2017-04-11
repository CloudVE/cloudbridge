from azure.mgmt.network.models import NetworkSecurityGroup
from azure.storage.blob.models import Container
from azure.mgmt.resource.resources.models import ResourceGroup


class MockAzureClient:
    sec_gr1 = NetworkSecurityGroup()
    sec_gr1.name = "sec_group1"
    sec_gr1.id = "sg1"
    sec_gr2 = NetworkSecurityGroup()
    sec_gr2.name = "sec_group2"
    sec_gr2.id = "sg2"
    sec_gr3 = NetworkSecurityGroup()
    sec_gr3.name = "sec_group3"
    sec_gr3.id = "sg3"
    security_groups = [sec_gr1, sec_gr2, sec_gr3]

    container1 = Container()
    container1.name = "container1"
    container2 = Container()
    container2.name = "container2"
    containers = [container1, container2]

    rg = ResourceGroup(location='westus')
    rg.name = "testResourceGroup"

    def __init__(self, provider):
        self._provider = provider

    def list_security_group(self):
        return self.security_groups

    def delete_security_group(self, name):
        for item in self.security_groups:
            if item.name == name:
                self.security_groups.remove(item)
                return True
        return False

    def get_resource_group(self, resource_group_name):
        return self.rg

    def create_resource_group(self, resource_group_name, params):
        rg = ResourceGroup(location='westus')
        rg.name = resource_group_name
        return rg

    def get_container(self, container_name):
        for container in self.containers:
            if container.name == container_name:
                return container
        return None

    def create_container(self, container_name):
        new_container = Container()
        new_container.name = "newContainerCreate"
        return None


