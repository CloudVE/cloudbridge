"""
Services implemented by the OpenStack provider.
"""
import fnmatch
import logging
import re

from cinderclient.exceptions import NotFound as CinderNotFound

from cloudbridge.cloud.base.resources import BaseLaunchConfig
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.services import BaseBlockStoreService
from cloudbridge.cloud.base.services import BaseComputeService
from cloudbridge.cloud.base.services import BaseImageService
from cloudbridge.cloud.base.services import BaseInstanceService
from cloudbridge.cloud.base.services import BaseInstanceTypesService
from cloudbridge.cloud.base.services import BaseKeyPairService
from cloudbridge.cloud.base.services import BaseNetworkService
from cloudbridge.cloud.base.services import BaseObjectStoreService
from cloudbridge.cloud.base.services import BaseRegionService
from cloudbridge.cloud.base.services import BaseSecurityGroupService
from cloudbridge.cloud.base.services import BaseSecurityService
from cloudbridge.cloud.base.services import BaseSnapshotService
from cloudbridge.cloud.base.services import BaseSubnetService
from cloudbridge.cloud.base.services import BaseVolumeService
from cloudbridge.cloud.interfaces.resources import InstanceType
from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import MachineImage
from cloudbridge.cloud.interfaces.resources import PlacementZone
from cloudbridge.cloud.interfaces.resources import SecurityGroup
from cloudbridge.cloud.interfaces.resources import Snapshot
from cloudbridge.cloud.interfaces.resources import Subnet
from cloudbridge.cloud.interfaces.resources import Volume
from cloudbridge.cloud.providers.openstack import helpers as oshelpers

from neutronclient.common.exceptions import NeutronClientException

from novaclient.exceptions import NotFound as NovaNotFound

from .resources import OpenStackBucket
from .resources import OpenStackFloatingIP
from .resources import OpenStackInstance
from .resources import OpenStackInstanceType
from .resources import OpenStackKeyPair
from .resources import OpenStackMachineImage
from .resources import OpenStackNetwork
from .resources import OpenStackRegion
from .resources import OpenStackRouter
from .resources import OpenStackSecurityGroup
from .resources import OpenStackSnapshot
from .resources import OpenStackSubnet
from .resources import OpenStackVolume

log = logging.getLogger(__name__)


class OpenStackSecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(OpenStackSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = OpenStackKeyPairService(provider)
        self._security_groups = OpenStackSecurityGroupService(provider)

    @property
    def key_pairs(self):
        """
        Provides access to key pairs for this provider.

        :rtype: ``object`` of :class:`.KeyPairService`
        :return: a KeyPairService object
        """
        return self._key_pairs

    @property
    def security_groups(self):
        """
        Provides access to security groups for this provider.

        :rtype: ``object`` of :class:`.SecurityGroupService`
        :return: a SecurityGroupService object
        """
        return self._security_groups

    def get_or_create_ec2_credentials(self):
        """
        A provider specific method than returns the ec2 credentials for the
        current user, or creates a new pair if one doesn't exist.
        """
        keystone = self.provider.keystone
        if hasattr(keystone, 'ec2'):
            user_creds = [cred for cred in keystone.ec2.list(keystone.user_id)
                          if cred.tenant_id == keystone.tenant_id]
            if user_creds:
                return user_creds[0]
            else:
                return keystone.ec2.create(keystone.user_id,
                                           keystone.tenant_id)

        return None

    def get_ec2_endpoints(self):
        """
        A provider specific method than returns the ec2 endpoints if
        available.
        """
        service_catalog = self.provider.keystone.service_catalog.get_data()
        current_region = self.provider.compute.regions.current.id
        ec2_url = [endpoint.get('publicURL')
                   for svc in service_catalog
                   for endpoint in svc.get('endpoints', [])
                   if endpoint.get('region', None) ==
                   current_region and svc.get('type', None) == 'ec2']
        s3_url = [endpoint.get('publicURL')
                  for svc in service_catalog
                  for endpoint in svc.get('endpoints', [])
                  if endpoint.get('region', None) ==
                  current_region and svc.get('type', None) == 's3']

        return {'ec2_endpoint': ec2_url[0] if ec2_url else None,
                's3_endpoint': s3_url[0] if s3_url else None}


class OpenStackKeyPairService(BaseKeyPairService):

    def __init__(self, provider):
        super(OpenStackKeyPairService, self).__init__(provider)

    def get(self, key_pair_id):
        """
        Returns a KeyPair given its id.
        """
        try:
            return OpenStackKeyPair(
                self.provider, self.provider.nova.keypairs.get(key_pair_id))
        except NovaNotFound:
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
        return ClientPagedResultList(self.provider, results,
                                     limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        """
        Searches for a key pair by a given list of attributes.
        """
        keypairs = self.provider.nova.keypairs.findall(name=name)
        results = [OpenStackKeyPair(self.provider, kp)
                   for kp in keypairs]
        return ClientPagedResultList(self.provider, results,
                                     limit=limit, marker=marker)

    def create(self, name):
        """
        Create a new key pair or raise an exception if one already exists.

        :type name: str
        :param name: The name of the key pair to be created.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  A key pair instance or ``None`` if one was not be created.
        """
        kp = self.provider.nova.keypairs.create(name)
        if kp:
            return OpenStackKeyPair(self.provider, kp)
        return None


class OpenStackSecurityGroupService(BaseSecurityGroupService):

    def __init__(self, provider):
        super(OpenStackSecurityGroupService, self).__init__(provider)

    def get(self, sg_id):
        """
        Returns a SecurityGroup given its id.
        """
        try:
            return OpenStackSecurityGroup(
                self.provider, self.provider.nova.security_groups.get(sg_id))
        except NovaNotFound:
            return None

    def list(self, limit=None, marker=None):
        """
        List all security groups associated with this account.

        :rtype: ``list`` of :class:`.SecurityGroup`
        :return:  list of SecurityGroup objects
        """

        sgs = [OpenStackSecurityGroup(self.provider, sg)
               for sg in self.provider.nova.security_groups.list()]

        return ClientPagedResultList(self.provider, sgs,
                                     limit=limit, marker=marker)

    def create(self, name, description, network_id):
        """
        Create a new security group under the current account.

        :type name: str
        :param name: The name of the new security group.

        :type description: str
        :param description: The description of the new security group.

        :type  network_id: ``None``
        :param network_id: Not applicable for OpenStack (yet) so any value is
                           ignored.

        :rtype: ``object`` of :class:`.SecurityGroup`
        :return: a SecurityGroup object
        """
        sg = self.provider.nova.security_groups.create(name, description)
        if sg:
            return OpenStackSecurityGroup(self.provider, sg)
        return None

    def find(self, name, limit=None, marker=None):
        """
        Get all security groups associated with your account.
        """
        sgs = self.provider.nova.security_groups.findall(name=name)
        results = [OpenStackSecurityGroup(self.provider, sg)
                   for sg in sgs]
        return ClientPagedResultList(self.provider, results,
                                     limit=limit, marker=marker)

    def delete(self, group_id):
        """
        Delete an existing SecurityGroup.

        :type group_id: str
        :param group_id: The security group ID to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the security group does not exist, ``False``
                  otherwise. Note that this implies that the group may not have
                  been deleted by this method but instead has not existed in
                  the first place.
        """
        sg = self.get(group_id)
        if sg:
            sg.delete()
        return True


class OpenStackImageService(BaseImageService):

    def __init__(self, provider):
        super(OpenStackImageService, self).__init__(provider)

    def get(self, image_id):
        """
        Returns an Image given its id
        """
        try:
            return OpenStackMachineImage(
                self.provider, self.provider.nova.images.get(image_id))
        except NovaNotFound:
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for an image by a given list of attributes
        """
        regex = fnmatch.translate(name)
        cb_images = [
            OpenStackMachineImage(self.provider, img)
            for img in self
            if img.name and re.search(regex, img.name)]

        return oshelpers.to_server_paged_list(self.provider, cb_images, limit)

    def list(self, limit=None, marker=None):
        """
        List all images.
        """
        if marker is None:
            os_images = self.provider.nova.images.list(
                limit=oshelpers.os_result_limit(self.provider, limit))
        else:
            os_images = self.provider.nova.images.list(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)

        cb_images = [
            OpenStackMachineImage(self.provider, img)
            for img in os_images]
        return oshelpers.to_server_paged_list(self.provider, cb_images, limit)


class OpenStackInstanceTypesService(BaseInstanceTypesService):

    def __init__(self, provider):
        super(OpenStackInstanceTypesService, self).__init__(provider)

    def list(self, limit=None, marker=None):
        cb_itypes = [
            OpenStackInstanceType(self.provider, obj)
            for obj in self.provider.nova.flavors.list(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)]

        return oshelpers.to_server_paged_list(self.provider, cb_itypes, limit)


class OpenStackBlockStoreService(BaseBlockStoreService):

    def __init__(self, provider):
        super(OpenStackBlockStoreService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = OpenStackVolumeService(self.provider)
        self._snapshot_svc = OpenStackSnapshotService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc


class OpenStackVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(OpenStackVolumeService, self).__init__(provider)

    def get(self, volume_id):
        """
        Returns a volume given its id.
        """
        try:
            return OpenStackVolume(
                self.provider, self.provider.cinder.volumes.get(volume_id))
        except CinderNotFound:
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a volume by a given list of attributes.
        """
        search_opts = {'name': name}
        cb_vols = [
            OpenStackVolume(self.provider, vol)
            for vol in self.provider.cinder.volumes.list(
                search_opts=search_opts,
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)]

        return oshelpers.to_server_paged_list(self.provider, cb_vols, limit)

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

    def create(self, name, size, zone, snapshot=None, description=None):
        """
        Creates a new volume.
        """
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.id if isinstance(
            snapshot, OpenStackSnapshot) and snapshot else snapshot

        os_vol = self.provider.cinder.volumes.create(
            size, name=name, description=description,
            availability_zone=zone_id, snapshot_id=snapshot_id)
        return OpenStackVolume(self.provider, os_vol)


class OpenStackSnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(OpenStackSnapshotService, self).__init__(provider)

    def get(self, snapshot_id):
        """
        Returns a snapshot given its id.
        """
        try:
            return OpenStackSnapshot(
                self.provider,
                self.provider.cinder.volume_snapshots.get(snapshot_id))
        except CinderNotFound:
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a volume by a given list of attributes.
        """
        search_opts = {'name': name,  # TODO: Cinder is ignoring name
                       'limit': oshelpers.os_result_limit(self.provider,
                                                          limit),
                       'marker': marker}
        cb_snaps = [
            OpenStackSnapshot(self.provider, snap) for
            snap in self.provider.cinder.volume_snapshots.list(search_opts)
            if snap.name == name]

        return oshelpers.to_server_paged_list(self.provider, cb_snaps, limit)

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

    def create(self, name, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        volume_id = (volume.id if isinstance(volume, OpenStackVolume)
                     else volume)

        os_snap = self.provider.cinder.volume_snapshots.create(
            volume_id, name=name,
            description=description)
        return OpenStackSnapshot(self.provider, os_snap)


class OpenStackObjectStoreService(BaseObjectStoreService):

    def __init__(self, provider):
        super(OpenStackObjectStoreService, self).__init__(provider)

    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        _, container_list = self.provider.swift.get_account(
            prefix=bucket_id)
        if container_list:
            return OpenStackBucket(self.provider,
                                   next((c for c in container_list
                                         if c['name'] == bucket_id), None))
        else:
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a bucket by a given list of attributes.
        """
        _, container_list = self.provider.swift.get_account(
            limit=oshelpers.os_result_limit(self.provider, limit),
            marker=marker)
        cb_buckets = [OpenStackBucket(self.provider, c)
                      for c in container_list
                      if name in c.get("name")]
        return oshelpers.to_server_paged_list(self.provider, cb_buckets, limit)

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
        self.provider.swift.put_container(name)
        return self.get(name)


class OpenStackRegionService(BaseRegionService):

    def __init__(self, provider):
        super(OpenStackRegionService, self).__init__(provider)

    def get(self, region_id):
        region = (r for r in self.list() if r.id == region_id)
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
        self._instance_type_svc = OpenStackInstanceTypesService(self.provider)
        self._instance_svc = OpenStackInstanceService(self.provider)
        self._region_svc = OpenStackRegionService(self.provider)
        self._images_svc = OpenStackImageService(self.provider)

    @property
    def images(self):
        return self._images_svc

    @property
    def instance_types(self):
        return self._instance_type_svc

    @property
    def instances(self):
        return self._instance_svc

    @property
    def regions(self):
        return self._region_svc


class OpenStackInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(OpenStackInstanceService, self).__init__(provider)

    def create(self, name, image, instance_type, subnet, zone=None,
               key_pair=None, security_groups=None, user_data=None,
               launch_config=None,
               **kwargs):
        """Create a new virtual machine instance."""
        image_id = image.id if isinstance(image, MachineImage) else image
        instance_size = instance_type.id if \
            isinstance(instance_type, InstanceType) else \
            self.provider.compute.instance_types.find(
                name=instance_type)[0].id
        network_id = subnet.network_id if isinstance(subnet, Subnet) else None
        if not network_id and subnet:
            network_id = (self.provider.network.subnets.get(subnet).network_id
                          if isinstance(subnet, str) else None)
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        key_pair_name = key_pair.name if \
            isinstance(key_pair, KeyPair) else key_pair
        if security_groups:
            if isinstance(security_groups, list) and \
                    isinstance(security_groups[0], SecurityGroup):
                security_groups_list = [sg.name for sg in security_groups]
            else:
                security_groups_list = security_groups
        else:
            security_groups_list = None
        bdm = None
        if launch_config:
            bdm = self._to_block_device_mapping(launch_config)

        log.debug("Launching in network %s" % network_id)
        os_instance = self.provider.nova.servers.create(
            name,
            None if self._has_root_device(launch_config) else image_id,
            instance_size,
            min_count=1,
            max_count=1,
            availability_zone=zone_id,
            key_name=key_pair_name,
            security_groups=security_groups_list,
            userdata=user_data,
            block_device_mapping_v2=bdm,
            nics=[{'net-id': network_id}] if network_id else None)
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

    def find(self, name, limit=None, marker=None):
        """
        Searches for an instance by a given list of attributes.
        """
        search_opts = {'name': name}
        cb_insts = [
            OpenStackInstance(self.provider, inst)
            for inst in self.provider.nova.servers.list(
                search_opts=search_opts,
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)]
        return oshelpers.to_server_paged_list(self.provider, cb_insts, limit)

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
            return None


class OpenStackNetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(OpenStackNetworkService, self).__init__(provider)
        self._subnet_svc = OpenStackSubnetService(self.provider)

    def get(self, network_id):
        network = (n for n in self.list() if n.id == network_id)
        return next(network, None)

    def list(self, limit=None, marker=None):
        networks = [OpenStackNetwork(self.provider, network)
                    for network in self.provider.neutron.list_networks()
                    .get('networks', [])]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    def create(self, name=''):
        net_info = {'name': name}
        network = self.provider.neutron.create_network({'network': net_info})
        return OpenStackNetwork(self.provider, network.get('network'))

    @property
    def subnets(self):
        return self._subnet_svc

    def floating_ips(self, network_id=None):
        if network_id:
            al = self.provider.neutron.list_floatingips(
                floating_network_id=network_id)['floatingips']
        else:
            al = self.provider.neutron.list_floatingips()['floatingips']
        return [OpenStackFloatingIP(self.provider, a) for a in al]

    def create_floating_ip(self):
        # OpenStack requires a floating IP to be associated with a pool,
        # so just choose the first one available...
        ip_pool_name = self.provider.nova.floating_ip_pools.list()[0].name
        ip = self.provider.nova.floating_ips.create(ip_pool_name)
        # Nova returns a different object than Neutron so fetch the Neutron one
        ip = self.provider.neutron.list_floatingips(id=ip.id)['floatingips'][0]
        return OpenStackFloatingIP(self.provider, ip)

    def routers(self):
        routers = self.provider.neutron.list_routers().get('routers')
        return [OpenStackRouter(self.provider, r) for r in routers]

    def create_router(self, name=None):
        router = self.provider.neutron.create_router(
            {'router': {'name': name}})
        return OpenStackRouter(self.provider, router.get('router'))


class OpenStackSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(OpenStackSubnetService, self).__init__(provider)

    def get(self, subnet_id):
        subnet = (s for s in self.list() if s.id == subnet_id)
        return next(subnet, None)

    def list(self, network=None):
        if network:
            network_id = (network.id if isinstance(network, OpenStackNetwork)
                          else network)
            subnets = self.list()
            return [subnet for subnet in subnets if network_id in
                    subnet.network_id]
        subnets = self.provider.neutron.list_subnets().get('subnets', [])
        return [OpenStackSubnet(self.provider, subnet) for subnet in subnets]

    def create(self, network, cidr_block, name='', zone=None):
        """zone param is ignored."""
        network_id = (network.id if isinstance(network, OpenStackNetwork)
                      else network)
        subnet_info = {'name': name, 'network_id': network_id,
                       'cidr': cidr_block, 'ip_version': 4}
        subnet = (self.provider.neutron.create_subnet({'subnet': subnet_info})
                  .get('subnet'))
        return OpenStackSubnet(self.provider, subnet)

    def get_or_create_default(self, zone=None):
        """
        Subnet zone is not supported by OpenStack and is thus ignored.
        """
        try:
            for sn in self.list():
                if sn.name == OpenStackSubnet.CB_DEFAULT_SUBNET_NAME:
                    return sn
            # No default; create one
            net = self.provider.network.create(
                OpenStackNetwork.CB_DEFAULT_NETWORK_NAME)
            sn = net.create_subnet(cidr_block='10.0.0.0/24',
                                   name=OpenStackSubnet.CB_DEFAULT_SUBNET_NAME)
            router = self.provider.network.create_router(
                OpenStackRouter.CB_DEFAULT_ROUTER_NAME)
            for n in self.provider.network.list():
                if n.external:
                    external_net = n
                    break
            router.attach_network(external_net.id)
            router.add_route(sn.id)
            return sn
        except NeutronClientException:
            return None

    def delete(self, subnet):
        subnet_id = (subnet.id if isinstance(subnet, OpenStackSubnet)
                     else subnet)
        self.provider.neutron.delete_subnet(subnet_id)
        # Adhere to the interface docs
        if subnet_id not in self.list():
            return True
        return False
