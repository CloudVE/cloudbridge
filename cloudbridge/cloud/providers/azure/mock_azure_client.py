import uuid
from datetime import datetime

from io import BytesIO

from azure.common import AzureException
from azure.mgmt.compute.models import CreationData, DataDisk, \
    Disk, DiskCreateOption, Image, InstanceViewStatus, \
    ManagedDiskParameters, NetworkProfile, OSDisk, Snapshot,\
    StorageProfile, VirtualMachine, \
    VirtualMachineInstanceView, VirtualMachineSize

from azure.mgmt.network.models import AddressSpace, NetworkInterface, \
    NetworkSecurityGroup, PublicIPAddress
from azure.mgmt.network.models import SecurityRule
from azure.mgmt.network.models import Subnet, VirtualNetwork
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.resource.subscriptions.models import Location
from azure.mgmt.storage.models import StorageAccount
from azure.storage.blob.models import Blob, BlobProperties, \
    Container
from azure.storage.table.models import Entity

from msrestazure.azure_exceptions import CloudError

from requests import Response


class Expando(object):
    pass


class MockAzureClient:
    sg_rule1 = SecurityRule(protocol='*', source_address_prefix='100',
                            destination_address_prefix="*", access="Allow",
                            direction="Inbound")
    sg_rule1.name = "rule1"
    sg_rule1.id = "r1"
    sg_rule1.destination_port_range = "*"
    sg_rule1.source_port_range = "25-1"

    sg_rule2 = SecurityRule(protocol='*', source_address_prefix='100',
                            destination_address_prefix="*", access="Allow",
                            direction="Inbound")
    sg_rule2.name = "rule2"
    sg_rule2.id = "r2"
    sg_rule2.destination_port_range = "*"
    sg_rule2.source_port_range = "*"

    sec_gr1 = NetworkSecurityGroup()
    sec_gr1.name = "sg1"
    sec_gr1.id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/cloudbridge'\
    '/providers/Microsoft.Network/networkSecurityGroups/sg1"
    sec_gr1.tags = None
    sec_gr1.resource_guid = uuid.uuid4()
    sec_gr1.security_rules = [sg_rule1, sg_rule2]

    sec_gr2 = NetworkSecurityGroup()
    sec_gr2.name = "sg2"
    sec_gr2.id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/cloudbridge'\
    '/providers/Microsoft.Network/networkSecurityGroups/sg2"
    sec_gr2.tags = None
    sec_gr2.security_rules = [sg_rule1, sg_rule2]

    sec_gr3 = NetworkSecurityGroup()
    sec_gr3.name = "sg3"
    sec_gr3.id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/cloudbridge'\
    '/providers/Microsoft.Network/networkSecurityGroups/sg3"
    sec_gr3.tags = {'Name': 'sg3'}
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

    block4 = Blob()
    block4.name = "block4"
    block4.content = None

    blocks = {'container1': [block1, block2, block3],
              'container2': [block1, block2, block3, block4]}

    rg = ResourceGroup(location='westus')
    rg.name = "testResourceGroup"

    network1 = VirtualNetwork()
    network1.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                  '/resourceGroups/cloudbridge/providers' \
                  '/Microsoft.Network/virtualNetworks/CloudBridgeNet1'
    network1.name = "CloudBridgeNet1"
    network1.location = 'eastus'
    network1.address_space = AddressSpace()
    network1.address_space.address_prefixes = ['10.0.0.0/16']
    network1.provisioning_state = "Succeeded"

    network2 = VirtualNetwork()
    network2.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                  '/resourceGroups/cloudbridge/providers' \
                  '/Microsoft.Network/virtualNetworks/CloudBridgeNet2'
    network2.name = "CloudBridgeNet2"
    network2.location = 'eastus'
    network2.address_space = AddressSpace()
    network2.address_space.address_prefixes = ['10.0.0.0/16']
    network2.provisioning_state = "Failed"

    network3 = VirtualNetwork()
    network3.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                  '/resourceGroups/cloudbridge/providers' \
                  '/Microsoft.Network/virtualNetworks/CloudBridgeNet3'
    network3.name = "CloudBridgeNet3"
    network3.location = 'eastus'
    network3.address_space = AddressSpace()
    network3.address_space.address_prefixes = ['10.0.0.0/16']
    network3.provisioning_state = "Succeeded"

    networks = [network1, network2, network3]

    floating_ip1 = PublicIPAddress()
    floating_ip1.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                      '/resourceGroups/cloudbridge/providers' \
                      '/Microsoft.Network/publicIPAddresses/public_ip_1'
    floating_ip1.name = 'public_ip_1'
    floating_ip1.public_ip = '13.82.104.1'
    floating_ip1.private_ip = None

    floating_ip2 = PublicIPAddress()
    floating_ip2.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                      '/resourceGroups/cloudbridge/providers' \
                      '/Microsoft.Network/publicIPAddresses/public_ip_2'
    floating_ip2.name = 'public_ip_2'
    floating_ip2.public_ip = '13.82.104.2'
    floating_ip2.private_ip = None

    floating_ip3 = PublicIPAddress()
    floating_ip3.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                      '/resourceGroups/cloudbridge/providers' \
                      '/Microsoft.Network/publicIPAddresses/public_ip_3'
    floating_ip3.name = 'public_ip_3'
    floating_ip3.public_ip = '13.82.104.3'
    floating_ip3.private_ip = None

    floating_ips = [floating_ip1, floating_ip2, floating_ip3]

    volume1 = Disk(location='eastus', creation_data=None)
    volume1.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                 'resourceGroups/cloudbridge' \
                 '/providers/Microsoft.Compute/disks/Volume1'
    volume1.name = "Volume1"
    volume1.disk_size_gb = 1
    volume1.creation_data = CreationData(create_option=DiskCreateOption.empty)
    volume1.time_created = '20-04-2017'
    volume1.owner_id = 'ubuntu-intro1'
    volume1.provisioning_state = 'InProgress'
    volume1.tags = {'Name': 'Volume1'}
    volume1.creation_data.source_uri = \
        '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
        '/resourceGroups/cloudbridge' \
        '/providers/Microsoft.Compute/snapshots/snapshot1'

    volume2 = Disk(location='eastus', creation_data=None)
    volume2.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                 '/resourceGroups/cloudbridge' \
                 '/providers/Microsoft.Compute/disks/Volume2'
    volume2.name = "Volume2"
    volume2.disk_size_gb = 1
    volume2.creation_data = CreationData(create_option=DiskCreateOption.empty)
    volume2.time_created = '20-04-2017'
    volume2.owner_id = None
    volume2.provisioning_state = 'Succeeded'
    volume2.tags = None

    volumes = [volume1, volume2]

    creation_data = CreationData(create_option=DiskCreateOption.empty)

    snapshot1 = Snapshot(location='eastus', creation_data=creation_data)
    snapshot1.name = 'snapshot1'
    snapshot1.tags = {'Name': 'snapshot1'}
    snapshot1.disk_size_gb = 1

    snapshot1.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                   '/resourceGroups/cloudbridge' \
                   '/providers/Microsoft.Compute/snapshots/snapshot1'
    snapshot1.os_type = 'Linux'
    snapshot1.account_type = 'Premium_LRS'

    snapshot2 = Snapshot(location='eastus', creation_data=creation_data)
    snapshot2.name = 'snapshot2'
    snapshot2.tags = None
    snapshot2.disk_size_gb = 2
    snapshot2.creation_data = \
        CreationData(create_option=DiskCreateOption.empty)
    snapshot2.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                   '/resourceGroups/cloudbridge' \
                   '/providers/Microsoft.Compute/snapshots/snapshot2'
    snapshot2.os_type = 'Windows'
    snapshot2.account_type = ' Standard_LRS'

    snapshots = [snapshot1, snapshot2]

    nic1 = NetworkInterface()
    nic1.name = 'nic1'
    nic1.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
              'resourceGroups/cloudbridge' \
              '/providers/Microsoft.Network/' \
              'networkInterfaces/nic1'

    nic2 = NetworkInterface()
    nic2.name = 'nic2'
    nic2.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
              'resourceGroups/cloudbridge' \
              '/providers/Microsoft.Network/' \
              'networkInterfaces/nic2'

    nics = [nic1, nic2]

    vm1 = VirtualMachine(location='eastus')
    vm1.name = 'VM1'
    vm1.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'\
             '/resourceGroups/cloudbridge'\
             '/providers/Microsoft.Compute/virtualMachines/VM1'
    vm1.provisioning_state = 'Succeeded'
    vm1.storage_profile = StorageProfile()
    vm1.tags = {'Name': 'VM1'}
    vm1.instance_view = VirtualMachineInstanceView()
    vm1.instance_view.statuses = [
        InstanceViewStatus(display_status='VM running'),
        InstanceViewStatus(display_status='VM running'),
    ]
    data_disk_id = '/subscriptions'\
                   '/7904d702-e01c-4826-8519-f5a25c866a96' \
                   '/resourceGroups/cloudbridge' \
                   '/providers/Microsoft.Compute/disks/Volume2'
    data_dik = \
        DataDisk(managed_disk=ManagedDiskParameters(id=data_disk_id),
                 lun=0, create_option='attach')
    vm1.storage_profile.data_disks = [data_dik]

    vm1.storage_profile.os_disk = OSDisk(create_option='fromImage')
    vm1.storage_profile.os_disk.managed_disk = \
        ManagedDiskParameters(id='')
    vm1.storage_profile.os_disk.disk_size_gb = 10

    vm1.network_profile = NetworkProfile()
    vm1.network_profile.network_interfaces = [nic1]

    vm2 = VirtualMachine(location='eastus')
    vm2.name = 'VM2'
    vm2.tags = {'Name': 'VM2'}
    vm2.instance_view = VirtualMachineInstanceView()
    vm2.instance_view.statuses = [
        InstanceViewStatus(display_status='VM running'),
        InstanceViewStatus(display_status='VM running'),
    ]
    vm2.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
             '/resourceGroups/cloudbridge' \
             '/providers/Microsoft.Compute/virtualMachines/VM2'
    vm2.provisioning_state = 'Succeeded'
    vm2.storage_profile = StorageProfile()
    vm2.storage_profile.data_disks = [data_dik]

    vm2.storage_profile.os_disk = OSDisk(create_option='fromImage')
    vm2.storage_profile.os_disk.managed_disk = \
        ManagedDiskParameters(id='')
    vm2.storage_profile.os_disk.disk_size_gb = 10

    vm2.network_profile = NetworkProfile()
    vm2.network_profile.network_interfaces = [nic2]

    virtual_machines = [vm1, vm2]

    image1 = Image(location='eastus')
    image1.name = 'image1'
    image1.tags = {'Name': 'image1'}
    image1.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                'resourceGroups/cloudbridge/providers/' \
                'Microsoft.Compute/images/image1'
    image1.storage_profile = StorageProfile()
    image1.storage_profile.os_disk = ManagedDiskParameters(id='')
    image1.storage_profile.os_disk.disk_size_gb = 10
    obj1 = Expando()
    obj1.name = 'linux'
    obj1.value = 'Linux'
    image1.storage_profile.os_disk.os_type = obj1

    image2 = Image(location='eastus')
    image2.name = 'image2'
    image2.tags = {'Name': 'image2'}
    image2.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                '/resourceGroups/cloudbridge' \
                '/providers/Microsoft.Compute/images/image2'
    image2.storage_profile = StorageProfile()
    image2.storage_profile.os_disk = ManagedDiskParameters(id='')
    image2.storage_profile.os_disk.disk_size_gb = 10

    obj = Expando()
    obj.name = 'linux'
    obj.value = 'Linux'
    image2.storage_profile.os_disk.os_type = obj

    image3 = Image(location='eastus')
    image3.name = 'image3'
    image3.tags = {'Name': 'image3'}
    image3.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                '/resourceGroups/cloudbridge' \
                '/providers/Microsoft.Compute/images/image3'
    image3.storage_profile = StorageProfile()
    image3.storage_profile.os_disk = ManagedDiskParameters(id='')
    image3.storage_profile.os_disk.disk_size_gb = 10

    obj = Expando()
    obj.name = 'linux'
    obj.value = 'Linux'
    image3.storage_profile.os_disk.os_type = obj

    images = [image1, image2, image3]

    region1 = Location()
    region1.name = "westus2"
    region1.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                 'locations/westus2'

    region2 = Location()
    region2.name = "koreasouth"
    region2.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                 'locations/koreasouth'

    region3 = Location()
    region3.name = "eastus"
    region3.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                 'locations/eastus'

    regions = [region1, region2, region3]

    subnet1 = Subnet()
    subnet1.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                 '/resourceGroups/cloudbridge/providers/' \
                 'Microsoft.Network/virtualNetworks/CloudBridgeNet1/subnets/' \
                 'MySN1'
    subnet1.name = 'MySN1'
    subnet1.address_prefix = '10.0.0.0/24'
    subnet2 = Subnet()
    subnet2.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                 'resourceGroups/cloudbridge/providers/' \
                 'Microsoft.Network/virtualNetworks/CloudBridgeNet1/' \
                 'subnets/MySN2'
    subnet2.name = 'MySN2'
    subnet2.address_prefix = '10.0.0.0/25'
    subnets = [subnet1, subnet2]

    instance_type1 = VirtualMachineSize()
    instance_type1.name = "Standard_DS1_v1"
    instance_type1.number_of_cores = 1
    instance_type1.os_disk_size_in_mb = 100
    instance_type1.resource_disk_size_in_mb = 100
    instance_type1.memory_in_mb = 1000
    instance_type1.max_data_disk_count = 1

    instance_type2 = VirtualMachineSize()
    instance_type2.name = "Standard_DS1_v2"
    instance_type2.number_of_cores = 2
    instance_type2.os_disk_size_in_mb = 200
    instance_type2.resource_disk_size_in_mb = 200
    instance_type2.memory_in_mb = 2000
    instance_type2.max_data_disk_count = 2

    instance_types = [instance_type1, instance_type2]

    def __init__(self, provider):
        self._provider = provider

    @property
    def region_name(self):
        return 'eastus'

    def create_security_group(self, name, parameters):
        sg_create = NetworkSecurityGroup()
        sg_create.name = name
        sg_create.id = name
        sg_create.tags = parameters.get('tags', None)
        sg_create.default_security_rules = [self.sg_rule1]
        sg_create.security_rules = [self.sg_rule2]
        self.security_groups.append(sg_create)
        return sg_create

    def update_security_group_tags(self, name, tags):
        sg = self.get_security_group(name)
        sg.tags = tags
        return sg

    def list_security_group(self):
        return self.security_groups

    def delete_security_group(self, name):
        sg = self.get_security_group(name)
        self.security_groups.remove(sg)

    def get_security_group(self, name):
        for item in self.security_groups:
            if item.name == name:
                return item
        response = Response()
        response.status_code = 404
        raise CloudError(response=response, error='Resource Not found')

    def create_security_group_rule(self, security_group,
                                   rule_name, parameters):
        new_sg_rule = SecurityRule(protocol=parameters['protocol'],
                                   source_address_prefix=parameters
                                   ['source_address_prefix'],
                                   destination_address_prefix=parameters
                                   ['destination_address_prefix'],
                                   access="Allow", direction="Inbound")
        new_sg_rule.name = "rule1"
        new_sg_rule.id = "r1"
        new_sg_rule.destination_port_range = "*"
        new_sg_rule.source_port_range = parameters['source_port_range']
        return new_sg_rule

    def delete_security_group_rule(self, name, security_group):
        pass

    def get_resource_group(self, resource_group_name):
        if resource_group_name == 'cloudbridge':
            response = Response()
            response.status_code = 404
            raise CloudError(response=response, error='Resource not found')
        return self.rg

    def list_networks(self):
        return self.networks

    def get_network(self, network_name):
        for network in self.networks:
            if network.name == network_name:
                return network

        response = Response()
        response.status_code = 404
        raise CloudError(response=response, error='Resource not found')

    def create_network(self, name, params):
        network = VirtualNetwork()
        network.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                     '/resourceGroups/cloudbridge/providers' \
                     '/Microsoft.Network/virtualNetworks/{0}'.\
            format(name)
        network.name = name
        network.address_space = AddressSpace()
        network.address_space.address_prefixes = ['10.0.0.0/16']
        network.provisioning_state = "Succeeded"
        network.tags = params['tags']
        self.networks.append(network)

    def update_network_tags(self, name, tags):
        pass

    def delete_network(self, network_name):
        network = self.get_network(network_name)
        self.networks.remove(network)

        return True

    def create_floating_ip(self, public_ip_address_name, public_ip_parameters):
        floating_ip = PublicIPAddress()
        floating_ip.id = '/subscriptions' \
                         '/7904d702-e01c-4826-8519-f5a25c866a96' \
                         '/resourceGroups/cloudbridge/providers' \
                         '/Microsoft.Network/publicIPAddresses/' \
                         + public_ip_address_name
        floating_ip.name = public_ip_address_name
        floating_ip.ip_address = '13.82.104.38'
        floating_ip.private_ip = None
        self.floating_ips.append(floating_ip)
        return floating_ip

    def list_floating_ips(self):
        return self.floating_ips

    def delete_floating_ip(self, public_ip_address_name):
        for floating_ip in self.floating_ips:
            if floating_ip.name == public_ip_address_name:
                self.floating_ips.remove(floating_ip)
        return True

    def create_resource_group(self, resource_group_name, params):
        rg = ResourceGroup(location='westus')
        rg.name = resource_group_name
        return rg

    def get_container(self, container_name):
        for container in self.containers:
            if container.name == container_name:
                return container
        raise AzureException()

    def list_containers(self, prefix=None):
        if (prefix is not None):
            found_containers = []
            for container in self.containers:
                if prefix in container.name:
                    found_containers.append(container)
            return found_containers
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
        if blob_name == 'block4' and text != '':
            raise AzureException()
        blob = self.get_blob(container_name, blob_name)
        blob.content = text
        blob.properties = BlobProperties()
        blob.properties.content_length = len(text)
        blob.properties.last_modified = \
            datetime(year=2017, month=5, day=2)
        return blob

    def get_blob(self, container_name, blob_name):
        for blob in self.blocks.get(container_name):
            if blob.name == blob_name:
                return blob
        raise AzureException()

    def list_blobs(self, container_name, prefix=None):
        return self.blocks.get(container_name)

    def get_blob_content(self, container_name, blob_name):
        blob = self.get_blob(container_name, blob_name)
        if blob.content:
            output = BytesIO()
            output.write(bytearray(blob.content, 'UTF-8'))
            return output

        return None

    def delete_blob(self, container_name, blob_name):
        blob = self.get_blob(container_name, blob_name)
        self.blocks.get(container_name).remove(blob)

    def create_blob_from_file(self, container_name, blob_name, file_path):
        if blob_name == 'block4':
            raise AzureException()

        blob = self.get_blob(container_name, blob_name)
        blob.content = file_path

    def get_blob_url(self, container_name, blob_name):
        return 'https://cloudbridgeazure.blob.core.windows.net/vhds/block1'

    def create_empty_disk(self, disk_name, params):
        volume = Disk(location='eastus', creation_data=None)
        volume.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                    'resourceGroups/cloudbridge' \
                    '/providers/Microsoft.Compute/disks/{0}'.format(disk_name)
        volume.name = disk_name
        volume.disk_size_gb = 30
        volume.creation_data = CreationData(
            create_option=DiskCreateOption.empty)
        volume.time_created = datetime(year=2017, month=5, day=2)
        volume.location = 'eastus'
        volume.provisioning_state = 'Succeeded'
        volume.tags = params.get('tags', None)
        if disk_name.startswith('attach'):
            volume.owner_id = \
                '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'\
                '/resourceGroups/cloudbridge'\
                '/providers/Microsoft.Compute/virtualMachines/VM1'
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
        disk = self.get_disk(disk_name)
        self.volumes.remove(disk)
        return True

    def get_storage_account(self, storage_account_name):
        if storage_account_name == 'cloudbridgestorage':
            response = Response()
            response.status_code = 404
            raise CloudError(response=response, error='Resource not found')

        storage_account = StorageAccount()
        storage_account.name = storage_account_name
        return storage_account

    def create_storage_account(self, storage_account_name, params):
        storage_account = StorageAccount()
        storage_account.name = storage_account_name
        return storage_account

    def update_disk_tags(self, disk_name, tags):
        pass

    def create_snapshot(self, snapshot_name, params):
        snapshot = Snapshot(location='eastus', creation_data=None)
        snapshot.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                      '/resourceGroups/cloudbridge' \
                      '/providers/Microsoft.Compute/Snapshots/{0}'.format(
                        snapshot_name)
        snapshot.name = snapshot_name
        snapshot.disk_size_gb = 30
        snapshot.creation_data = \
            CreationData(create_option=DiskCreateOption.empty)
        snapshot.time_created = datetime(year=2017, month=5, day=2)
        snapshot.creation_data.source_uri = \
            '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
            '/resourceGroups/cloudbridge/providers' \
            '/Microsoft.Compute/disks/{0}'.format(
                snapshot_name)
        snapshot.tags = params.get('tags', None)
        self.snapshots.append(snapshot)
        return snapshot

    def update_snapshot_tags(self, snapshot_name, tags):
        snapshot = self.get_snapshot(snapshot_name)
        snapshot.tags = tags
        return snapshot

    def get_snapshot(self, name):
        for snapshot in self.snapshots:
            if snapshot.name == name:
                return snapshot

        response = Response()
        response.status_code = 404
        raise CloudError(response=response, error='Resource Not found')

    def delete_snapshot(self, name):
        snapshot = self.get_snapshot(name)
        self.snapshots.remove(snapshot)
        return True

    def create_snapshot_disk(self, disk_name, params):
        volume = Disk(location='eastus', creation_data=None)
        volume.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                    '/resourceGroups/cloudbridge/providers' \
                    '/Microsoft.Compute/disks/{0}'.format(
                        disk_name)
        volume.name = disk_name
        volume.disk_size_gb = 50
        volume.creation_data = CreationData(
            create_option=DiskCreateOption.copy,
            source_uri=params.get('creation_data').get('source_uri'))
        volume.time_created = '01-01-2017'
        volume.tags = params.get('tags', None)
        self.volumes.append(volume)
        return volume

    def list_snapshots(self):
        return self.snapshots

    def create_vm(self, vm_name, params):

        if not isinstance(params, dict):
            for data_disk in params.storage_profile.data_disks:
                if isinstance(data_disk, dict):
                    disk_id = data_disk.get('managed_disk').get('id')
                    lun = data_disk.get('lun')
                    create_option = data_disk.get('create_option')
                    managed_disk = \
                        ManagedDiskParameters(id=disk_id)
                    params.storage_profile.data_disks.remove(data_disk)
                    params.storage_profile.\
                        data_disks\
                        .append(DataDisk(managed_disk=managed_disk,
                                lun=lun, create_option=create_option))

            return params

        vm = VirtualMachine(location='eastus')
        vm.name = vm_name
        vm.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                '/resourceGroups/cloudbridge' \
                '/providers/Microsoft.Compute/virtualMachines/' + vm_name
        vm.provisioning_state = 'Succeeded'
        vm.storage_profile = StorageProfile()
        vm.tags = {'Name': vm_name}
        data_disk_id = '/subscriptions' \
                       '/7904d702-e01c-4826-8519-f5a25c866a96' \
                       '/resourceGroups/cloudbridge' \
                       '/providers/Microsoft.Compute/disks/Volume2'
        data_dik = \
            DataDisk(managed_disk=ManagedDiskParameters(id=data_disk_id),
                     lun=0, create_option='attach')
        vm.storage_profile.data_disks = [data_dik]

        vm.storage_profile.os_disk = OSDisk(create_option='fromImage')
        os_disk_id = '/subscriptions' \
                     '/7904d702-e01c-4826-8519-f5a25c866a96' \
                     '/resourceGroups/cloudbridge' \
                     '/providers/Microsoft.Compute/disks/os_disk'

        vm.storage_profile.os_disk.managed_disk = \
            ManagedDiskParameters(id=os_disk_id)
        vm.storage_profile.os_disk.disk_size_gb = 10

        os_disk = Disk(location='eastus', creation_data=None)
        os_disk.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                     '/resourceGroups/cloudbridge' \
                     '/providers/Microsoft.Compute/disks/os_dsk'
        os_disk.name = "os_disk"
        os_disk.disk_size_gb = 30
        os_disk.creation_data = \
            CreationData(create_option=DiskCreateOption.empty)
        os_disk.time_created = '20-04-2017'
        os_disk.owner_id = None
        os_disk.provisioning_state = 'Succeeded'
        os_disk.tags = None

        self.volumes.append(os_disk)

        nic = NetworkInterface()
        nic.name = vm_name + '_NIC'
        nic.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                 'resourceGroups/cloudbridge' \
                 '/providers/Microsoft.Network/' \
                 'networkInterfaces/{0}_NIC'.format(vm_name)

        self.nics.append(nic)

        vm.network_profile = NetworkProfile()
        vm.network_profile.network_interfaces = [nic]

        vm.instance_view = VirtualMachineInstanceView()
        vm.instance_view.statuses = [
            InstanceViewStatus(display_status='VM running'),
            InstanceViewStatus(display_status='VM running'),
        ]

        self.virtual_machines.append(vm)
        return vm

    def list_images(self):
        return self.images

    def get_image(self, name):
        for image in self.images:
            if image.name == name:
                return image

        response = Response()
        response.status_code = 404
        raise CloudError(response=response, error='Resource Not found')

    def delete_image(self, name):
        img = self.get_image(name)
        self.images.remove(img)

    def list_locations(self):
        return self.regions

    def list_instance_types(self):
        return self.instance_types

    def update_image_tags(self, name, tags):
        img = self.get_image(name)
        img.tags = tags
        return img

    def list_subnets(self, network_name):
        return self.subnets

    def get_subnet(self, network_name, subnet_name):
        for subnet in self.subnets:
            if subnet.name == subnet_name:
                return subnet
        response = Response()
        response.status_code = 404
        raise CloudError(response=response, error='Resource Not found')

    def create_subnet(self, network_name, subnet_name, params):
        subnet = Subnet()
        subnet.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                    'resourceGroups/cloudbridge/providers/' \
                    'Microsoft.Network/virtualNetworks/{0}/' \
                    'subnets/{1}'.format(network_name, subnet_name)
        subnet.name = subnet_name
        subnet.address_prefix = '10.0.0.0/25'
        self.subnets.append(subnet)
        return subnet

    def delete_subnet(self, network_name, subnet_name):
        subnet = self.get_subnet(network_name, subnet_name)
        self.subnets.remove(subnet)

    def create_image(self, name, params):
        image = Image(location='eastus')
        image.name = name
        image.tags = {'Name': name}
        image.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                   'resourceGroups/cloudbridge/providers/' \
                   'Microsoft.Compute/images/' + name
        image.storage_profile = StorageProfile()
        image.storage_profile.os_disk = ManagedDiskParameters(id='')
        image.storage_profile.os_disk.disk_size_gb = 10
        obj = Expando()
        obj.name = 'linux'
        obj.value = 'Linux'
        image.storage_profile.os_disk.os_type = obj
        self.images.append(image)
        return image

    def restart_vm(self, vm_name):
        pass

    def deallocate_vm(self, vm_name):
        pass

    def generalize_vm(self, vm_name):
        pass

    def start_vm(self, vm_name):
        pass

    def get_nic(self, name):
        return [nic for nic in self.nics if nic.name == name][0]

    def create_nic(self, name, params):
        nic = NetworkInterface()
        nic.name = name
        nic.id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                 'resourceGroups/cloudbridge' \
                 '/providers/Microsoft.Network/' \
                 'networkInterfaces/' + name
        self.nics.append(nic)
        return nic

    def get_public_ip(self, name):
        pass

    def update_vm_tags(self, vm_name, tags):
        vm = self.get_vm(vm_name)
        vm.tags = tags
        return vm

    def add_security_group_vm(self, vm_name, security_group_id):
        pass

    def delete_security_group_vm(self, vm_name, security_group_id):
        pass

    def delete_vm(self, vm_name):
        vm = self.get_vm(vm_name)
        self.virtual_machines.remove(vm)

    def delete_nic(self, nic_name):
        pass

    def delete_public_ip(self, public_ip_name):
        self.get_public_ip(public_ip_name)

    def list_vm(self):
        return self.virtual_machines

    def get_vm(self, vm_name):
        for vm in self.virtual_machines:
            if vm.name == vm_name:
                return vm
        response = Response()
        response.status_code = 404
        raise CloudError(response=response, error='Resource Not found')

    keyEntity1 = Entity()
    keyEntity1.PartitionKey = '00000000-0000-0000-0000-000000000000'
    keyEntity1.RowKey = str(uuid.uuid4())
    keyEntity1.Name = 'KeyPair1'
    keyEntity1.Key = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ+G1hl'

    keyEntity2 = Entity()
    keyEntity2.PartitionKey = '00000000-0000-0000-0000-000000000000'
    keyEntity2.RowKey = str(uuid.uuid4())
    keyEntity2.Name = 'KeyPair2'
    keyEntity2.Key = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ+G1h2'

    key_entities = [keyEntity1, keyEntity2]

    def create_public_key(self, entity):
        newKey = Entity()
        newKey.PartitionKey = entity['PartitionKey']
        newKey.RowKey = entity['RowKey']
        newKey.Name = entity['Name']
        newKey.Key = entity['Key']
        self.key_entities.append(newKey)

    def get_public_key(self, key_name):
        for key in self.key_entities:
            if key.Name == key_name:
                return key
        response = Response()
        response.status_code = 404
        raise AzureException()

    def delete_public_key(self, entity):
        self.key_entities.remove(entity)

    def list_public_keys(self, partition_key):
        return self.key_entities
