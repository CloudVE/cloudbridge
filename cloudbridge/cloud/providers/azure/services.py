import base64
import logging
import uuid

from azure.common import AzureException

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.services import BaseBucketService, \
    BaseComputeService, BaseFloatingIPService, BaseGatewayService, \
    BaseImageService, BaseInstanceService, BaseKeyPairService, \
    BaseNetworkService, BaseNetworkingService, BaseRegionService, \
    BaseRouterService, BaseSecurityService, BaseSnapshotService, \
    BaseStorageService, BaseSubnetService, BaseVMFirewallService, \
    BaseVMTypeService, BaseVolumeService
from cloudbridge.cloud.interfaces import InvalidConfigurationException
from cloudbridge.cloud.interfaces.resources import MachineImage, \
    Network, PlacementZone, Snapshot, Subnet, VMFirewall, VMType, Volume

from msrestazure.azure_exceptions import CloudError

from . import helpers as azure_helpers
from .resources import AzureBucket, AzureFloatingIP, \
    AzureInstance, AzureInternetGateway, AzureKeyPair, \
    AzureLaunchConfig, AzureMachineImage, AzureNetwork, \
    AzureRegion, AzureRouter, AzureSnapshot, AzureSubnet, \
    AzureVMFirewall, AzureVMType, AzureVolume

log = logging.getLogger(__name__)


