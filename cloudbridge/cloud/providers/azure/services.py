import base64
import logging
import uuid

from azure.common import AzureException
from azure.mgmt.compute.models import DiskCreateOption

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.base.resources import ClientPagedResultList, \
    ServerPagedResultList
from cloudbridge.cloud.base.services import BaseBucketService, \
    BaseComputeService, \
    BaseImageService, BaseInstanceService, BaseKeyPairService, \
    BaseNetworkService, BaseNetworkingService, BaseRegionService, \
    BaseRouterService, BaseSecurityService, BaseSnapshotService, \
    BaseStorageService, BaseSubnetService, BaseVMFirewallService, \
    BaseVMTypeService, BaseVolumeService
from cloudbridge.cloud.interfaces.exceptions import \
    DuplicateResourceException, InvalidValueException
from cloudbridge.cloud.interfaces.resources import MachineImage, \
    Network, PlacementZone, Snapshot, Subnet, VMFirewall, VMType, Volume

from msrestazure.azure_exceptions import CloudError

from . import helpers as azure_helpers
from .resources import AzureBucket, \
    AzureInstance, AzureKeyPair, \
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
        except (CloudError, InvalidValueException) as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError)
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

        # Add default rules to negate azure default rules.
        # See: https://github.com/CloudVE/cloudbridge/issues/106
        # pylint:disable=protected-access
        for rule in fw.default_security_rules:
            rule_name = "cb-override-" + rule.name
            # Transpose rules to priority 4001 onwards, because
            # only 0-4096 are allowed for custom rules
            rule.priority = rule.priority - 61440
            rule.access = "Deny"
            self._provider.azure_client.create_vm_firewall_rule(
                fw.id, rule_name, rule)

        # Add a new custom rule allowing all outbound traffic to the internet
        parameters = {"priority": 3000,
                      "protocol": "*",
                      "source_port_range": "*",
                      "source_address_prefix": "*",
                      "destination_port_range": "*",
                      "destination_address_prefix": "Internet",
                      "access": "Allow",
                      "direction": "Outbound"}
        result = self._provider.azure_client.create_vm_firewall_rule(
            fw.id, "cb-default-internet-outbound", parameters)
        fw.security_rules.append(result)

        cb_fw = AzureVMFirewall(self.provider, fw)
        return cb_fw

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        filters = {'Name': name}
        fws = [AzureVMFirewall(self.provider, vm_firewall)
               for vm_firewall in azure_helpers.filter_by_tag(
               self.provider.azure_client.list_vm_firewall(), filters)]
        return ClientPagedResultList(self.provider, fws)

    def delete(self, group_id):
        self.provider.azure_client.delete_vm_firewall(group_id)


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
        key_pairs, resume_marker = self.provider.azure_client.list_public_keys(
            AzureKeyPairService.PARTITION_KEY, marker=marker,
            limit=limit or self.provider.config.default_result_limit)
        results = [AzureKeyPair(self.provider, key_pair)
                   for key_pair in key_pairs]
        return ServerPagedResultList(is_truncated=resume_marker,
                                     marker=resume_marker,
                                     supports_total=False,
                                     data=results)

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        key_pair = self.get(name)
        return ClientPagedResultList(self.provider,
                                     [key_pair] if key_pair else [])

    def create(self, name, public_key_material=None):
        AzureKeyPair.assert_valid_resource_name(name)

        key_pair = self.get(name)

        if key_pair:
            raise DuplicateResourceException(
                'Keypair already exists with name {0}'.format(name))

        private_key = None
        if not public_key_material:
            public_key_material, private_key = cb_helpers.generate_key_pair()

        entity = {
            'PartitionKey': AzureKeyPairService.PARTITION_KEY,
            'RowKey': str(uuid.uuid4()),
            'Name': name,
            'Key': public_key_material
        }

        self.provider.azure_client.create_public_key(entity)
        key_pair = self.get(name)
        key_pair.material = private_key
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

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        buckets = [AzureBucket(self.provider, bucket)
                   for bucket in
                   self.provider.azure_client.list_containers(prefix=name)]
        return ClientPagedResultList(self.provider, buckets)

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
        except (CloudError, InvalidValueException) as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError)
            return None

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        filters = {'Name': name}
        cb_vols = [AzureVolume(self.provider, volume)
                   for volume in azure_helpers.filter_by_tag(
                   self.provider.azure_client.list_disks(), filters)]
        return ClientPagedResultList(self.provider, cb_vols)

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
                    'create_option': DiskCreateOption.copy,
                    'source_uri': snapshot.resource_id
                },
                'tags': tags
            }

            disk = self.provider.azure_client.create_snapshot_disk(disk_name,
                                                                   params)

        else:
            params = {
                'location':
                    zone_id or self.provider.region_name,
                'disk_size_gb': size,
                'creation_data': {
                    'create_option': DiskCreateOption.empty
                },
                'tags': tags}

            disk = self.provider.azure_client.create_empty_disk(disk_name,
                                                                params)

        azure_vol = self.provider.azure_client.get_disk(disk.id)
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
        except (CloudError, InvalidValueException) as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError)
            return None

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        filters = {'Name': name}
        cb_snapshots = [AzureSnapshot(self.provider, snapshot)
                        for snapshot in azure_helpers.filter_by_tag(
                        self.provider.azure_client.list_snapshots(), filters)]
        return ClientPagedResultList(self.provider, cb_snapshots)

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
                'create_option': DiskCreateOption.copy,
                'source_uri': volume.resource_id
            },
            'disk_size_gb': volume.size,
            'tags': tags
        }

        azure_snap = self.provider.azure_client.create_snapshot(snapshot_name,
                                                                params)
        return AzureSnapshot(self.provider, azure_snap)


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
        temp_key_pair = None
        if key_pair:
            key_pair = (self.provider.security.key_pairs.get(key_pair)
                        if isinstance(key_pair, str) else key_pair)
        else:
            # Create a temporary keypair if none is provided to keep Azure
            # happy, but the private key will be discarded, so it'll be all
            # but useless. However, this will allow an instance to be launched
            # without specifying a keypair, so users may still be able to login
            # if they have a preinstalled keypair/password baked into the image
            default_kp_name = "cb_default_key_pair"
            default_kp = self.provider.security.key_pairs.find(
                name=default_kp_name)
            if default_kp:
                key_pair = default_kp[0]
            else:
                key_pair = self.provider.security.key_pairs.create(
                    name=default_kp_name)
                temp_key_pair = key_pair

        image = (image if isinstance(image, AzureMachineImage) else
                 self.provider.compute.images.get(image))
        if not isinstance(image, AzureMachineImage):
            raise Exception("Provided image %s is not a valid azure image"
                            % image)

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

        storage_profile = self._create_storage_profile(image, launch_config,
                                                       instance_name, zone_id)

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
            'storage_profile': storage_profile,
            'tags': {'Name': name}
        }

        if key_pair:
            params['tags'].update(Key_Pair=key_pair.name)

        if user_data:
            custom_data = base64.b64encode(bytes(ud, 'utf-8'))
            params['os_profile']['custom_data'] = str(custom_data, 'utf-8')

        try:
            vm = self.provider.azure_client.create_vm(instance_name, params)
        except Exception as e:
            # If VM creation fails, attempt to clean up intermediary resources
            self.provider.azure_client.delete_nic(nic_info.id)
            for disk_def in storage_profile.get('data_disks', []):
                if disk_def.get('tags', {}).get('delete_on_terminate'):
                    disk_id = disk_def.get('managed_disk', {}).get('id')
                    if disk_id:
                        vol = self.provider.storage.volumes.get(disk_id)
                        vol.delete()
            raise e
        finally:
            if temp_key_pair:
                temp_key_pair.delete()
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

    def _create_storage_profile(self, image, launch_config, instance_name,
                                zone_id):

        if image.is_gallery_image:
            reference = image._image.as_dict()
            image_ref = {
                'publisher': reference['publisher'],
                'offer': reference['offer'],
                'sku': reference['sku'],
                'version': reference['version']
            }
        else:
            image_ref = {
                'id': image.resource_id
            }

        storage_profile = {
            'image_reference': image_ref,
            "os_disk": {
                "name": instance_name + '_os_disk',
                "create_option": DiskCreateOption.from_image
            },
        }

        if launch_config:
            data_disks, root_disk_size = self._process_block_device_mappings(
                launch_config, instance_name, zone_id)
            if data_disks:
                storage_profile['data_disks'] = data_disks
            if root_disk_size:
                storage_profile['os_disk']['disk_size_gb'] = root_disk_size

        return storage_profile

    def _process_block_device_mappings(self, launch_config,
                                       vm_name, zone=None):
        """
        Processes block device mapping information
        and returns a Data disk dictionary list. If new volumes
        are requested (source is None and destination is VOLUME), they will be
        created and the relevant volume ids included in the mapping.
        """
        data_disks = []
        root_disk_size = None

        def append_disk(disk_def, device_no, delete_on_terminate):
            # In azure, there is no option to specify terminate disks
            # (similar to AWS delete_on_terminate) on VM delete.
            # This method uses the azure tags functionality to store
            # the  delete_on_terminate option when the virtual machine
            # is deleted, we parse the tags and delete accordingly
            disk_def['lun'] = device_no
            disk_def['tags'] = {
                'delete_on_terminate': delete_on_terminate
            }
            data_disks.append(disk_def)

        for device_no, device in enumerate(launch_config.block_devices):
            if device.is_volume:
                if device.is_root:
                    root_disk_size = device.size
                else:
                    # In azure, os disk automatically created,
                    # we are ignoring the root disk, if specified
                    if isinstance(device.source, Snapshot):
                        snapshot_vol = device.source.create_volume()
                        disk_def = {
                            # pylint:disable=protected-access
                            'name': snapshot_vol._volume.name,
                            'create_option': DiskCreateOption.attach,
                            'managed_disk': {
                                'id': snapshot_vol.id
                            }
                        }
                    elif isinstance(device.source, Volume):
                        disk_def = {
                            # pylint:disable=protected-access
                            'name': device.source._volume.name,
                            'create_option': DiskCreateOption.attach,
                            'managed_disk': {
                                'id': device.source.id
                            }
                        }
                    elif isinstance(device.source, MachineImage):
                        disk_def = {
                            # pylint:disable=protected-access
                            'name': device.source._volume.name,
                            'create_option': DiskCreateOption.from_image,
                            'source_resource_id': device.source.id
                        }
                    else:
                        disk_def = {
                            # pylint:disable=protected-access
                            'create_option': DiskCreateOption.empty,
                            'disk_size_gb': device.size
                        }
                    append_disk(disk_def, device_no,
                                device.delete_on_terminate)
            else:  # device is ephemeral
                # in azure we cannot add the ephemeral disks explicitly
                pass

        return data_disks, root_disk_size

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
        except (CloudError, InvalidValueException) as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError)
            return None

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        filtr = {'Name': name}
        instances = [AzureInstance(self.provider, inst)
                     for inst in azure_helpers.filter_by_tag(
                     self.provider.azure_client.list_vm(), filtr)]
        return ClientPagedResultList(self.provider, instances)


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
        except (CloudError, InvalidValueException) as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError)
            return None

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        filters = {'Name': name}
        cb_images = [AzureMachineImage(self.provider, image)
                     for image in azure_helpers.filter_by_tag(
                     self.provider.azure_client.list_images(), filters)]
        # All gallery image properties (id, resource_id, name) are the URN
        # Improvement: wrap the filters by publisher, offer, etc...
        cb_images.extend([AzureMachineImage(self.provider, image) for image
                          in self.provider.azure_client.list_gallery_refs()
                          if azure_helpers.generate_urn(image) == name])
        return ClientPagedResultList(self.provider, cb_images)

    def list(self, limit=None, marker=None):
        """
        List all images.
        """
        azure_images = self.provider.azure_client.list_images()
        azure_gallery_refs = self.provider.azure_client.list_gallery_refs()
        cb_images = [AzureMachineImage(self.provider, img)
                     for img in azure_images + azure_gallery_refs]
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
        self._router_service = AzureRouterService(self.provider)

    @property
    def networks(self):
        return self._network_service

    @property
    def subnets(self):
        return self._subnet_service

    @property
    def routers(self):
        return self._router_service


