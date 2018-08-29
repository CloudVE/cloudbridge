"""
Services implemented by the OpenStack provider.
"""
import logging

from cinderclient.exceptions import NotFound as CinderNotFound

from neutronclient.common.exceptions import NeutronClientException

from novaclient.exceptions import NotFound as NovaNotFound

from openstack.exceptions import NotFoundException
from openstack.exceptions import ResourceNotFound

from swiftclient import ClientException as SwiftClientException

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.base.resources import BaseLaunchConfig
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.services import BaseBucketService
from cloudbridge.cloud.base.services import BaseComputeService
from cloudbridge.cloud.base.services import BaseImageService
from cloudbridge.cloud.base.services import BaseInstanceService
from cloudbridge.cloud.base.services import BaseKeyPairService
from cloudbridge.cloud.base.services import BaseNetworkService
from cloudbridge.cloud.base.services import BaseNetworkingService
from cloudbridge.cloud.base.services import BaseRegionService
from cloudbridge.cloud.base.services import BaseRouterService
from cloudbridge.cloud.base.services import BaseSecurityService
from cloudbridge.cloud.base.services import BaseSnapshotService
from cloudbridge.cloud.base.services import BaseStorageService
from cloudbridge.cloud.base.services import BaseSubnetService
from cloudbridge.cloud.base.services import BaseVMFirewallService
from cloudbridge.cloud.base.services import BaseVMTypeService
from cloudbridge.cloud.base.services import BaseVolumeService
from cloudbridge.cloud.interfaces.exceptions \
    import DuplicateResourceException
from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import MachineImage
from cloudbridge.cloud.interfaces.resources import PlacementZone
from cloudbridge.cloud.interfaces.resources import Snapshot
from cloudbridge.cloud.interfaces.resources import Subnet
from cloudbridge.cloud.interfaces.resources import VMFirewall
from cloudbridge.cloud.interfaces.resources import VMType
from cloudbridge.cloud.interfaces.resources import Volume
from cloudbridge.cloud.providers.openstack import helpers as oshelpers

from .resources import OpenStackBucket
from .resources import OpenStackInstance
from .resources import OpenStackKeyPair
from .resources import OpenStackMachineImage
from .resources import OpenStackNetwork
from .resources import OpenStackRegion
from .resources import OpenStackRouter
from .resources import OpenStackSnapshot
from .resources import OpenStackSubnet
from .resources import OpenStackVMFirewall
from .resources import OpenStackVMType
from .resources import OpenStackVolume

log = logging.getLogger(__name__)


class OpenStackSecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(OpenStackSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = OpenStackKeyPairService(provider)
        self._vm_firewalls = OpenStackVMFirewallService(provider)

    @property
    def key_pairs(self):
        """
        Provides access to key pairs for this provider.

        :rtype: ``object`` of :class:`.KeyPairService`
        :return: a KeyPairService object
        """
        return self._key_pairs

    @property
    def vm_firewalls(self):
        """
        Provides access to VM firewalls for this provider.

        :rtype: ``object`` of :class:`.VMFirewallService`
        :return: a VMFirewallService object
        """
        return self._vm_firewalls

    def get_or_create_ec2_credentials(self):
        """
        A provider specific method than returns the ec2 credentials for the
        current user, or creates a new pair if one doesn't exist.
        """
        keystone = self.provider.keystone
        if hasattr(keystone, 'ec2'):
            user_id = keystone.session.get_user_id()
            user_creds = [cred for cred in keystone.ec2.list(user_id) if
                          cred.tenant_id == keystone.session.get_project_id()]
            if user_creds:
                return user_creds[0]
            else:
                return keystone.ec2.create(
                    user_id, keystone.session.get_project_id())

        return None

    def get_ec2_endpoints(self):
        """
        A provider specific method than returns the ec2 endpoints if
        available.
        """
        keystone = self.provider.keystone
        ec2_url = keystone.session.get_endpoint(service_type='ec2')
        s3_url = keystone.session.get_endpoint(service_type='s3')

        return {'ec2_endpoint': ec2_url,
                's3_endpoint': s3_url}


class OpenStackKeyPairService(BaseKeyPairService):

    def __init__(self, provider):
        super(OpenStackKeyPairService, self).__init__(provider)

    def get(self, key_pair_id):
        """
        Returns a KeyPair given its id.
        """
        log.debug("Returning KeyPair with the id %s", key_pair_id)
        try:
            return OpenStackKeyPair(
                self.provider, self.provider.nova.keypairs.get(key_pair_id))
        except NovaNotFound:
            log.debug("KeyPair %s was not found.", key_pair_id)
            return None

    def list(self, limit=None, marker=None):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        keypairs = self.provider.nova.keypairs.list()
        results = [OpenStackKeyPair(self.provider, kp)
                   for kp in keypairs]
        log.debug("Listing all key pairs associated with OpenStack "
                  "Account: %s", results)
        return ClientPagedResultList(self.provider, results,
                                     limit=limit, marker=marker)

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        keypairs = self.provider.nova.keypairs.findall(name=name)
        results = [OpenStackKeyPair(self.provider, kp)
                   for kp in keypairs]
        log.debug("Searching for %s in: %s", name, keypairs)
        return ClientPagedResultList(self.provider, results)

    def create(self, name, public_key_material=None):
        log.debug("Creating a new key pair with the name: %s", name)
        OpenStackKeyPair.assert_valid_resource_name(name)

        existing_kp = self.find(name=name)
        if existing_kp:
            raise DuplicateResourceException(
                'Keypair already exists with name {0}'.format(name))

        private_key = None
        if not public_key_material:
            public_key_material, private_key = cb_helpers.generate_key_pair()

        kp = self.provider.nova.keypairs.create(name,
                                                public_key=public_key_material)
        cb_kp = OpenStackKeyPair(self.provider, kp)
        cb_kp.material = private_key
        return cb_kp


class OpenStackVMFirewallService(BaseVMFirewallService):

    def __init__(self, provider):
        super(OpenStackVMFirewallService, self).__init__(provider)

    def get(self, firewall_id):
        log.debug("Getting OpenStack VM Firewall with the id: %s", firewall_id)
        try:
            return OpenStackVMFirewall(
                self.provider,
                self.provider.os_conn.network.get_security_group(firewall_id))
        except (ResourceNotFound, NotFoundException):
            log.debug("Firewall %s not found.", firewall_id)
            return None

    def list(self, limit=None, marker=None):
        firewalls = [
            OpenStackVMFirewall(self.provider, fw)
            for fw in self.provider.os_conn.network.security_groups()]

        return ClientPagedResultList(self.provider, firewalls,
                                     limit=limit, marker=marker)

    def create(self, label, description, network_id):
        OpenStackVMFirewall.assert_valid_resource_label(label)
        name = OpenStackVMFirewall._generate_name_from_label(label, 'cb-fw')
        log.debug("Creating OpenStack VM Firewall with the params: "
                  "[label: %s network id: %s description: %s]", label,
                  network_id, description)
        sg = self.provider.os_conn.network.create_security_group(
            name=name, description=description or name)
        if sg:
            return OpenStackVMFirewall(self.provider, sg)
        return None

    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for %s", label)
        sgs = [self.provider.os_conn.network.find_security_group(label)]
        results = [OpenStackVMFirewall(self.provider, sg)
                   for sg in sgs if sg]
        return ClientPagedResultList(self.provider, results)

    def delete(self, group_id):
        log.debug("Deleting OpenStack Firewall with the id: %s", group_id)
        firewall = self.get(group_id)
        if firewall:
            firewall.delete()
        return True


class OpenStackImageService(BaseImageService):

    def __init__(self, provider):
        super(OpenStackImageService, self).__init__(provider)

    def get(self, image_id):
        """
        Returns an Image given its id
        """
        log.debug("Getting OpenStack Image with the id: %s", image_id)
        try:
            return OpenStackMachineImage(
                self.provider, self.provider.os_conn.image.get_image(image_id))
        except (NotFoundException, ResourceNotFound):
            log.debug("Image %s not found", image_id)
            return None

    def find(self, **kwargs):
        filters = ['name', 'label']
        obj_list = self
        return cb_helpers.generic_find(filters, kwargs, obj_list)

    def list(self, filter_by_owner=True, limit=None, marker=None):
        """
        List all images.
        """
        project_id = None
        if filter_by_owner:
            project_id = self.provider.os_conn.session.get_project_id()
        os_images = self.provider.os_conn.image.images(
            owner=project_id,
            limit=oshelpers.os_result_limit(self.provider, limit),
            marker=marker)

        cb_images = [
            OpenStackMachineImage(self.provider, img)
            for img in os_images]
        return oshelpers.to_server_paged_list(self.provider, cb_images, limit)


class OpenStackVMTypeService(BaseVMTypeService):

    def __init__(self, provider):
        super(OpenStackVMTypeService, self).__init__(provider)

    def list(self, limit=None, marker=None):
        cb_itypes = [
            OpenStackVMType(self.provider, obj)
            for obj in self.provider.nova.flavors.list(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)]

        return oshelpers.to_server_paged_list(self.provider, cb_itypes, limit)


class OpenStackStorageService(BaseStorageService):

    def __init__(self, provider):
        super(OpenStackStorageService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = OpenStackVolumeService(self.provider)
        self._snapshot_svc = OpenStackSnapshotService(self.provider)
        self._bucket_svc = OpenStackBucketService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc

    @property
    def buckets(self):
        return self._bucket_svc


class OpenStackVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(OpenStackVolumeService, self).__init__(provider)

    def get(self, volume_id):
        """
        Returns a volume given its id.
        """
        log.debug("Getting OpenStack Volume with the id: %s", volume_id)
        try:
            return OpenStackVolume(
                self.provider, self.provider.cinder.volumes.get(volume_id))
        except CinderNotFound:
            log.debug("Volume %s was not found.", volume_id)
            return None

    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for an OpenStack Volume with the label %s", label)
        search_opts = {'name': label}
        cb_vols = [
            OpenStackVolume(self.provider, vol)
            for vol in self.provider.cinder.volumes.list(
                search_opts=search_opts,
                limit=oshelpers.os_result_limit(self.provider),
                marker=None)]

        return oshelpers.to_server_paged_list(self.provider, cb_vols)

    def list(self, limit=None, marker=None):
        """
        List all volumes.
        """
        cb_vols = [
            OpenStackVolume(self.provider, vol)
            for vol in self.provider.cinder.volumes.list(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)]

        return oshelpers.to_server_paged_list(self.provider, cb_vols, limit)

    def create(self, label, size, zone, snapshot=None, description=None):
        """
        Creates a new volume.
        """
        log.debug("Creating a new volume with the params: "
                  "[label: %s size: %s zone: %s snapshot: %s description: %s]",
                  label, size, zone, snapshot, description)
        OpenStackVolume.assert_valid_resource_label(label)

        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.id if isinstance(
            snapshot, OpenStackSnapshot) and snapshot else snapshot

        os_vol = self.provider.cinder.volumes.create(
            size, name=label, description=description,
            availability_zone=zone_id, snapshot_id=snapshot_id)
        return OpenStackVolume(self.provider, os_vol)


class OpenStackSnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(OpenStackSnapshotService, self).__init__(provider)

    def get(self, snapshot_id):
        """
        Returns a snapshot given its id.
        """
        log.debug("Getting OpenStack snapshot with the id: %s", snapshot_id)
        try:
            return OpenStackSnapshot(
                self.provider,
                self.provider.cinder.volume_snapshots.get(snapshot_id))
        except CinderNotFound:
            log.debug("Snapshot %s was not found.", snapshot_id)
            return None

    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        search_opts = {'name': label,  # TODO: Cinder is ignoring name
                       'limit': oshelpers.os_result_limit(self.provider),
                       'marker': None}
        log.debug("Searching for an OpenStack snapshot with the following "
                  "params: %s", search_opts)
        cb_snaps = [
            OpenStackSnapshot(self.provider, snap) for
            snap in self.provider.cinder.volume_snapshots.list(search_opts)
            if snap.name == label]

        return oshelpers.to_server_paged_list(self.provider, cb_snaps)

    def list(self, limit=None, marker=None):
        """
        List all snapshot.
        """
        cb_snaps = [
            OpenStackSnapshot(self.provider, snap) for
            snap in self.provider.cinder.volume_snapshots.list(
                search_opts={'limit': oshelpers.os_result_limit(self.provider,
                                                                limit),
                             'marker': marker})]
        return oshelpers.to_server_paged_list(self.provider, cb_snaps, limit)

    def create(self, label, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        log.debug("Creating a new snapshot of the %s volume.", label)
        OpenStackSnapshot.assert_valid_resource_label(label)

        volume_id = (volume.id if isinstance(volume, OpenStackVolume)
                     else volume)

        os_snap = self.provider.cinder.volume_snapshots.create(
            volume_id, name=label,
            description=description)
        return OpenStackSnapshot(self.provider, os_snap)


class OpenStackBucketService(BaseBucketService):

    def __init__(self, provider):
        super(OpenStackBucketService, self).__init__(provider)

    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        log.debug("Getting OpenStack bucket with the id: %s", bucket_id)
        _, container_list = self.provider.swift.get_account(
            prefix=bucket_id)
        if container_list:
            return OpenStackBucket(self.provider,
                                   next((c for c in container_list
                                         if c['name'] == bucket_id), None))
        else:
            log.debug("Bucket %s was not found.", bucket_id)
            return None

    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        log.debug("Searching for the OpenStack Bucket with the name: %s", name)
        _, container_list = self.provider.swift.get_account(
            limit=oshelpers.os_result_limit(self.provider),
            marker=None)
        cb_buckets = [OpenStackBucket(self.provider, c)
                      for c in container_list
                      if name in c.get("name")]
        return oshelpers.to_server_paged_list(self.provider, cb_buckets)

    def list(self, limit=None, marker=None):
        """
        List all containers.
        """
        _, container_list = self.provider.swift.get_account(
            limit=oshelpers.os_result_limit(self.provider, limit),
            marker=marker)
        cb_buckets = [OpenStackBucket(self.provider, c)
                      for c in container_list]
        return oshelpers.to_server_paged_list(self.provider, cb_buckets, limit)

    def create(self, name, location=None):
        """
        Create a new bucket.
        """
        log.debug("Creating a new OpenStack Bucket with the name: %s", name)
        OpenStackBucket.assert_valid_resource_name(name)
        try:
            self.provider.swift.head_container(name)
            raise DuplicateResourceException(
                'Bucket already exists with name {0}'.format(name))
        except SwiftClientException:
            self.provider.swift.put_container(name)
            return self.get(name)


class OpenStackRegionService(BaseRegionService):

    def __init__(self, provider):
        super(OpenStackRegionService, self).__init__(provider)

    def get(self, region_id):
        log.debug("Getting OpenStack Region with the id: %s", region_id)
        region = (r for r in self if r.id == region_id)
        return next(region, None)

    def list(self, limit=None, marker=None):
        # pylint:disable=protected-access
        if self.provider._keystone_version == 3:
            os_regions = [OpenStackRegion(self.provider, region)
                          for region in self.provider.keystone.regions.list()]
            return ClientPagedResultList(self.provider, os_regions,
                                         limit=limit, marker=marker)
        else:
            # Keystone v3 onwards supports directly listing regions
            # but for v2, this convoluted method is necessary.
            regions = (
                endpoint.get('region') or endpoint.get('region_id')
                for svc in self.provider.keystone.service_catalog.get_data()
                for endpoint in svc.get('endpoints', [])
            )
            regions = set(region for region in regions if region)
            os_regions = [OpenStackRegion(self.provider, region)
                          for region in regions]

            return ClientPagedResultList(self.provider, os_regions,
                                         limit=limit, marker=marker)

    @property
    def current(self):
        nova_region = self.provider.nova.client.region_name
        return self.get(nova_region) if nova_region else None


class OpenStackComputeService(BaseComputeService):

    def __init__(self, provider):
        super(OpenStackComputeService, self).__init__(provider)
        self._vm_type_svc = OpenStackVMTypeService(self.provider)
        self._instance_svc = OpenStackInstanceService(self.provider)
        self._region_svc = OpenStackRegionService(self.provider)
        self._images_svc = OpenStackImageService(self.provider)

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


class OpenStackInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(OpenStackInstanceService, self).__init__(provider)

    def create(self, label, image, vm_type, subnet, zone,
               key_pair=None, vm_firewalls=None, user_data=None,
               launch_config=None,
               **kwargs):
        """Create a new virtual machine instance."""
        OpenStackInstance.assert_valid_resource_label(label)

        image_id = image.id if isinstance(image, MachineImage) else image
        vm_size = vm_type.id if \
            isinstance(vm_type, VMType) else \
            self.provider.compute.vm_types.find(
                name=vm_type)[0].id
        if isinstance(subnet, Subnet):
            subnet_id = subnet.id
            net_id = subnet.network_id
        else:
            subnet_id = subnet
            net_id = (self.provider.networking.subnets
                      .get(subnet_id).network_id
                      if subnet_id else None)
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        key_pair_name = key_pair.name if \
            isinstance(key_pair, KeyPair) else key_pair
        bdm = None
        if launch_config:
            bdm = self._to_block_device_mapping(launch_config)

        # Security groups must be passed in as a list of IDs and attached to a
        # port if a port is being created. Otherwise, the security groups must
        # be passed in as a list of names to the servers.create() call.
        # OpenStack will respect the port's security groups first and then
        # fall-back to the named security groups.
        sg_name_list = []
        nics = None
        if subnet_id:
            log.debug("Creating network port for %s in subnet: %s",
                      label, subnet_id)
            sg_list = []
            if vm_firewalls:
                if isinstance(vm_firewalls, list) and \
                        isinstance(vm_firewalls[0], VMFirewall):
                    sg_list = vm_firewalls
                else:
                    sg_list = (self.provider.security.vm_firewalls
                               .find(label=sg) for sg in vm_firewalls)
                    sg_list = (sg[0] for sg in sg_list if sg)
            sg_id_list = [sg.id for sg in sg_list]
            port_def = {
                "port": {
                    "admin_state_up": True,
                    "name": OpenStackInstance._generate_name_from_label(
                        label, 'cb-port'),
                    "network_id": net_id,
                    "fixed_ips": [{"subnet_id": subnet_id}],
                    "security_groups": sg_id_list
                }
            }
            port_id = self.provider.neutron.create_port(port_def)['port']['id']
            nics = [{'net-id': net_id, 'port-id': port_id}]
        else:
            if vm_firewalls:
                if isinstance(vm_firewalls, list) and \
                        isinstance(vm_firewalls[0], VMFirewall):
                    sg_name_list = [sg.name for sg in vm_firewalls]
                else:
                    sg_list = (self.provider.security.vm_firewalls.get(sg)
                               for sg in vm_firewalls)
                    sg_name_list = (sg[0].name for sg in sg_list if sg)

        log.debug("Launching in subnet %s", subnet_id)
        os_instance = self.provider.nova.servers.create(
            label,
            None if self._has_root_device(launch_config) else image_id,
            vm_size,
            min_count=1,
            max_count=1,
            availability_zone=zone_id,
            key_name=key_pair_name,
            security_groups=sg_name_list,
            userdata=str(user_data) or None,
            block_device_mapping_v2=bdm,
            nics=nics)
        return OpenStackInstance(self.provider, os_instance)

    def _to_block_device_mapping(self, launch_config):
        """
        Extracts block device mapping information
        from a launch config and constructs a BlockDeviceMappingV2
        object.
        """
        bdm = []
        for device in launch_config.block_devices:
            bdm_dict = dict()

            if device.is_volume:
                bdm_dict['destination_type'] = 'volume'

                if device.is_root:
                    bdm_dict['device_name'] = '/dev/sda'
                    bdm_dict['boot_index'] = 0

                if isinstance(device.source, Snapshot):
                    bdm_dict['source_type'] = 'snapshot'
                    bdm_dict['uuid'] = device.source.id
                elif isinstance(device.source, Volume):
                    bdm_dict['source_type'] = 'volume'
                    bdm_dict['uuid'] = device.source.id
                elif isinstance(device.source, MachineImage):
                    bdm_dict['source_type'] = 'image'
                    bdm_dict['uuid'] = device.source.id
                else:
                    bdm_dict['source_type'] = 'blank'

                if device.delete_on_terminate is not None:
                    bdm_dict[
                        'delete_on_termination'] = device.delete_on_terminate

                if device.size:
                    bdm_dict['volume_size'] = device.size
            else:
                bdm_dict['destination_type'] = 'local'
                bdm_dict['source_type'] = 'blank'
                bdm_dict['delete_on_termination'] = True
            bdm.append(bdm_dict)
        return bdm

    def _has_root_device(self, launch_config):
        if not launch_config:
            return False
        for device in launch_config.block_devices:
            if device.is_root:
                return True
        return False

    def create_launch_config(self):
        return BaseLaunchConfig(self.provider)

    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        search_opts = {'name': label}
        cb_insts = [
            OpenStackInstance(self.provider, inst)
            for inst in self.provider.nova.servers.list(
                search_opts=search_opts,
                limit=oshelpers.os_result_limit(self.provider),
                marker=None)]
        return oshelpers.to_server_paged_list(self.provider, cb_insts)

    def list(self, limit=None, marker=None):
        """
        List all instances.
        """
        cb_insts = [
            OpenStackInstance(self.provider, inst)
            for inst in self.provider.nova.servers.list(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)]
        return oshelpers.to_server_paged_list(self.provider, cb_insts, limit)

    def get(self, instance_id):
        """
        Returns an instance given its id.
        """
        try:
            os_instance = self.provider.nova.servers.get(instance_id)
            return OpenStackInstance(self.provider, os_instance)
        except NovaNotFound:
            log.debug("Instance %s was not found.", instance_id)
            return None


class OpenStackNetworkingService(BaseNetworkingService):

    def __init__(self, provider):
        super(OpenStackNetworkingService, self).__init__(provider)
        self._network_service = OpenStackNetworkService(self.provider)
        self._subnet_service = OpenStackSubnetService(self.provider)
        self._router_service = OpenStackRouterService(self.provider)

    @property
    def networks(self):
        return self._network_service

    @property
    def subnets(self):
        return self._subnet_service

    @property
    def routers(self):
        return self._router_service


class OpenStackNetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(OpenStackNetworkService, self).__init__(provider)

    def get(self, network_id):
        log.debug("Getting OpenStack Network with the id: %s", network_id)
        network = (n for n in self if n.id == network_id)
        return next(network, None)

    def list(self, limit=None, marker=None):
        networks = [OpenStackNetwork(self.provider, network)
                    for network in self.provider.neutron.list_networks()
                    .get('networks') if network]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for OpenStack Network with label: %s", label)
        networks = [OpenStackNetwork(self.provider, network)
                    for network in self.provider.neutron.list_networks(
                        name=label)
                    .get('networks') if network]
        return ClientPagedResultList(self.provider, networks)

    def create(self, label, cidr_block):
        log.debug("Creating OpenStack Network with the params: "
                  "[label: %s Cinder Block: %s]", label, cidr_block)
        OpenStackNetwork.assert_valid_resource_label(label)
        net_info = {'name': label or ""}
        network = self.provider.neutron.create_network({'network': net_info})
        cb_net = OpenStackNetwork(self.provider, network.get('network'))
        if label:
            cb_net.label = label
        return cb_net


class OpenStackSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(OpenStackSubnetService, self).__init__(provider)

    def get(self, subnet_id):
        log.debug("Getting OpenStack Subnet with the id: %s", subnet_id)
        subnet = (s for s in self if s.id == subnet_id)
        return next(subnet, None)

    def list(self, network=None, limit=None, marker=None):
        if network:
            network_id = (network.id if isinstance(network, OpenStackNetwork)
                          else network)
            subnets = [subnet for subnet in self if network_id ==
                       subnet.network_id]
        else:
            subnets = [OpenStackSubnet(self.provider, subnet) for subnet in
                       self.provider.neutron.list_subnets().get('subnets', [])]
        return ClientPagedResultList(self.provider, subnets,
                                     limit=limit, marker=marker)

    def create(self, label, network, cidr_block, zone):
        """zone param is ignored."""
        log.debug("Creating OpenStack Subnet with the params: "
                  "[Label: %s Network: %s Cinder Block: %s Zone: -ignored-]",
                  label, network, cidr_block)
        OpenStackSubnet.assert_valid_resource_label(label)
        name = OpenStackSubnet._generate_name_from_label(label, 'cb-subnet')
        network_id = (network.id if isinstance(network, OpenStackNetwork)
                      else network)
        subnet_info = {'name': name, 'network_id': network_id,
                       'cidr': cidr_block, 'ip_version': 4}
        subnet = (self.provider.neutron.create_subnet({'subnet': subnet_info})
                  .get('subnet'))
        cb_subnet = OpenStackSubnet(self.provider, subnet)
        cb_subnet.label = label
        return cb_subnet

    def get_or_create_default(self, zone):
        """
        Subnet zone is not supported by OpenStack and is thus ignored.
        """
        try:
            sn = self.find(label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL)
            if sn:
                return sn[0]
            # No default; create one
            net = self.provider.networking.networks.create(
                label=OpenStackNetwork.CB_DEFAULT_NETWORK_LABEL,
                cidr_block='10.0.0.0/16')
            sn = net.create_subnet(
                label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL,
                cidr_block='10.0.0.0/24')
            router = self.provider.networking.routers.create(
                network=net, label=OpenStackRouter.CB_DEFAULT_ROUTER_LABEL)
            router.attach_subnet(sn)
            gteway = net.gateways.get_or_create_inet_gateway()
            router.attach_gateway(gteway)
            return sn
        except NeutronClientException:
            return None

    def delete(self, subnet):
        log.debug("Deleting subnet: %s", subnet)
        subnet_id = (subnet.id if isinstance(subnet, OpenStackSubnet)
                     else subnet)
        self.provider.neutron.delete_subnet(subnet_id)
        # Adhere to the interface docs
        if subnet_id not in self:
            return True
        return False


class OpenStackRouterService(BaseRouterService):

    def __init__(self, provider):
        super(OpenStackRouterService, self).__init__(provider)

    def get(self, router_id):
        log.debug("Getting OpenStack Router with the id: %s", router_id)
        router = (r for r in self if r.id == router_id)
        return next(router, None)

    def list(self, limit=None, marker=None):
        routers = self.provider.neutron.list_routers().get('routers')
        os_routers = [OpenStackRouter(self.provider, r) for r in routers]
        return ClientPagedResultList(self.provider, os_routers, limit=limit,
                                     marker=marker)

    def find(self, **kwargs):
        obj_list = self
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def create(self, label, network):
        """
        ``network`` is not used by OpenStack.

        However, the API seems to indicate it is a (required) param?!
        https://developer.openstack.org/api-ref/networking/v2/
            ?expanded=delete-router-detail,create-router-detail#create-router
        """
        log.debug("Creating OpenStack Router with the label: %s", label)
        OpenStackRouter.assert_valid_resource_label(label)

        body = {'router': {'name': label}} if label else None
        router = self.provider.neutron.create_router(body)
        return OpenStackRouter(self.provider, router.get('router'))