class AzureSecurityService(BaseSecurityService):
    def __init__(self, provider):
        super(AzureSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = AzureKeyPairService(provider)
        self._vm_firewalls = AzureVMFirewallService(provider)

    @property
    def key_pairs(self):
        return self._key_pairs

    @property
    def vm_firewalls(self):
        return self._vm_firewalls


class AzureVMFirewallService(BaseVMFirewallService):
    def __init__(self, provider):
        super(AzureVMFirewallService, self).__init__(provider)

    def get(self, fw_id):
        try:
            fws = self.provider.azure_client.get_vm_firewall(fw_id)
            return AzureVMFirewall(self.provider, fws)

        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return None

    def list(self, limit=None, marker=None):
        fws = [AzureVMFirewall(self.provider, fw)
               for fw in self.provider.azure_client.list_vm_firewall()]
        return ClientPagedResultList(self.provider, fws, limit, marker)

    def create(self, name, description, network_id=None):
        AzureVMFirewall.assert_valid_resource_name(name)
        parameters = {"location": self.provider.region_name,
                      'tags': {'Name': name}}

        if description:
            parameters['tags'].update(Description=description)

        fw = self.provider.azure_client.create_vm_firewall(name, parameters)
        cb_fw = AzureVMFirewall(self.provider, fw)

        return cb_fw

    def find(self, name, limit=None, marker=None):
        """
        Searches for a security group by a given list of attributes.
        """
        filters = {'Name': name}
        fws = [AzureVMFirewall(self.provider, vm_firewall)
               for vm_firewall in azure_helpers.filter(
                self.provider.azure_client.list_vm_firewall(), filters)]

        return ClientPagedResultList(self.provider, fws,
                                     limit=limit, marker=marker)

    def delete(self, group_id):
        try:
            self.provider.azure_client.delete_vm_firewall(group_id)
            return True
        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return False


class AzureKeyPairService(BaseKeyPairService):
    PARTITION_KEY = '00000000-0000-0000-0000-000000000000'

    def __init__(self, provider):
        super(AzureKeyPairService, self).__init__(provider)

    def get(self, key_pair_id):
        try:
            key_pair = self.provider.azure_client.\
                get_public_key(key_pair_id)

            if key_pair:
                return AzureKeyPair(self.provider, key_pair)
            return None
        except AzureException as error:
            log.exception(error)
            return None

    def list(self, limit=None, marker=None):
        key_pairs = [AzureKeyPair(self.provider, key_pair) for key_pair in
                     self.provider.azure_client.
                     list_public_keys(AzureKeyPairService.PARTITION_KEY)]
        return ClientPagedResultList(self.provider, key_pairs, limit, marker)

    def find(self, name, limit=None, marker=None):
        key_pair = self.get(name)
        return ClientPagedResultList(self.provider,
                                     [key_pair] if key_pair else [],
                                     limit, marker)

    def create(self, name):
        AzureKeyPair.assert_valid_resource_name(name)

        key_pair = self.get(name)

        if key_pair:
            raise Exception(
                'Keypair already exists with name {0}'.format(name))

        private_key_str, public_key_str = azure_helpers.gen_key_pair()

        entity = {
                  'PartitionKey': AzureKeyPairService.PARTITION_KEY,
                  'RowKey': str(uuid.uuid4()),
                  'Name': name,
                  'Key': public_key_str
                 }

        self.provider.azure_client.create_public_key(entity)

        key_pair = self.get(name)

        key_pair.material = private_key_str

        return key_pair


class AzureBucketService(BaseBucketService):
    def __init__(self, provider):
        super(AzureBucketService, self).__init__(provider)

    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        try:
            bucket = self.provider.azure_client.get_container(bucket_id)
            return AzureBucket(self.provider, bucket)

        except AzureException as error:
            log.exception(error)
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a bucket by a given list of attributes.
        """
        buckets = [AzureBucket(self.provider, bucket)
                   for bucket in
                   self.provider.azure_client.list_containers(prefix=name)]
        return ClientPagedResultList(self.provider, buckets,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all containers.
        """
        buckets = [AzureBucket(self.provider, bucket)
                   for bucket in self.provider.azure_client.list_containers()]
        return ClientPagedResultList(self.provider, buckets,
                                     limit=limit, marker=marker)

    def create(self, name, location=None):
        """
        Create a new bucket.
        """
        AzureBucket.assert_valid_resource_name(name)
        bucket = self.provider.azure_client.create_container(name.lower())
        return AzureBucket(self.provider, bucket)


class AzureStorageService(BaseStorageService):
    def __init__(self, provider):
        super(AzureStorageService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = AzureVolumeService(self.provider)
        self._snapshot_svc = AzureSnapshotService(self.provider)
        self._bucket_svc = AzureBucketService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc

    @property
    def buckets(self):
        return self._bucket_svc


class AzureVolumeService(BaseVolumeService):
    def __init__(self, provider):
        super(AzureVolumeService, self).__init__(provider)

    def get(self, volume_id):
        """
        Returns a volume given its id.
        """
        try:
            volume = self.provider.azure_client.get_disk(volume_id)
            return AzureVolume(self.provider, volume)
        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a volume by a given list of attributes.
        """
        filters = {'Name': name}
        cb_vols = [AzureVolume(self.provider, volume)
                   for volume in azure_helpers.filter(
                self.provider.azure_client.list_disks(), filters)]
        return ClientPagedResultList(self.provider, cb_vols,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all volumes.
        """
        azure_vols = self.provider.azure_client.list_disks()
        cb_vols = [AzureVolume(self.provider, vol) for vol in azure_vols]
        return ClientPagedResultList(self.provider, cb_vols,
                                     limit=limit, marker=marker)

    def create(self, name, size, zone=None, snapshot=None, description=None):
        """
        Creates a new volume.
        """
        AzureVolume.assert_valid_resource_name(name)
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        snapshot = (self.provider.storage.snapshots.get(snapshot)
                    if snapshot and isinstance(snapshot, str) else snapshot)
        disk_name = "{0}-{1}".format(name, uuid.uuid4().hex[:6])
        tags = {'Name': name}
        if description:
            tags.update(Description=description)
        if snapshot:
            params = {
                'location':
                    zone_id or self.provider.azure_client.region_name,
                'creation_data': {
                    'create_option': 'copy',
                    'source_uri': snapshot.resource_id
                },
                'tags': tags
            }

            self.provider.azure_client.create_snapshot_disk(disk_name, params)

        else:
            params = {
                'location':
                    zone_id or self.provider.region_name,
                'disk_size_gb': size,
                'creation_data': {
                    'create_option': 'empty'
                },
                'tags': tags}

            self.provider.azure_client.create_empty_disk(disk_name, params)

        azure_vol = self.provider.azure_client.get_disk(disk_name)
        cb_vol = AzureVolume(self.provider, azure_vol)

        return cb_vol


class AzureSnapshotService(BaseSnapshotService):
    def __init__(self, provider):
        super(AzureSnapshotService, self).__init__(provider)

    def get(self, ss_id):
        """
        Returns a snapshot given its id.
        """
        try:
            snapshot = self.provider.azure_client.get_snapshot(ss_id)
            return AzureSnapshot(self.provider, snapshot)
        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return None

    def find(self, name, limit=None, marker=None):
        """
             Searches for a snapshot by a given list of attributes.
        """
        filters = {'Name': name}
        cb_snapshots = [AzureSnapshot(self.provider, snapshot)
                        for snapshot in azure_helpers.filter(
                self.provider.azure_client.list_snapshots(), filters)]
        return ClientPagedResultList(self.provider, cb_snapshots,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
               List all snapshots.
        """
        snaps = [AzureSnapshot(self.provider, obj)
                 for obj in
                 self.provider.azure_client.list_snapshots()]
        return ClientPagedResultList(self.provider, snaps, limit, marker)

    def create(self, name, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        AzureSnapshot.assert_valid_resource_name(name)
        volume = (self.provider.storage.volumes.get(volume)
                  if isinstance(volume, str) else volume)

        tags = {'Name': name}
        snapshot_name = "{0}-{1}".format(name, uuid.uuid4().hex[:6])

        if description:
            tags.update(Description=description)

        params = {
            'location': self.provider.azure_client.region_name,
            'creation_data': {
                'create_option': 'Copy',
                'source_uri': volume.resource_id
            },
            'disk_size_gb': volume.size,
            'tags': tags
        }

        self.provider.azure_client. \
            create_snapshot(snapshot_name, params)
        azure_snap = self.provider.azure_client.get_snapshot(snapshot_name)
        cb_snap = AzureSnapshot(self.provider, azure_snap)

        return cb_snap


class AzureComputeService(BaseComputeService):
    def __init__(self, provider):
        super(AzureComputeService, self).__init__(provider)
        self._vm_type_svc = AzureVMTypeService(self.provider)
        self._instance_svc = AzureInstanceService(self.provider)
        self._region_svc = AzureRegionService(self.provider)
        self._images_svc = AzureImageService(self.provider)

    @property
    def images(self):
        return self._images_svc

    @property
    def vm_types(self):
        return self._vm_type_svc

    @property
    def instances(self):
        return self._instance_svc

    @property
    def regions(self):
        return self._region_svc


class AzureInstanceService(BaseInstanceService):
    def __init__(self, provider):
        super(AzureInstanceService, self).__init__(provider)

    def create(self, name, image, vm_type, subnet=None, zone=None,
               key_pair=None, vm_firewalls=None, user_data=None,
               launch_config=None, **kwargs):

        instance_name = name.replace("_", "-") if name \
            else "{0} - {1}".format("cb", uuid.uuid4())

        AzureInstance.assert_valid_resource_name(instance_name)

        # Key_pair is mandatory in azure and it should not be None.
        if key_pair:
            key_pair = (self.provider.security.key_pairs.get(key_pair)
                        if isinstance(key_pair, str) else key_pair)
        else:
            raise Exception("Can not create instance in azure "
                            "without public key. Keypair required")

        image = (self.provider.compute.images.get(image)
                 if isinstance(image, str) else image)

        instance_size = vm_type.id if \
            isinstance(vm_type, VMType) else vm_type

        if not subnet:
            subnet = self.provider.networking.subnets.get_or_create_default()
        else:
            subnet = (self.provider.networking.subnets.get(subnet)
                      if isinstance(subnet, str) else subnet)

        zone_id = zone.id if isinstance(zone, PlacementZone) else zone

        subnet_id, zone_id, vm_firewall_id = \
            self._resolve_launch_options(instance_name,
                                         subnet, zone_id, vm_firewalls)

        if launch_config:
            disks, root_disk_size = \
                self._process_block_device_mappings(launch_config,
                                                    name, zone_id)
        else:
            disks = None
            root_disk_size = None

        nic_params = {
                'location': self._provider.region_name,
                'ip_configurations': [{
                    'name': instance_name + '_ip_config',
                    'private_ip_allocation_method': 'Dynamic',
                    'subnet': {
                        'id': subnet_id
                    }
                }]
            }

        if vm_firewall_id:
            nic_params['network_security_group'] = {
                'id': vm_firewall_id
            }
        nic_info = self.provider.azure_client.create_nic(
            instance_name + '_nic',
            nic_params
        )
        # #! indicates shell script
        ud = '#cloud-config\n' + user_data \
            if user_data and not user_data.startswith('#!')\
            and not user_data.startswith('#cloud-config') else user_data

        params = {
            'location': zone_id or self._provider.region_name,
            'os_profile': {
                'admin_username': self.provider.vm_default_user_name,
                'computer_name': instance_name,
                'linux_configuration': {
                             "disable_password_authentication": True,
                             "ssh": {
                                 "public_keys": [{
                                      "path":
                                      "/home/{}/.ssh/authorized_keys".format(
                                          self.provider.vm_default_user_name),
                                      "key_data": key_pair._key_pair.Key
                                     }]
                                   }
                           }
            },
            'hardware_profile': {
                'vm_size': instance_size
            },
            'network_profile': {
                'network_interfaces': [{
                    'id': nic_info.id
                }]
            },
            'storage_profile': {
                'image_reference': {
                    'id': image.resource_id
                },
                "os_disk": {
                    "name": instance_name + '_os_disk',
                    "create_option": "fromImage"
                },
                'data_disks': disks
            },
            'tags': {'Name': name}
        }

        if key_pair:
            params['tags'].update(Key_Pair=key_pair.name)

        if root_disk_size:
            params['storage_profile']['os_disk']['disk_size_gb'] = \
                root_disk_size

        if user_data:
            custom_data = base64.b64encode(bytes(ud, 'utf-8'))
            params['os_profile']['custom_data'] = str(custom_data, 'utf-8')

        self.provider.azure_client.create_vm(instance_name, params)
        vm = self._provider.azure_client.get_vm(instance_name)
        return AzureInstance(self.provider, vm)

    def _resolve_launch_options(self, name, subnet=None, zone_id=None,
                                vm_firewalls=None):
        if subnet:
            # subnet's zone takes precedence
            zone_id = subnet.zone.id
        vm_firewall_id = None

        if isinstance(vm_firewalls, list) and len(vm_firewalls) > 0:

            if isinstance(vm_firewalls[0], VMFirewall):
                vm_firewalls_ids = [fw.id for fw in vm_firewalls]
                vm_firewall_id = vm_firewalls[0].resource_id
            else:
                vm_firewalls_ids = vm_firewalls
                vm_firewall = self.provider.security.\
                    vm_firewalls.get(vm_firewalls[0])
                vm_firewall_id = vm_firewall.resource_id

            if len(vm_firewalls) > 1:
                new_fw = self.provider.security.vm_firewalls.\
                    create('{0}-fw'.format(name), 'Merge vm firewall {0}'.
                           format(','.join(vm_firewalls_ids)))

                for fw in vm_firewalls:
                    new_fw.add_rule(src_dest_fw=fw)

                vm_firewall_id = new_fw.resource_id

        return subnet.resource_id, zone_id, vm_firewall_id

    def _process_block_device_mappings(self, launch_config,
                                       vm_name, zone=None):
        """
        Processes block device mapping information
        and returns a Data disk dictionary list. If new volumes
        are requested (source is None and destination is VOLUME), they will be
        created and the relevant volume ids included in the mapping.
        """
        disks = []
        volumes_count = 0
        root_disk_size = None

        def attach_volume(volume, delete_on_terminate):
            disks.append({
                'lun': volumes_count,
                'name': volume.id,
                'create_option': 'attach',
                'managed_disk': {
                    'id': volume.resource_id
                }
            })
            delete_on_terminate = delete_on_terminate or False
            volume.tags.update(delete_on_terminate=str(delete_on_terminate))
            # In azure, there is no option to specify terminate disks
            # (similar to AWS delete_on_terminate) on VM delete.
            # This method uses the azure tags functionality to store
            # the  delete_on_terminate option when the virtual machine
            # is deleted, we parse the tags and delete accordingly
            self.provider.azure_client.\
                update_disk_tags(volume.id, volume.tags)

        for device in launch_config.block_devices:
            if device.is_volume:
                if not device.is_root:
                    # In azure, os disk automatically created,
                    # we are ignoring the root disk, if specified
                    if isinstance(device.source, Snapshot):
                        snapshot_vol = device.source.create_volume()
                        attach_volume(snapshot_vol,
                                      device.delete_on_terminate)
                    elif isinstance(device.source, Volume):
                        attach_volume(device.source,
                                      device.delete_on_terminate)
                    elif isinstance(device.source, MachineImage):
                        # Not supported
                        pass
                    else:
                        # source is None, but destination is volume, therefore
                        # create a blank volume. If the Zone is None, this
                        # could fail since the volume and instance may
                        # be created in two different zones.
                        if not zone:
                            raise InvalidConfigurationException(
                                "A zone must be specified when "
                                "launching with a"
                                " new blank volume block device mapping.")
                        vol_name = \
                            "{0}_{1}_disk".format(vm_name,
                                                  uuid.uuid4().hex[:6])
                        new_vol = self.provider.storage.volumes.create(
                            vol_name,
                            device.size,
                            zone)
                        attach_volume(new_vol, device.delete_on_terminate)
                    volumes_count += 1
                else:
                    root_disk_size = device.size

            else:  # device is ephemeral
                # in azure we cannot add the ephemeral disks explicitly
                pass

        return disks, root_disk_size

    def create_launch_config(self):
        return AzureLaunchConfig(self.provider)

    def list(self, limit=None, marker=None):
        """
        List all instances.
        """
        instances = [AzureInstance(self.provider, inst)
                     for inst in self.provider.azure_client.list_vm()]
        return ClientPagedResultList(self.provider, instances,
                                     limit=limit, marker=marker)

    def get(self, instance_id):
        """
        Returns an instance given its id. Returns None
        if the object does not exist.
        """
        try:
            vm = self.provider.azure_client.get_vm(instance_id)
            return AzureInstance(self.provider, vm)
        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for an instance by a given list of attributes.

        :rtype: ``object`` of :class:`.Instance`
        :return: an Instance object
        """
        filtr = {'Name': name}
        instances = [AzureInstance(self.provider, inst)
                     for inst in azure_helpers.filter(
                self.provider.azure_client.list_vm(), filtr)]
        return ClientPagedResultList(self.provider, instances,
                                     limit=limit, marker=marker)


class AzureImageService(BaseImageService):
    def __init__(self, provider):
        super(AzureImageService, self).__init__(provider)

    def get(self, image_id):
        """
        Returns an Image given its id
        """
        try:
            image = self.provider.azure_client.get_image(image_id)
            return AzureMachineImage(self.provider, image)
        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return None

    def find(self, name, limit=None, marker=None):

        """
         Searches for a image by a given list of attributes.
        """
        filters = {'Name': name}
        cb_images = [AzureMachineImage(self.provider, image)
                     for image in azure_helpers.filter(
                self.provider.azure_client.list_images(), filters)]
        return ClientPagedResultList(self.provider, cb_images,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all images.
        """
        azure_images = self.provider.azure_client.list_images()
        cb_images = [AzureMachineImage(self.provider, img)
                     for img in azure_images]
        return ClientPagedResultList(self.provider, cb_images,
                                     limit=limit, marker=marker)


class AzureVMTypeService(BaseVMTypeService):

    def __init__(self, provider):
        super(AzureVMTypeService, self).__init__(provider)

    @property
    def instance_data(self):
        """
        Fetch info about the available instances.
        """
        r = self.provider.azure_client.list_vm_types()
        return r

    def list(self, limit=None, marker=None):
        vm_types = [AzureVMType(self.provider, vm_type)
                    for vm_type in self.instance_data]
        return ClientPagedResultList(self.provider, vm_types,
                                     limit=limit, marker=marker)


class AzureNetworkingService(BaseNetworkingService):
    def __init__(self, provider):
        super(AzureNetworkingService, self).__init__(provider)
        self._network_service = AzureNetworkService(self.provider)
        self._subnet_service = AzureSubnetService(self.provider)
        self._fip_service = AzureFloatingIPService(self.provider)
        self._router_service = AzureRouterService(self.provider)
        self._gateway_service = AzureGatewayService(self.provider)

    @property
    def networks(self):
        return self._network_service

    @property
    def subnets(self):
        return self._subnet_service

    @property
    def floating_ips(self):
        return self._fip_service

    @property
    def routers(self):
        return self._router_service

    @property
    def gateways(self):
        return self._gateway_service


class AzureNetworkService(BaseNetworkService):
    def __init__(self, provider):
        super(AzureNetworkService, self).__init__(provider)

    def get(self, network_id):
        try:
            network = self.provider.azure_client.get_network(network_id)
            return AzureNetwork(self.provider, network)

        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return None

    def list(self, limit=None, marker=None):
        """
        List all networks.
        """
        networks = [AzureNetwork(self.provider, network)
                    for network in self.provider.azure_client.list_networks()]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        filters = {'Name': name}
        networks = [AzureNetwork(self.provider, network)
                    for network in azure_helpers.filter(
                self.provider.azure_client.list_networks(), filters)]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    def create(self, name, cidr_block):
        # Azure requires CIDR block to be specified when creating a network
        # so set a default one and use the largest allowed netmask.
        network_name = AzureNetwork.CB_DEFAULT_NETWORK_NAME
        if name:
            network_name = "{0}-{1}".format(name, uuid.uuid4().hex[:6])

        AzureNetwork.assert_valid_resource_name(network_name)

        params = {
            'location': self.provider.azure_client.region_name,
            'address_space': {
                'address_prefixes': [cidr_block]
            },
            'tags': {'Name': name or AzureNetwork.CB_DEFAULT_NETWORK_NAME}
        }
        self.provider.azure_client.create_network(network_name, params)
        network = self.provider.azure_client.get_network(network_name)
        cb_network = AzureNetwork(self.provider, network)
        return cb_network

    def delete(self, network_id):
        """
        Delete an existing network.
        """
        try:
            self.provider.azure_client.delete_network(network_id)
            return True
        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return False


class AzureFloatingIPService(BaseFloatingIPService):

    def __init__(self, provider):
        super(AzureFloatingIPService, self).__init__(provider)

    def get(self, floating_ip):
        log.debug("Getting AWS Floating IP Service with the id: %s",
                  floating_ip)
        fip = [fip for fip in self.list() if fip.id == floating_ip]
        return fip[0] if fip else None

    def list(self, limit=None, marker=None):
        floating_ips = [AzureFloatingIP(self.provider, floating_ip)
                        for floating_ip in self.provider.azure_client.
                        list_floating_ips()]
        return ClientPagedResultList(self.provider, floating_ips,
                                     limit=limit, marker=marker)

    def create(self):
        public_ip_address_name = "{0}-{1}".format(
            'public_ip', uuid.uuid4().hex[:6])
        public_ip_parameters = {
            'location': self.provider.azure_client.region_name,
            'public_ip_allocation_method': 'Static'
        }

        floating_ip = self.provider.azure_client.\
            create_floating_ip(public_ip_address_name, public_ip_parameters)
        return AzureFloatingIP(self.provider, floating_ip)


class AzureRegionService(BaseRegionService):
    def __init__(self, provider):
        super(AzureRegionService, self).__init__(provider)

    def get(self, region_id):
        region = None
        for azureRegion in self.provider.azure_client.list_locations():
            if azureRegion.name == region_id:
                region = AzureRegion(self.provider, azureRegion)
                break
        return region

    def list(self, limit=None, marker=None):
        regions = [AzureRegion(self.provider, region)
                   for region in self.provider.azure_client.list_locations()]
        return ClientPagedResultList(self.provider, regions,
                                     limit=limit, marker=marker)

    @property
    def current(self):
        return self.get(self.provider.region_name)


class AzureSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(AzureSubnetService, self).__init__(provider)

    def get(self, subnet_id):
        """
         Azure does not provide an api to get the subnet directly by id.
         It also requires the network id.
         To make it consistent across the providers the following code
         gets the specific code from the subnet list.

        :param subnet_id:
        :return:
        """
        try:
            subnet_id_parts = subnet_id.split('|$|')
            if (len(subnet_id_parts) != 2):
                return None
            azure_subnet = self.provider.azure_client.\
                get_subnet(subnet_id_parts[0], subnet_id_parts[1])
            return AzureSubnet(self.provider,
                               azure_subnet) if azure_subnet else None
        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return None

    def list(self, network=None, limit=None, marker=None):
        """
        List subnets
        """
        return ClientPagedResultList(self.provider,
                                     self._list_subnets(network),
                                     limit=limit, marker=marker)

    def _list_subnets(self, network=None):
        result_list = []
        if network:
            network_id = network.id \
                if isinstance(network, Network) else network
            result_list = self.provider.azure_client.list_subnets(network_id)
        else:
            for net in self.provider.azure_client.list_networks():
                result_list.extend(self.provider.azure_client.list_subnets(
                    net.name
                ))
        subnets = [AzureSubnet(self.provider, subnet)
                   for subnet in result_list]

        return subnets

    def create(self, network, cidr_block, name=None, **kwargs):
        """
        Create subnet
        """
        AzureSubnet.assert_valid_resource_name(name)
        network_id = network.id \
            if isinstance(network, Network) else network

        if not name:
            subnet_name = AzureSubnet.CB_DEFAULT_SUBNET_NAME
        else:
            subnet_name = name

        subnet_info = self.provider.azure_client\
            .create_subnet(
                            network_id,
                            subnet_name,
                            {
                                'address_prefix': cidr_block
                            }
                          )

        return AzureSubnet(self.provider, subnet_info)

    def get_or_create_default(self, zone=None):
        default_cdir = '10.0.1.0/24'
        network = None
        subnet = None

        # No provider-default Subnet exists, look for a library-default one
        try:
            subnet = self.provider.azure_client.get_subnet(
                AzureNetwork.CB_DEFAULT_NETWORK_NAME,
                AzureSubnet.CB_DEFAULT_SUBNET_NAME
            )
        except CloudError:
            # Azure raises the cloud error if the resource not available
            pass

        if subnet:
            return AzureSubnet(self.provider, subnet)

        # No provider-default Subnet exists, try to create it (net + subnets)
        default_net_name = AzureNetwork.CB_DEFAULT_NETWORK_NAME
        try:
            network = self.provider.azure_client \
                .get_network(default_net_name)
        except CloudError:
            # Azure raises the cloud error if the resource not available
            pass

        if not network:
            network = self.provider.networking.networks.create(
                name=default_net_name, cidr_block='10.0.0.0/16')

        subnet = self.provider.azure_client.create_subnet(
            network.id,
            AzureSubnet.CB_DEFAULT_SUBNET_NAME,
            {'address_prefix': default_cdir}
        )

        return AzureSubnet(self.provider, subnet)

    def delete(self, subnet):
        try:
            # Azure does not provide an api to delete the subnet by id
            # It also requires network id. To get the network id
            # code is doing an explicit get and retrieving the network id

            subnet_id = subnet.id if isinstance(subnet, Subnet) else subnet
            subnet_id_parts = subnet_id.split('|$|')
            self.provider.azure_client.\
                delete_subnet(subnet_id_parts[0], subnet_id_parts[1])
            return True
        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return False


class AzureRouterService(BaseRouterService):
    def __init__(self, provider):
        super(AzureRouterService, self).__init__(provider)

    def get(self, router_id):
        try:
            route = self.provider.azure_client.get_route_table(router_id)
            return AzureRouter(self.provider, route)

        except CloudError as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError.message)
            return None

    def find(self, name, limit=None, marker=None):
        filters = {'Name': name}
        routes = [AzureRouter(self.provider, route)
                  for route in azure_helpers.filter(
                self.provider.azure_client.list_route_tables(), filters)]

        return ClientPagedResultList(self.provider, routes,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        routes = [AzureRouter(self.provider, route)
                  for route in
                  self.provider.azure_client.list_route_tables()]
        return ClientPagedResultList(self.provider,
                                     routes,
                                     limit=limit, marker=marker)

    def create(self, name, network):
        AzureRouter.assert_valid_resource_name(name)
        parameters = {"location": self.provider.region_name,
                      'tags': {'Name': name}}
        route = self.provider.azure_client. \
            create_route_table(name, parameters)
        return AzureRouter(self.provider, route)


class AzureGatewayService(BaseGatewayService):
    def __init__(self, provider):
        super(AzureGatewayService, self).__init__(provider)
        # Singleton returned by the list method
        self.gateway_singleton = AzureInternetGateway(self.provider, None)

    def get_or_create_inet_gateway(self, name):
        AzureInternetGateway.assert_valid_resource_name(name)
        gateway = AzureInternetGateway(self.provider, None)
        gateway.name = name
        return gateway

    def list(self, limit=None, marker=None):
        return [self.gateway_singleton]

    def delete(self, gateway):
        pass