class AzureNetworkService(BaseNetworkService):
    def __init__(self, provider):
        super(AzureNetworkService, self).__init__(provider)

    def get(self, network_id):
        try:
            network = self.provider.azure_client.get_network(network_id)
            return AzureNetwork(self.provider, network)
        except (CloudError, InvalidValueException) as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError)
            return None

    def list(self, limit=None, marker=None):
        """
        List all networks.
        """
        networks = [AzureNetwork(self.provider, network)
                    for network in self.provider.azure_client.list_networks()]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        filters = {'Name': name}
        networks = [
            AzureNetwork(self.provider, network) for network
            in azure_helpers.filter_by_tag(
                self.provider.azure_client.list_networks(), filters)]
        return ClientPagedResultList(self.provider, networks)

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
        az_network = self.provider.azure_client.create_network(network_name,
                                                               params)
        cb_network = AzureNetwork(self.provider, az_network)
        return cb_network

    def delete(self, network_id):
        """
        Delete an existing network.
        """
        self.provider.azure_client.delete_network(network_id)


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
            azure_subnet = self.provider.azure_client.get_subnet(subnet_id)
            return AzureSubnet(self.provider,
                               azure_subnet) if azure_subnet else None
        except (CloudError, InvalidValueException) as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError)
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
                    net.id
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
        default_cidr = '10.0.1.0/24'

        # No provider-default Subnet exists, look for a library-default one
        matches = self.find(name=AzureSubnet.CB_DEFAULT_SUBNET_NAME)
        if matches:
            return matches[0]

        # No provider-default Subnet exists, try to create it (net + subnets)
        networks = self.provider.networking.networks.find(
            name=AzureNetwork.CB_DEFAULT_NETWORK_NAME)

        if networks:
            network = networks[0]
        else:
            network = self.provider.networking.networks.create(
                AzureNetwork.CB_DEFAULT_NETWORK_NAME, '10.0.0.0/16')

        subnet = self.create(network, default_cidr,
                             name=AzureSubnet.CB_DEFAULT_SUBNET_NAME)
        return subnet

    def delete(self, subnet):
        subnet_id = subnet.id if isinstance(subnet, Subnet) else subnet
        self.provider.azure_client.delete_subnet(subnet_id)


class AzureRouterService(BaseRouterService):
    def __init__(self, provider):
        super(AzureRouterService, self).__init__(provider)

    def get(self, router_id):
        try:
            route = self.provider.azure_client.get_route_table(router_id)
            return AzureRouter(self.provider, route)
        except (CloudError, InvalidValueException) as cloudError:
            # Azure raises the cloud error if the resource not available
            log.exception(cloudError)
            return None

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        filters = {'Name': name}
        routes = [AzureRouter(self.provider, route)
                  for route in azure_helpers.filter_by_tag(
                  self.provider.azure_client.list_route_tables(), filters)]

        return ClientPagedResultList(self.provider, routes)

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
