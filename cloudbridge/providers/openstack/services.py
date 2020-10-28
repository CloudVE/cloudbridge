"""
Services implemented by the OpenStack provider.
"""
import logging

from neutronclient.common.exceptions import NeutronClientException
from neutronclient.common.exceptions import PortNotFoundClient

from novaclient.exceptions import NotFound as NovaNotFound

from openstack.exceptions import BadRequestException
from openstack.exceptions import HttpException
from openstack.exceptions import NotFoundException
from openstack.exceptions import ResourceNotFound

from swiftclient import ClientException as SwiftClientException

import cloudbridge.base.helpers as cb_helpers
from cloudbridge.base.middleware import dispatch
from cloudbridge.base.resources import BaseLaunchConfig
from cloudbridge.base.resources import ClientPagedResultList
from cloudbridge.base.services import BaseBucketObjectService
from cloudbridge.base.services import BaseBucketService
from cloudbridge.base.services import BaseComputeService
from cloudbridge.base.services import BaseDnsRecordService
from cloudbridge.base.services import BaseDnsService
from cloudbridge.base.services import BaseDnsZoneService
from cloudbridge.base.services import BaseFloatingIPService
from cloudbridge.base.services import BaseGatewayService
from cloudbridge.base.services import BaseImageService
from cloudbridge.base.services import BaseInstanceService
from cloudbridge.base.services import BaseKeyPairService
from cloudbridge.base.services import BaseNetworkService
from cloudbridge.base.services import BaseNetworkingService
from cloudbridge.base.services import BaseRegionService
from cloudbridge.base.services import BaseRouterService
from cloudbridge.base.services import BaseSecurityService
from cloudbridge.base.services import BaseSnapshotService
from cloudbridge.base.services import BaseStorageService
from cloudbridge.base.services import BaseSubnetService
from cloudbridge.base.services import BaseVMFirewallRuleService
from cloudbridge.base.services import BaseVMFirewallService
from cloudbridge.base.services import BaseVMTypeService
from cloudbridge.base.services import BaseVolumeService
from cloudbridge.interfaces.exceptions \
    import CloudBridgeBaseException
from cloudbridge.interfaces.exceptions \
    import DuplicateResourceException
from cloudbridge.interfaces.exceptions import InvalidParamException
from cloudbridge.interfaces.exceptions import InvalidValueException
from cloudbridge.interfaces.resources import KeyPair
from cloudbridge.interfaces.resources import MachineImage
from cloudbridge.interfaces.resources import Network
from cloudbridge.interfaces.resources import Snapshot
from cloudbridge.interfaces.resources import Subnet
from cloudbridge.interfaces.resources import TrafficDirection
from cloudbridge.interfaces.resources import VMFirewall
from cloudbridge.interfaces.resources import VMType
from cloudbridge.interfaces.resources import Volume

from . import helpers as oshelpers
from .resources import OpenStackBucket
from .resources import OpenStackBucketObject
from .resources import OpenStackDnsRecord
from .resources import OpenStackDnsZone
from .resources import OpenStackFloatingIP
from .resources import OpenStackInstance
from .resources import OpenStackInternetGateway
from .resources import OpenStackKeyPair
from .resources import OpenStackMachineImage
from .resources import OpenStackNetwork
from .resources import OpenStackRegion
from .resources import OpenStackRouter
from .resources import OpenStackSnapshot
from .resources import OpenStackSubnet
from .resources import OpenStackVMFirewall
from .resources import OpenStackVMFirewallRule
from .resources import OpenStackVMType
from .resources import OpenStackVolume

log = logging.getLogger(__name__)


class OpenStackSecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(OpenStackSecurityService, self).__init__(provider)

        # pylint:disable=protected-access
        self.service_zone_name = self.provider._get_config_value(
            'os_security_zone_name', cb_helpers.get_env(
                'OS_SECURITY_ZONE_NAME', self.provider.zone_name))
        # Initialize provider services
        self._key_pairs = OpenStackKeyPairService(provider)
        self._vm_firewalls = OpenStackVMFirewallService(provider)
        self._vm_firewall_rule_svc = OpenStackVMFirewallRuleService(provider)

    @property
    def key_pairs(self):
        return self._key_pairs

    @property
    def vm_firewalls(self):
        return self._vm_firewalls

    @property
    def _vm_firewall_rules(self):
        return self._vm_firewall_rule_svc

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

    @dispatch(event="provider.security.key_pairs.get",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
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

    @dispatch(event="provider.security.key_pairs.list",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
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

    @dispatch(event="provider.security.key_pairs.find",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'name'))

        keypairs = self.provider.nova.keypairs.findall(name=name)
        results = [OpenStackKeyPair(self.provider, kp)
                   for kp in keypairs]
        log.debug("Searching for %s in: %s", name, keypairs)
        return ClientPagedResultList(self.provider, results)

    @dispatch(event="provider.security.key_pairs.create",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def create(self, name, public_key_material=None):
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

    @dispatch(event="provider.security.key_pairs.delete",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def delete(self, key_pair):
        keypair = (key_pair if isinstance(key_pair, OpenStackKeyPair)
                   else self.get(key_pair))
        if keypair:
            # pylint:disable=protected-access
            keypair._key_pair.delete()


class OpenStackVMFirewallService(BaseVMFirewallService):

    def __init__(self, provider):
        super(OpenStackVMFirewallService, self).__init__(provider)

    @dispatch(event="provider.security.vm_firewalls.get",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_firewall_id):
        try:
            return OpenStackVMFirewall(
                self.provider,
                self.provider.os_conn.network
                    .get_security_group(vm_firewall_id))
        except (ResourceNotFound, NotFoundException):
            log.debug("Firewall %s not found.", vm_firewall_id)
            return None

    @dispatch(event="provider.security.vm_firewalls.list",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        firewalls = [
            OpenStackVMFirewall(self.provider, fw)
            for fw in self.provider.os_conn.network.security_groups()]

        return ClientPagedResultList(self.provider, firewalls,
                                     limit=limit, marker=marker)

    @cb_helpers.deprecated_alias(network_id='network')
    @dispatch(event="provider.security.vm_firewalls.create",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network, description=None):
        OpenStackVMFirewall.assert_valid_resource_label(label)
        net_id = network.id if isinstance(network, Network) else network
        # We generally simulate a network being associated with a firewall
        # by storing the supplied value in the firewall description field that
        # is not modifiable after creation; however, because of some networking
        # specificity in Nectar, we must also allow an empty network id value.
        if not net_id:
            net_id = ""
        if not description:
            description = ""
        description += " [{}{}]".format(OpenStackVMFirewall._network_id_tag,
                                        net_id)
        sg = self.provider.os_conn.network.create_security_group(
            name=label, description=description)
        if sg:
            return OpenStackVMFirewall(self.provider, sg)
        return None

    @dispatch(event="provider.security.vm_firewalls.delete",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def delete(self, vm_firewall):
        fw = (vm_firewall if isinstance(vm_firewall, OpenStackVMFirewall)
              else self.get(vm_firewall))
        if fw:
            # pylint:disable=protected-access
            fw._vm_firewall.delete(self.provider.os_conn.network)


class OpenStackVMFirewallRuleService(BaseVMFirewallRuleService):

    def __init__(self, provider):
        super(OpenStackVMFirewallRuleService, self).__init__(provider)

    @dispatch(event="provider.security.vm_firewall_rules.list",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def list(self, firewall, limit=None, marker=None):
        # pylint:disable=protected-access
        rules = [OpenStackVMFirewallRule(firewall, r)
                 for r in firewall._vm_firewall.security_group_rules]
        return ClientPagedResultList(self.provider, rules,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.security.vm_firewall_rules.create",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def create(self, firewall, direction, protocol=None, from_port=None,
               to_port=None, cidr=None, src_dest_fw=None):
        src_dest_fw_id = (src_dest_fw.id if isinstance(src_dest_fw,
                                                       OpenStackVMFirewall)
                          else src_dest_fw)

        try:
            if direction == TrafficDirection.INBOUND:
                os_direction = 'ingress'
            elif direction == TrafficDirection.OUTBOUND:
                os_direction = 'egress'
            else:
                raise InvalidValueException("direction", direction)
            # pylint:disable=protected-access
            rule = self.provider.os_conn.network.create_security_group_rule(
                security_group_id=firewall.id,
                direction=os_direction,
                port_range_max=to_port,
                port_range_min=from_port,
                protocol=protocol,
                remote_ip_prefix=cidr,
                remote_group_id=src_dest_fw_id)
            firewall.refresh()
            return OpenStackVMFirewallRule(firewall, rule.to_dict())
        except HttpException as e:
            firewall.refresh()
            # 409=Conflict, raised for duplicate rule
            if e.status_code == 409:
                existing = self.find(firewall, direction=direction,
                                     protocol=protocol, from_port=from_port,
                                     to_port=to_port, cidr=cidr,
                                     src_dest_fw_id=src_dest_fw_id)
                return existing[0]
            else:
                raise e

    @dispatch(event="provider.security.vm_firewall_rules.delete",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def delete(self, firewall, rule):
        rule_id = (rule.id if isinstance(rule, OpenStackVMFirewallRule)
                   else rule)
        self.provider.os_conn.network.delete_security_group_rule(rule_id)
        firewall.refresh()


class OpenStackStorageService(BaseStorageService):

    def __init__(self, provider):
        super(OpenStackStorageService, self).__init__(provider)

        # pylint:disable=protected-access
        self.service_zone_name = self.provider._get_config_value(
            'os_storage_zone_name', cb_helpers.get_env(
                'OS_STORAGE_ZONE_NAME', self.provider.zone_name))
        # Initialize provider services
        self._volume_svc = OpenStackVolumeService(self.provider)
        self._snapshot_svc = OpenStackSnapshotService(self.provider)
        self._bucket_svc = OpenStackBucketService(self.provider)
        self._bucket_obj_svc = OpenStackBucketObjectService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc

    @property
    def buckets(self):
        return self._bucket_svc

    @property
    def _bucket_objects(self):
        return self._bucket_obj_svc


class OpenStackVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(OpenStackVolumeService, self).__init__(provider)

    @dispatch(event="provider.storage.volumes.get",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def get(self, volume_id):
        try:
            os_vol = self.provider.os_conn.block_storage.get_volume(volume_id)
        except (NotFoundException, ResourceNotFound):
            log.debug("Volume %s was not found.", volume_id)
            return None
        if os_vol.availability_zone != self.provider.service_zone_name(self):
            log.debug("Volume %s was found in availability zone '%s' while the"
                      " OpenStack provider is in zone '%s'",
                      volume_id,
                      os_vol.availability_zone,
                      self.provider.service_zone_name(self))
            return None
        else:
            return OpenStackVolume(self.provider, os_vol)

    @dispatch(event="provider.storage.volumes.find",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for an OpenStack Volume with the label %s", label)
        cb_vols = [
            OpenStackVolume(self.provider, vol)
            for vol in self.provider.os_conn.block_storage.volumes(
                name=label,
                limit=oshelpers.os_result_limit(self.provider),
                marker=None)
            if vol.availability_zone == self.provider.service_zone_name(self)]
        return oshelpers.to_server_paged_list(self.provider, cb_vols)

    @dispatch(event="provider.storage.volumes.list",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        cb_vols = [
            OpenStackVolume(self.provider, vol)
            for vol in self.provider.os_conn.block_storage.volumes(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)
            if vol.availability_zone == self.provider.service_zone_name(self)]
        return oshelpers.to_server_paged_list(self.provider, cb_vols, limit)

    @dispatch(event="provider.storage.volumes.create",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def create(self, label, size, snapshot=None, description=None):
        OpenStackVolume.assert_valid_resource_label(label)
        zone_name = self.provider.service_zone_name(self)
        snapshot_id = snapshot.id if isinstance(
            snapshot, OpenStackSnapshot) and snapshot else snapshot

        os_vol = self.provider.os_conn.block_storage.create_volume(
            size=size, name=label, description=description,
            availability_zone=zone_name, snapshot_id=snapshot_id)
        return OpenStackVolume(self.provider, os_vol)

    @dispatch(event="provider.storage.volumes.delete",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def delete(self, volume):
        vol = (volume if isinstance(volume, OpenStackVolume)
               else self.get(volume))
        if vol:
            # pylint:disable=protected-access
            self.provider.os_conn.block_storage.delete_volume(vol._volume)


class OpenStackSnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(OpenStackSnapshotService, self).__init__(provider)

    @dispatch(event="provider.storage.snapshots.get",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def get(self, snapshot_id):
        try:
            return OpenStackSnapshot(
                self.provider,
                self.provider.os_conn.block_storage.get_snapshot(snapshot_id))
        except (NotFoundException, ResourceNotFound):
            log.debug("Snapshot %s was not found.", snapshot_id)
            return None

    @dispatch(event="provider.storage.snapshots.find",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        search_opts = {'name': label,  # TODO: Cinder is ignoring name
                       'limit': oshelpers.os_result_limit(self.provider),
                       'marker': None}
        log.debug("Searching for an OpenStack snapshot with the following "
                  "params: %s", search_opts)
        cb_snaps = [
            OpenStackSnapshot(self.provider, snap) for
            snap in self.provider.os_conn.block_storage.snapshots(
                **search_opts)
            if snap.name == label]

        return oshelpers.to_server_paged_list(self.provider, cb_snaps)

    @dispatch(event="provider.storage.snapshots.list",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        cb_snaps = [
            OpenStackSnapshot(self.provider, snap)
            for snap in self.provider.os_conn.block_storage.snapshots(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)
        ]
        return oshelpers.to_server_paged_list(self.provider, cb_snaps, limit)

    @dispatch(event="provider.storage.snapshots.create",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def create(self, label, volume, description=None):
        OpenStackSnapshot.assert_valid_resource_label(label)
        volume_id = (volume.id if isinstance(volume, OpenStackVolume)
                     else volume)

        os_snap = self.provider.os_conn.block_storage.create_snapshot(
            volume_id=volume_id, name=label,
            description=description)
        return OpenStackSnapshot(self.provider, os_snap)

    @dispatch(event="provider.storage.snapshots.delete",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def delete(self, snapshot):
        s = (snapshot if isinstance(snapshot, OpenStackSnapshot) else
             self.get(snapshot))
        if s:
            # pylint:disable=protected-access
            self.provider.os_conn.block_storage.delete_snapshot(s._snapshot)


class OpenStackBucketService(BaseBucketService):

    def __init__(self, provider):
        super(OpenStackBucketService, self).__init__(provider)

    @dispatch(event="provider.storage.buckets.get",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
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
            log.debug("Bucket %s was not found.", bucket_id)
            return None

    @dispatch(event="provider.storage.buckets.find",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'name'))
        _, container_list = self.provider.swift.get_account()
        cb_buckets = [OpenStackBucket(self.provider, c)
                      for c in container_list
                      if name in c.get("name")]
        return oshelpers.to_server_paged_list(self.provider, cb_buckets)

    @dispatch(event="provider.storage.buckets.list",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        _, container_list = self.provider.swift.get_account(
            limit=oshelpers.os_result_limit(self.provider, limit),
            marker=marker)
        cb_buckets = [OpenStackBucket(self.provider, c)
                      for c in container_list]
        return oshelpers.to_server_paged_list(self.provider, cb_buckets, limit)

    @dispatch(event="provider.storage.buckets.create",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def create(self, name, location=None):
        OpenStackBucket.assert_valid_resource_name(name)
        location = location or self.provider.region_name
        try:
            self.provider.swift.head_container(name)
            raise DuplicateResourceException(
                'Bucket already exists with name {0}'.format(name))
        except SwiftClientException:
            self.provider.swift.put_container(name)
            return self.get(name)

    @dispatch(event="provider.storage.buckets.delete",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def delete(self, bucket):
        b_id = bucket.id if isinstance(bucket, OpenStackBucket) else bucket
        self.provider.swift.delete_container(b_id)


class OpenStackBucketObjectService(BaseBucketObjectService):

    def __init__(self, provider):
        super(OpenStackBucketObjectService, self).__init__(provider)

    def get(self, bucket, name):
        """
        Retrieve a given object from this bucket.
        """
        # Swift always returns a reference for the container first,
        # followed by a list containing references to objects.
        _, object_list = self.provider.swift.get_container(
            bucket.name, prefix=name)
        # Loop through list of objects looking for an exact name vs. a prefix
        for obj in object_list:
            if obj.get('name') == name:
                return OpenStackBucketObject(self.provider,
                                             bucket,
                                             obj)
        return None

    def list(self, bucket, limit=None, marker=None, prefix=None):
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        _, object_list = self.provider.swift.get_container(
            bucket.name,
            limit=oshelpers.os_result_limit(self.provider, limit),
            marker=marker, prefix=prefix)
        cb_objects = [OpenStackBucketObject(
            self.provider, bucket, obj) for obj in object_list]

        return oshelpers.to_server_paged_list(
            self.provider,
            cb_objects,
            limit)

    def find(self, bucket, **kwargs):
        _, obj_list = self.provider.swift.get_container(bucket.name)
        cb_objs = [OpenStackBucketObject(self.provider, bucket, obj)
                   for obj in obj_list]
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, cb_objs)
        return ClientPagedResultList(self.provider, list(matches))

    def create(self, bucket, object_name):
        self.provider.swift.put_object(bucket.name, object_name, None)
        return self.get(bucket, object_name)


class OpenStackComputeService(BaseComputeService):

    def __init__(self, provider):
        super(OpenStackComputeService, self).__init__(provider)
        self._vm_type_svc = OpenStackVMTypeService(self.provider)
        self._instance_svc = OpenStackInstanceService(self.provider)
        self._region_svc = OpenStackRegionService(self.provider)
        self._images_svc = OpenStackImageService(self.provider)
        # Region service must be defined before invoking the following
        # pylint:disable=protected-access
        self.service_zone_name = self.provider._get_config_value(
            'os_compute_zone_name',
            cb_helpers.get_env(
                'OS_COMPUTE_ZONE_NAME',
                self.provider._zone_name or
                self.regions.current.default_zone.name))

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
        filters = ['label']
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


class OpenStackInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(OpenStackInstanceService, self).__init__(provider)

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

    @dispatch(event="provider.compute.instances.create",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def create(self, label, image, vm_type, subnet,
               key_pair=None, vm_firewalls=None, user_data=None,
               launch_config=None, **kwargs):
        OpenStackInstance.assert_valid_resource_label(label)
        image_id = image.id if isinstance(image, MachineImage) else image
        if isinstance(vm_type, VMType):
            vm_size = vm_type.id
        else:
            vm_type_obj = self.provider.compute.vm_types.find(name=vm_type)
            if not vm_type_obj:
                raise CloudBridgeBaseException(
                    "Could not find vm type with name {0}".format(vm_type))
            vm_size = vm_type_obj[0].id
        if isinstance(subnet, Subnet):
            subnet_id = subnet.id
            net_id = subnet.network_id
        else:
            subnet_id = subnet
            net_id = (self.provider.networking.subnets
                      .get(subnet_id).network_id
                      if subnet_id else None)
        zone_name = self.provider.service_zone_name(self)
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
            availability_zone=zone_name,
            key_name=key_pair_name,
            security_groups=sg_name_list,
            userdata=str(user_data) or None,
            block_device_mapping_v2=bdm,
            nics=nics)
        return OpenStackInstance(self.provider, os_instance)

    @dispatch(event="provider.compute.instances.find",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        search_opts = {'name': label,
                       'availability_zone': self.provider
                                                .service_zone_name(self)}
        cb_insts = [
            OpenStackInstance(self.provider, inst)
            for inst in self.provider.nova.servers.list(
                search_opts=search_opts,
                limit=oshelpers.os_result_limit(self.provider),
                marker=None)]
        return oshelpers.to_server_paged_list(self.provider, cb_insts)

    @dispatch(event="provider.compute.instances.list",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        """
        List all instances.
        """
        search_opts = {'availability_zone': self.provider
                                                .service_zone_name(self)}
        cb_insts = [
            OpenStackInstance(self.provider, inst)
            for inst in self.provider.nova.servers.list(
                search_opts=search_opts,
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)]
        return oshelpers.to_server_paged_list(self.provider, cb_insts, limit)

    @dispatch(event="provider.compute.instances.get",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def get(self, instance_id):
        """
        Returns an instance given its id.
        """
        try:
            os_instance = self.provider.nova.servers.get(instance_id)
        except NovaNotFound:
            log.debug("Instance %s was not found.", instance_id)
            return None
        if (getattr(os_instance,
                    'OS-EXT-AZ:availability_zone', "")
                != self.provider.service_zone_name(self)):
            log.debug("Instance %s was found in availability zone '%s' while "
                      "the OpenStack provider is in zone '%s'",
                      instance_id,
                      getattr(os_instance, 'OS-EXT-AZ:availability_zone', ""),
                      self.provider.service_zone_name(self))
            return None
        return OpenStackInstance(self.provider, os_instance)

    @dispatch(event="provider.compute.instances.delete",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def delete(self, instance):
        ins = (instance if isinstance(instance, OpenStackInstance) else
               self.get(instance))
        if ins:
            # pylint:disable=protected-access
            os_instance = ins._os_instance
            # delete the port we created when launching
            # Assumption: it's the first interface in the list
            iface_list = os_instance.interface_list()
            if iface_list:
                with cb_helpers.cleanup_action(
                        lambda: self.provider.neutron.delete_port(
                            iface_list[0].port_id)):
                    # Ignore errors if port can't be deleted
                    pass
            os_instance.delete()


class OpenStackVMTypeService(BaseVMTypeService):

    def __init__(self, provider):
        super(OpenStackVMTypeService, self).__init__(provider)

    @dispatch(event="provider.compute.vm_types.list",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        cb_itypes = [
            OpenStackVMType(self.provider, obj)
            for obj in self.provider.nova.flavors.list(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)]

        return oshelpers.to_server_paged_list(self.provider, cb_itypes, limit)


class OpenStackRegionService(BaseRegionService):

    def __init__(self, provider):
        super(OpenStackRegionService, self).__init__(provider)

    @dispatch(event="provider.compute.regions.get",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def get(self, region_id):
        log.debug("Getting OpenStack Region with the id: %s", region_id)
        region = (r for r in self if r.id == region_id)
        return next(region, None)

    @dispatch(event="provider.compute.regions.list",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
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


class OpenStackNetworkingService(BaseNetworkingService):

    def __init__(self, provider):
        super(OpenStackNetworkingService, self).__init__(provider)
        # pylint:disable=protected-access
        self.service_zone_name = self.provider._get_config_value(
            'os_networking_zone_name', cb_helpers.get_env(
                'OS_NETWORKING_ZONE_NAME', self.provider.zone_name))
        self._network_service = OpenStackNetworkService(self.provider)
        self._subnet_service = OpenStackSubnetService(self.provider)
        self._router_service = OpenStackRouterService(self.provider)
        self._gateway_service = OpenStackGatewayService(self.provider)
        self._floating_ip_service = OpenStackFloatingIPService(self.provider)

    @property
    def networks(self):
        return self._network_service

    @property
    def subnets(self):
        return self._subnet_service

    @property
    def routers(self):
        return self._router_service

    @property
    def _gateways(self):
        return self._gateway_service

    @property
    def _floating_ips(self):
        return self._floating_ip_service


class OpenStackNetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(OpenStackNetworkService, self).__init__(provider)

    @dispatch(event="provider.networking.networks.get",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def get(self, network_id):
        network = (n for n in self if n.id == network_id)
        return next(network, None)

    @dispatch(event="provider.networking.networks.list",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        networks = [OpenStackNetwork(self.provider, network)
                    for network in self.provider.neutron.list_networks()
                    .get('networks') if network
                    # If there are no availability zones, keep the network
                    # in the results list
                    and (not network.get('availability_zones')
                         or self.provider.service_zone_name(self)
                         in network.get('availability_zones'))]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.networks.find",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    @dispatch(event="provider.networking.networks.create",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def create(self, label, cidr_block):
        OpenStackNetwork.assert_valid_resource_label(label)
        net_info = {'name': label or ""}
        network = self.provider.neutron.create_network({'network': net_info})
        cb_net = OpenStackNetwork(self.provider, network.get('network'))
        return cb_net

    @dispatch(event="provider.networking.networks.delete",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def delete(self, network):
        network = (network if isinstance(network, OpenStackNetwork) else
                   self.get(network))
        if not network:
            return
        if not network.external and network.id in str(
                self.provider.neutron.list_networks()):
            # If there are ports associated with the network, it won't delete
            ports = self.provider.neutron.list_ports(
                network_id=network.id).get('ports', [])
            for port in ports:
                try:
                    self.provider.neutron.delete_port(port.get('id'))
                except PortNotFoundClient:
                    # Ports could have already been deleted if instances
                    # are terminated etc. so exceptions can be safely ignored
                    pass
            self.provider.neutron.delete_network(network.id)


class OpenStackSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(OpenStackSubnetService, self).__init__(provider)

    @dispatch(event="provider.networking.subnets.get",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def get(self, subnet_id):
        subnet = (s for s in self if s.id == subnet_id)
        return next(subnet, None)

    @dispatch(event="provider.networking.subnets.list",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
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

    @dispatch(event="provider.networking.subnets.create",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network, cidr_block):
        OpenStackSubnet.assert_valid_resource_label(label)
        network_id = (network.id if isinstance(network, OpenStackNetwork)
                      else network)
        subnet_info = {'name': label, 'network_id': network_id,
                       'cidr': cidr_block, 'ip_version': 4}
        subnet = (self.provider.neutron.create_subnet({'subnet': subnet_info})
                  .get('subnet'))
        cb_subnet = OpenStackSubnet(self.provider, subnet)
        return cb_subnet

    @dispatch(event="provider.networking.subnets.delete",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def delete(self, subnet):
        sn_id = subnet.id if isinstance(subnet, OpenStackSubnet) else subnet
        self.provider.neutron.delete_subnet(sn_id)

    def get_or_create_default(self):
        try:
            sn = self.find(label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL)
            if sn:
                return sn[0]
            # No default subnet look for default network, then create subnet
            net = self.provider.networking.networks.get_or_create_default()
            sn = self.provider.networking.subnets.create(
                label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL,
                cidr_block=OpenStackSubnet.CB_DEFAULT_SUBNET_IPV4RANGE,
                network=net)
            router = self.provider.networking.routers.get_or_create_default(
                net)
            router.attach_subnet(sn)
            gateway = net.gateways.get_or_create()
            router.attach_gateway(gateway)
            return sn
        except NeutronClientException:
            return None


class OpenStackRouterService(BaseRouterService):

    def __init__(self, provider):
        super(OpenStackRouterService, self).__init__(provider)

    @dispatch(event="provider.networking.routers.get",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def get(self, router_id):
        router = self.provider.os_conn.get_router(router_id)
        if not router:
            log.debug("Router %s was not found.", router_id)
            return None
        elif self.provider.service_zone_name(self) \
                not in router.availability_zones:
            log.debug("Router %s was found in availability zone '%s' while the"
                      " OpenStack provider is in zone '%s'",
                      router_id,
                      router.availability_zones,
                      self.provider.service_zone_name(self))
            return None
        return OpenStackRouter(self.provider, router)

    @dispatch(event="provider.networking.routers.list",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        routers = self.provider.os_conn.list_routers()
        os_routers = [OpenStackRouter(self.provider, r) for r in routers
                      if self.provider.service_zone_name(self)
                      in r.availability_zones]
        return ClientPagedResultList(self.provider, os_routers, limit=limit,
                                     marker=marker)

    @dispatch(event="provider.networking.routers.find",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    @dispatch(event="provider.networking.routers.create",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network):
        """Parameter ``network`` is not used by OpenStack."""
        router = self.provider.os_conn.create_router(name=label)
        return OpenStackRouter(self.provider, router)

    @dispatch(event="provider.networking.routers.delete",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def delete(self, router):
        r_id = router.id if isinstance(router, OpenStackRouter) else router
        self.provider.os_conn.delete_router(r_id)


class OpenStackGatewayService(BaseGatewayService):
    """For OpenStack, an internet gateway is a just an 'external' network."""

    def __init__(self, provider):
        super(OpenStackGatewayService, self).__init__(provider)

    def _check_fip_connectivity(self, network, external_net):
        # Due to current limitations in OpenStack:
        # https://bugs.launchpad.net/neutron/+bug/1743480, it's not
        # possible to differentiate between floating ip networks and provider
        # external networks. Therefore, we systematically step through
        # all available networks and perform an assignment test to infer valid
        # floating ip nets.
        dummy_router = self._provider.networking.routers.create(
            label='cb-conn-test-router', network=network)
        with cb_helpers.cleanup_action(lambda: dummy_router.delete()):
            try:
                dummy_router.attach_gateway(external_net)
                return True
            except Exception:
                return False

    @dispatch(event="provider.networking.gateways.get_or_create",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def get_or_create(self, network):
        """For OS, inet gtw is any net that has `external` property set."""
        external_nets = (n for n in self._provider.networking.networks
                         if n.external)
        for net in external_nets:
            if self._check_fip_connectivity(network, net):
                return OpenStackInternetGateway(self._provider, net)
        return None

    @dispatch(event="provider.networking.gateways.delete",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def delete(self, network, gateway):
        pass

    @dispatch(event="provider.networking.gateways.list",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def list(self, network, limit=None, marker=None):
        log.debug("OpenStack listing of all current internet gateways")
        igl = [OpenStackInternetGateway(self._provider, n)
               for n in self._provider.networking.networks
               if n.external and self._check_fip_connectivity(network, n)]
        return ClientPagedResultList(self._provider, igl, limit=limit,
                                     marker=marker)


class OpenStackFloatingIPService(BaseFloatingIPService):

    def __init__(self, provider):
        super(OpenStackFloatingIPService, self).__init__(provider)

    @dispatch(event="provider.networking.floating_ips.get",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def get(self, gateway, fip_id):
        try:
            return OpenStackFloatingIP(
                self.provider,
                self.provider.os_conn.network.get_ip(fip_id))
        except (ResourceNotFound, NotFoundException):
            log.debug("Floating IP %s not found.", fip_id)
            return None

    @dispatch(event="provider.networking.floating_ips.list",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def list(self, gateway, limit=None, marker=None):
        fips = [OpenStackFloatingIP(self.provider, fip)
                for fip in self.provider.os_conn.network.ips(
                    floating_network_id=gateway.id
                )]
        return ClientPagedResultList(self.provider, fips,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.floating_ips.create",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def create(self, gateway):
        return OpenStackFloatingIP(
            self.provider, self.provider.os_conn.network.create_ip(
                floating_network_id=gateway.id))

    @dispatch(event="provider.networking.floating_ips.delete",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def delete(self, gateway, fip):
        if isinstance(fip, OpenStackFloatingIP):
            # pylint:disable=protected-access
            os_ip = fip._ip
        else:
            try:
                os_ip = self.provider.os_conn.network.get_ip(fip)
            except (ResourceNotFound, NotFoundException):
                log.debug("Floating IP %s not found.", fip)
                return True
        os_ip.delete(self._provider.os_conn.network)


class OpenStackDnsService(BaseDnsService):

    def __init__(self, provider):
        super(OpenStackDnsService, self).__init__(provider)

        # Initialize provider services
        self._zone_svc = OpenStackDnsZoneService(self.provider)
        self._record_svc = OpenStackDnsRecordService(self.provider)

    @property
    def host_zones(self):
        return self._zone_svc

    @property
    def _records(self):
        return self._record_svc


class OpenStackDnsZoneService(BaseDnsZoneService):

    def __init__(self, provider):
        super(OpenStackDnsZoneService, self).__init__(provider)

    @dispatch(event="provider.dns.host_zones.get",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def get(self, dns_zone_id):
        try:
            return OpenStackDnsZone(
                self.provider,
                self.provider.os_conn.dns.get_zone(dns_zone_id))
        except (ResourceNotFound, NotFoundException, BadRequestException):
            log.debug("Dns Zone %s not found.", dns_zone_id)
            return None

    @dispatch(event="provider.dns.host_zones.list",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        zones = [OpenStackDnsZone(self.provider, zone)
                 for zone in self.provider.os_conn.dns.zones()]
        return ClientPagedResultList(self.provider, zones,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.dns.host_zones.find",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, self)
        return ClientPagedResultList(self.provider, list(matches),
                                     limit=None, marker=None)

    @dispatch(event="provider.dns.host_zones.create",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def create(self, name, admin_email):
        OpenStackDnsZone.assert_valid_resource_name(name)

        return OpenStackDnsZone(
            self.provider, self.provider.os_conn.dns.create_zone(
                name=self._get_fully_qualified_dns(name),
                email=admin_email, ttl=3600))

    @dispatch(event="provider.dns.host_zones.delete",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def delete(self, dns_zone):
        zone_id = (dns_zone.id if isinstance(dns_zone, OpenStackDnsZone)
                   else dns_zone)
        if zone_id:
            self.provider.os_conn.dns.delete_zone(zone_id)


class OpenStackDnsRecordService(BaseDnsRecordService):

    def __init__(self, provider):
        super(OpenStackDnsRecordService, self).__init__(provider)

    def _to_resource_records(self, data, rec_type):
        """
        Converts a record to what OpenStack expects. For example,
        OpenStack expects a fully qualified name for all CNAME records.
        """
        if isinstance(data, list):
            records = data
        else:
            records = [data]
        return [self._standardize_record(r, rec_type) for r in records]

    def get(self, dns_zone, rec_id):
        try:
            return OpenStackDnsRecord(
                self.provider, dns_zone,
                self.provider.os_conn.dns.get_recordset(rec_id, dns_zone.id))
        except (ResourceNotFound, NotFoundException, BadRequestException):
            log.debug("Dns Record %s not found.", rec_id)
            return None

    def list(self, dns_zone, limit=None, marker=None):
        recs = [OpenStackDnsRecord(self.provider, dns_zone, rec)
                for rec in self.provider.os_conn.dns.recordsets(dns_zone.id)]
        return ClientPagedResultList(self.provider, recs,
                                     limit=limit, marker=marker)

    def find(self, dns_zone, **kwargs):
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, dns_zone.records)
        return ClientPagedResultList(self.provider, list(matches),
                                     limit=None, marker=None)

    def create(self, dns_zone, name, type, data, ttl=None):
        OpenStackDnsRecord.assert_valid_resource_name(name)

        return OpenStackDnsRecord(
            self.provider, dns_zone,
            self.provider.os_conn.dns.create_recordset(
                zone=dns_zone.id, name=name, type=type,
                records=self._to_resource_records(data, type),
                ttl=ttl or 3600))

    def delete(self, dns_zone, record):
        rec_id = (record.id if isinstance(record, OpenStackDnsRecord)
                  else record)
        if rec_id:
            self.provider.os_conn.dns.delete_recordset(
                rec_id, zone=dns_zone.id)
