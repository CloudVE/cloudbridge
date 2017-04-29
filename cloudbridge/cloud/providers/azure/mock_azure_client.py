from io import BytesIO

from azure.common import AzureException
from azure.mgmt.compute.models import Disk, CreationData, DiskCreateOption
from azure.mgmt.network.models import NetworkSecurityGroup
from azure.mgmt.network.models import SecurityRule
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.storage.models import StorageAccount
from azure.storage.blob.models import Container, Blob
from msrestazure.azure_exceptions import CloudError
from requests import Response


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
    sg_rule2.destination_port_range = "*"
    sg_rule2.source_port_range = "*"

    sec_gr1 = NetworkSecurityGroup()
    sec_gr1.name = "sg1"
    sec_gr1.id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure'\
    '/providers/Microsoft.Network/networkSecurityGroups/sg1"
    sec_gr1.security_rules = [sg_rule1, sg_rule2]

    sec_gr2 = NetworkSecurityGroup()
    sec_gr2.name = "sg2"
    sec_gr2.id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure'\
    '/providers/Microsoft.Network/networkSecurityGroups/sg2"
    sec_gr2.security_rules = [sg_rule1, sg_rule2]

    sec_gr3 = NetworkSecurityGroup()
    sec_gr3.name = "sg3"
    sec_gr3.id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure'\
    '/providers/Microsoft.Network/networkSecurityGroups/sg3"
    sec_gr3.security_rules = [sg_rule1, sg_rule2]

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

    blocks = {'container1': [block1, block2, block3],
              'container2': [block1, block2, block3]}

    rg = ResourceGroup(location='westus')
    rg.name = "testResourceGroup"

    volume1 = Disk(location='eastus', creation_data=None)
    volume1.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CLOUDBRIDGE-AZURE' \
                 '/providers/Microsoft.Compute/disks/Volume1'
    volume1.name = "Volume1"
    volume1.disk_size_gb = 1
    volume1.creation_data = CreationData(create_option=DiskCreateOption.empty)
    volume1.time_created = '20-04-2017'
    volume1.owner_id = 'ubuntu-intro1'
    volume1.provisioning_state = 'InProgress'

    volume2 = Disk(location='eastus', creation_data=None)
    volume2.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CLOUDBRIDGE-AZURE' \
                 '/providers/Microsoft.Compute/disks/Volume2'
    volume2.name = "Volume2"
    volume2.disk_size_gb = 1
    volume2.creation_data = CreationData(create_option=DiskCreateOption.empty)
    volume2.time_created = '20-04-2017'
    volume2.owner_id = None
    volume2.provisioning_state = 'Succeeded'

    volumes = [volume1, volume2]

    snapshots = []

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
        response = Response()
        response.status_code = 404
        raise CloudError(response=response, error='Resource Not found')

    def create_security_group_rule(self, security_group, rule_name, parameters):
        new_sg_rule = SecurityRule(protocol='*', source_address_prefix='100', destination_address_prefix="*",
                                   access="Allow", direction="Inbound")
        new_sg_rule.name = "rule1"
        new_sg_rule.id = "r1"
        new_sg_rule.destination_port_range = "*"
        new_sg_rule.source_port_range = "25-1"
        return new_sg_rule

    def delete_security_group_rule(self, name, security_group):
        pass

    def get_resource_group(self, resource_group_name):
        if resource_group_name == 'cloudbridge-azure':
            response = Response()
            response.status_code = 404
            raise CloudError(response=response, error='Resource not found')
        return self.rg

    def create_resource_group(self, resource_group_name, params):
        rg = ResourceGroup(location='westus')
        rg.name = resource_group_name
        return rg

    def get_container(self, container_name):
        for container in self.containers:
            if container.name == container_name:
                return container
        raise AzureException()

    def list_containers(self):
        return self.containers

    def create_container(self, container_name):
        new_container = Container()
        new_container.name = container_name
        self.containers.append(new_container)
        return new_container

    def delete_container(self, container_name):
        container = self.get_container(container_name)
        self.containers.remove(container)

    def create_blob_from_text(self, container_name, blob_name, text):
        blob = self.get_blob(container_name, blob_name)
        blob.content = text
        return blob

    def get_blob(self, container_name, blob_name):
        for blob in self.blocks.get(container_name):
            if blob.name == blob_name:
                return blob
        raise AzureException()

    def list_blobs(self, container_name):
        return self.blocks.get(container_name)

    def get_blob_content(self, container_name, blob_name):
        blob = self.get_blob(container_name, blob_name)
        if blob.content:
            output = BytesIO()
            output.write(bytearray(blob.content, 'UTF-8'))
            return output

        return None

    def delete_blob(self, container_name, blob_name):
        for blob in self.blocks.get(container_name):
            if blob.name == blob_name:
                self.blocks.get(container_name).remove(blob)

    def create_blob_from_file(self, container_name, blob_name, file_path):
        blob = self.get_blob(container_name, blob_name)
        blob.content = file_path

    def get_blob_url(self, container_name, blob_name):
        return 'https://cloudbridgeazure.blob.core.windows.net/vhds/block1'

    def create_empty_disk(self, disk_name, size, region=None, snapshot_id=None):
        volume = Disk(location='eastus', creation_data=None)
        volume.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/cloudbridge-azure' \
                    '/providers/Microsoft.Compute/disks/{0}'.format(disk_name)
        volume.name = disk_name
        volume.disk_size_gb = size
        volume.creation_data = CreationData(create_option=DiskCreateOption.empty)
        volume.time_created = '01-01-2017'
        volume.provisioning_state = 'Succeeded'
        volume.owner_id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure' \
                          's/providers/Microsoft.Compute/virtualMachines/ubuntu-intro1'
        self.volumes.append(volume)
        return volume

    def get_disk(self, disk_name):
        for volume in self.volumes:
            if volume.name == disk_name:
                return volume
        response = Response()
        response.status_code = 404
        raise CloudError(response=response, error='Resource Not found')

    def list_disks(self):
        return self.volumes

    def delete_disk(self, disk_name):
        for disk in self.volumes:
            if disk.name == disk_name:
                self.volumes.remove(disk)

        return True

    def attach_disk(self, vm_name, disk_name, disk_id):
        return None

    def detach_disk(self, disk_id):
        return None

    def get_storage_account(self, storage_account_name):
        storage_account = StorageAccount()
        storage_account.name = storage_account_name
        return storage_account
