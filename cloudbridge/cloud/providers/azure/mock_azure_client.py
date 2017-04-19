from azure.mgmt.compute.models import Disk, CreationData, DiskCreateOption
from azure.mgmt.network.models import NetworkSecurityGroup
from azure.mgmt.network.models import SecurityRule
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.storage.blob.models import Container, Blob

from cloudbridge.cloud.providers.azure.azure_client import FilterList


class MockAzureClient:
    sg_rule1 = SecurityRule(protocol='*', source_address_prefix='100', destination_address_prefix="*", access="Allow",
                            direction="Inbound")
    sg_rule1.name = "rule1"
    sg_rule1.id = "r1"
    sg_rule1.destination_port_range = "*"
    sg_rule1.source_port_range = "25-1"

    sg_rule2 = SecurityRule(protocol='*', source_address_prefix='100', destination_address_prefix="*", access="Allow",
                            direction="Inbound")
    sg_rule2.name = "rule2"
    sg_rule2.id = "r2"
    sg_rule2.is_default = True
    sg_rule2.destination_port_range = "*"
    sg_rule2.source_port_range = "*"


    sec_gr1 = NetworkSecurityGroup()
    sec_gr1.name = "sg1"
    sec_gr1.id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure/providers/Microsoft.Network/networkSecurityGroups/sg1"
    sec_gr1.default_security_rules = [sg_rule1]
    sec_gr1.security_rules = [sg_rule2]

    sec_gr2 = NetworkSecurityGroup()
    sec_gr2.name = "sg2"
    sec_gr2.id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure/providers/Microsoft.Network/networkSecurityGroups/sg2"
    sec_gr2.default_security_rules = [sg_rule1]
    sec_gr2.security_rules = [sg_rule2]

    sec_gr3 = NetworkSecurityGroup()
    sec_gr3.name = "sg3"
    sec_gr3.id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure/providers/Microsoft.Network/networkSecurityGroups/sg3"
    sec_gr3.default_security_rules = [sg_rule1]
    sec_gr3.security_rules = [sg_rule2]

    security_groups = [sec_gr1, sec_gr2, sec_gr3]


    container1 = Container()
    container1.name = "container1"

    container2 = Container()
    container2.name = "container2"

    containers = [container1, container2]

    block1 = Blob()
    block1.name = "block1"
    block1.content = "blob1Content"

    block2 = Blob()
    block2.name = "block2"
    block2.content = "blob2Content"

    block3 = Blob()
    block3.name = "block3"
    block3.content = None

    blocks = [block1, block2, block3]

    rg = ResourceGroup(location='westus')
    rg.name = "testResourceGroup"

    def __init__(self, provider):
        self._provider = provider


    def create_security_group(self, name, parameters):
        sg_create = NetworkSecurityGroup()
        sg_create.name = name
        sg_create.id = name
        sg_create.default_security_rules = [self.sg_rule1]
        sg_create.security_rules = [self.sg_rule2]
        self.security_groups.append(sg_create)
        return sg_create

    def list_security_group(self):
        return self.security_groups

    def delete_security_group(self, name):
        for item in self.security_groups:
            if item.name == name:
                self.security_groups.remove(item)
                return True
        return False

    def get_security_group(self, name):
        for item in self.security_groups:
            if item.name == name:
                return item
        return None

    def create_security_group_rule(self, security_group, rule_name, parameters):
        new_sg_rule = SecurityRule(protocol='*',source_address_prefix='100',destination_address_prefix="*",access="Allow",direction = "Inbound")
        new_sg_rule.name = "rule1"
        new_sg_rule.id = "r1"
        new_sg_rule.destination_port_range = "*"
        new_sg_rule.source_port_range = "25-1"
        return new_sg_rule

    def delete_security_group_rule(self, name, security_group):
        pass

    def get_resource_group(self, resource_group_name):
        if resource_group_name == 'cloudbridge-azure':
            raise Exception()
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

    def list_containers(self, filters = None):
        containers = FilterList(self.containers)
        containers.filter(filters)
        return containers

    def create_container(self, container_name):
        new_container = Container()
        new_container.name = container_name
        return new_container

    def delete_container(self, container_name):
        container = self.get_container(container_name)
        self.containers.remove(container)

    def create_blob_from_text(self, container_name, blob_name, text):
        blob = self.get_blob(container_name, blob_name)
        blob.content = text

    def get_blob(self, container_name, blob_name):
        for blob in self.blocks:
            if blob.name == blob_name:
                return blob
        return None

    def list_blobs(self,container_name):
        return self.blocks

    def get_blob_content(self, container_name, blob_name):
        blob = self.get_blob(container_name, blob_name)
        return blob

    def delete_blob(self,container_name, blob_name):
        for blob in self.blocks:
            if blob.name == blob_name:
                self.blocks.remove(blob)

    def create_blob_from_file(self, container_name, blob_name, file_path):
        blob = self.get_blob(container_name, blob_name)
        blob.content = file_path

    def get_blob_url(self, container_name, blob_name):
        return 'https://cloudbridgeazure.blob.core.windows.net/vhds/block1'

    def create_empty_disk(self, disk_name, size, region=None, snapshot_id=None):
        volume = Disk(location='eastus',creation_data=None)
        volume.id='/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/cloudbridge-azure/providers/Microsoft.Compute/disks/SampleVolume'
        volume.name = disk_name
        volume.disk_size_gb= size
        volume.creation_data = CreationData(create_option=DiskCreateOption.empty)
        volume.time_created = '01-01-2017'
        volume.owner_id ='/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure/providers/Microsoft.Compute/virtualMachines/ubuntu-intro1'
        return volume


