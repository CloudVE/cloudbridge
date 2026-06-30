"""
Services implemented by the OpenStack provider.
"""
from __future__ import annotations

import builtins
import json
import logging
import uuid
from typing import Any
from typing import IO
from typing import TYPE_CHECKING
from typing import cast

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
from cloudbridge.base.resources import BaseMultipartUpload
from cloudbridge.base.resources import BaseUploadPart
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
from cloudbridge.interfaces.exceptions import ProviderInternalException
from cloudbridge.interfaces.resources import Bucket
from cloudbridge.interfaces.resources import BucketObject
from cloudbridge.interfaces.resources import DnsRecord
from cloudbridge.interfaces.resources import DnsZone
from cloudbridge.interfaces.resources import FloatingIP
from cloudbridge.interfaces.resources import Gateway
from cloudbridge.interfaces.resources import Instance
from cloudbridge.interfaces.resources import InternetGateway
from cloudbridge.interfaces.resources import KeyPair
from cloudbridge.interfaces.resources import LaunchConfig
from cloudbridge.interfaces.resources import MachineImage
from cloudbridge.interfaces.resources import MultipartUpload
from cloudbridge.interfaces.resources import Network
from cloudbridge.interfaces.resources import Region
from cloudbridge.interfaces.resources import ResultList
from cloudbridge.interfaces.resources import Router
from cloudbridge.interfaces.resources import Snapshot
from cloudbridge.interfaces.resources import Subnet
from cloudbridge.interfaces.resources import TrafficDirection
from cloudbridge.interfaces.resources import UploadPart
from cloudbridge.interfaces.resources import VMFirewall
from cloudbridge.interfaces.resources import VMFirewallRule
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

if TYPE_CHECKING:
    from cloudbridge.interfaces.provider import CloudProvider
    from cloudbridge.providers.openstack.provider import OpenStackCloudProvider

log = logging.getLogger(__name__)


class OpenStackSecurityService(BaseSecurityService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackSecurityService, self).__init__(provider)

        # pylint:disable=protected-access
        os_provider = cast("OpenStackCloudProvider", self.provider)
        self.service_zone_name = os_provider._get_config_value(
            'os_security_zone_name', cb_helpers.get_env(
                'OS_SECURITY_ZONE_NAME', self.provider.zone_name))
        # Initialize provider services
        self._key_pairs = OpenStackKeyPairService(provider)
        self._vm_firewalls = OpenStackVMFirewallService(provider)
        self._vm_firewall_rule_svc = OpenStackVMFirewallRuleService(provider)

    @property
    def key_pairs(self) -> OpenStackKeyPairService:
        return self._key_pairs

    @property
    def vm_firewalls(self) -> OpenStackVMFirewallService:
        return self._vm_firewalls

    @property
    def _vm_firewall_rules(self) -> OpenStackVMFirewallRuleService:
        return self._vm_firewall_rule_svc

    def get_or_create_ec2_credentials(self) -> Any:
        """
        A provider specific method than returns the ec2 credentials for the
        current user, or creates a new pair if one doesn't exist.
        """
        keystone = cast("OpenStackCloudProvider", self.provider).keystone
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

    def get_ec2_endpoints(self) -> dict[str, Any]:
        """
        A provider specific method than returns the ec2 endpoints if
        available.
        """
        keystone = cast("OpenStackCloudProvider", self.provider).keystone
        ec2_url = keystone.session.get_endpoint(service_type='ec2')
        s3_url = keystone.session.get_endpoint(service_type='s3')

        return {'ec2_endpoint': ec2_url,
                's3_endpoint': s3_url}


class OpenStackKeyPairService(BaseKeyPairService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackKeyPairService, self).__init__(provider)

    @dispatch(event="provider.security.key_pairs.get",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def get(self, key_pair_id: str) -> KeyPair | None:
        """
        Returns a KeyPair given its id.
        """
        log.debug("Returning KeyPair with the id %s", key_pair_id)
        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            return OpenStackKeyPair(
                provider, provider.nova.keypairs.get(key_pair_id))
        except NovaNotFound:
            log.debug("KeyPair %s was not found.", key_pair_id)
            return None

    @dispatch(event="provider.security.key_pairs.list",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[KeyPair]:
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        provider = cast("OpenStackCloudProvider", self.provider)
        keypairs = provider.nova.keypairs.list()
        results = [OpenStackKeyPair(provider, kp)
                   for kp in keypairs]
        log.debug("Listing all key pairs associated with OpenStack "
                  "Account: %s", results)
        return ClientPagedResultList(self.provider, results,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.security.key_pairs.find",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[KeyPair]:
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'name'))

        provider = cast("OpenStackCloudProvider", self.provider)
        keypairs = provider.nova.keypairs.findall(name=name)
        results = [OpenStackKeyPair(provider, kp)
                   for kp in keypairs]
        log.debug("Searching for %s in: %s", name, keypairs)
        return ClientPagedResultList(self.provider, results)

    @dispatch(event="provider.security.key_pairs.create",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def create(self, name: str,
               public_key_material: str | None = None) -> KeyPair:
        OpenStackKeyPair.assert_valid_resource_name(name)
        existing_kp = self.find(name=name)
        if existing_kp:
            raise DuplicateResourceException(
                'Keypair already exists with name {0}'.format(name))

        private_key = None
        if not public_key_material:
            public_key_material, private_key = cb_helpers.generate_key_pair()

        provider = cast("OpenStackCloudProvider", self.provider)
        kp = provider.nova.keypairs.create(name,
                                           public_key=public_key_material)
        cb_kp = OpenStackKeyPair(provider, kp)
        cb_kp.material = private_key
        return cb_kp

    @dispatch(event="provider.security.key_pairs.delete",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def delete(self, key_pair: KeyPair | str) -> None:
        keypair = (key_pair if isinstance(key_pair, OpenStackKeyPair)
                   else self.get(key_pair))
        if keypair:
            # pylint:disable=protected-access
            keypair._key_pair.delete()


class OpenStackVMFirewallService(BaseVMFirewallService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackVMFirewallService, self).__init__(provider)

    @dispatch(event="provider.security.vm_firewalls.get",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_firewall_id: str) -> VMFirewall | None:
        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            return OpenStackVMFirewall(
                provider,
                provider.os_conn.network.get_security_group(
                    vm_firewall_id))
        except (ResourceNotFound, NotFoundException):
            log.debug("Firewall %s not found.", vm_firewall_id)
            return None

    @dispatch(event="provider.security.vm_firewalls.list",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[VMFirewall]:
        provider = cast("OpenStackCloudProvider", self.provider)
        firewalls = [
            OpenStackVMFirewall(provider, fw)
            for fw in provider.os_conn.network.security_groups()]

        return ClientPagedResultList(self.provider, firewalls,
                                     limit=limit, marker=marker)

    @cb_helpers.deprecated_alias(network_id='network')
    @dispatch(event="provider.security.vm_firewalls.create",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, network: Network | str,
               description: str | None = None) -> VMFirewall:
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
        provider = cast("OpenStackCloudProvider", self.provider)
        sg = provider.os_conn.network.create_security_group(
            name=label, description=description)
        # The interface declares create() -> VMFirewall; the SDK always returns
        # a security group on success, so a None return is not expected here.
        return OpenStackVMFirewall(provider, sg)

    @dispatch(event="provider.security.vm_firewalls.delete",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def delete(self, vm_firewall: VMFirewall | str) -> None:
        fw = (vm_firewall if isinstance(vm_firewall, OpenStackVMFirewall)
              else self.get(vm_firewall))
        if fw:
            # pylint:disable=protected-access
            provider = cast("OpenStackCloudProvider", self.provider)
            fw._vm_firewall.delete(provider.os_conn.network)


class OpenStackVMFirewallRuleService(BaseVMFirewallRuleService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackVMFirewallRuleService, self).__init__(provider)

    @dispatch(event="provider.security.vm_firewall_rules.list",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def list(self, firewall: VMFirewall, limit: int | None = None,
             marker: str | None = None) -> ResultList[VMFirewallRule]:
        # pylint:disable=protected-access
        rules = [OpenStackVMFirewallRule(firewall, r)
                 for r in cast(Any, firewall)._vm_firewall
                 .security_group_rules]
        return ClientPagedResultList(self.provider, rules,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.security.vm_firewall_rules.create",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def create(self, firewall: VMFirewall, direction: TrafficDirection,
               protocol: str | None = None, from_port: int | None = None,
               to_port: int | None = None, cidr: str | None = None,
               src_dest_fw: VMFirewall | None = None) -> VMFirewallRule:
        src_dest_fw_id = (src_dest_fw.id if isinstance(src_dest_fw,
                                                       OpenStackVMFirewall)
                          else src_dest_fw)

        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            if direction == TrafficDirection.INBOUND:
                os_direction = 'ingress'
            elif direction == TrafficDirection.OUTBOUND:
                os_direction = 'egress'
            else:
                raise InvalidValueException("direction", direction)
            # pylint:disable=protected-access
            rule = provider.os_conn.network.create_security_group_rule(
                security_group_id=firewall.id,
                direction=os_direction,
                port_range_max=to_port,
                port_range_min=from_port,
                protocol=protocol,
                remote_ip_prefix=cidr,
                remote_group_id=src_dest_fw_id)
            cast(Any, firewall).refresh()
            return OpenStackVMFirewallRule(firewall, rule.to_dict())
        except HttpException as e:
            cast(Any, firewall).refresh()
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
    def delete(self, firewall: VMFirewall,
               rule: VMFirewallRule | str) -> None:
        rule_id = (rule.id if isinstance(rule, OpenStackVMFirewallRule)
                   else rule)
        provider = cast("OpenStackCloudProvider", self.provider)
        provider.os_conn.network.delete_security_group_rule(rule_id)
        cast(Any, firewall).refresh()


class OpenStackStorageService(BaseStorageService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackStorageService, self).__init__(provider)

        # pylint:disable=protected-access
        os_provider = cast("OpenStackCloudProvider", self.provider)
        self.service_zone_name = os_provider._get_config_value(
            'os_storage_zone_name', cb_helpers.get_env(
                'OS_STORAGE_ZONE_NAME', self.provider.zone_name))
        # Initialize provider services
        self._volume_svc = OpenStackVolumeService(self.provider)
        self._snapshot_svc = OpenStackSnapshotService(self.provider)
        self._bucket_svc = OpenStackBucketService(self.provider)
        self._bucket_obj_svc = OpenStackBucketObjectService(self.provider)

    @property
    def volumes(self) -> OpenStackVolumeService:
        return self._volume_svc

    @property
    def snapshots(self) -> OpenStackSnapshotService:
        return self._snapshot_svc

    @property
    def buckets(self) -> OpenStackBucketService:
        return self._bucket_svc

    @property
    def _bucket_objects(self) -> OpenStackBucketObjectService:
        return self._bucket_obj_svc


class OpenStackVolumeService(BaseVolumeService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackVolumeService, self).__init__(provider)

    @dispatch(event="provider.storage.volumes.get",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def get(self, volume_id: str) -> Volume | None:
        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            os_vol = provider.os_conn.block_storage.get_volume(volume_id)
        except (NotFoundException, ResourceNotFound):
            log.debug("Volume %s was not found.", volume_id)
            return None
        if os_vol.availability_zone != cast("OpenStackCloudProvider", self.provider).service_zone_name(self):
            log.debug("Volume %s was found in availability zone '%s' while the"
                      " OpenStack provider is in zone '%s'",
                      volume_id,
                      os_vol.availability_zone,
                      cast("OpenStackCloudProvider", self.provider).service_zone_name(self))
            return None
        else:
            return OpenStackVolume(provider, os_vol)

    @dispatch(event="provider.storage.volumes.find",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Volume]:
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for an OpenStack Volume with the label %s", label)
        provider = cast("OpenStackCloudProvider", self.provider)
        cb_vols = [
            OpenStackVolume(provider, vol)
            for vol in provider.os_conn.block_storage.volumes(
                name=label,
                limit=oshelpers.os_result_limit(self.provider),
                marker=None)
            if vol.availability_zone == cast("OpenStackCloudProvider", self.provider).service_zone_name(self)]
        return oshelpers.to_server_paged_list(self.provider, cb_vols)

    @dispatch(event="provider.storage.volumes.list",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Volume]:
        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            os_vols = list(provider.os_conn.block_storage.volumes(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker))
        except NotFoundException:
            # Cinder returns 404 when the supplied pagination marker
            # refers to a volume that has since been deleted (e.g.,
            # between the time a caller saw the volume in page N and
            # asked for page N+1, or when a concurrent test deletes it).
            # Fall back to a fresh listing.
            if marker is None:
                raise
            os_vols = list(provider.os_conn.block_storage.volumes(
                limit=oshelpers.os_result_limit(self.provider, limit)))
        cb_vols = [OpenStackVolume(provider, vol) for vol in os_vols
                   if vol.availability_zone ==
                   cast("OpenStackCloudProvider", self.provider).service_zone_name(self)]
        return oshelpers.to_server_paged_list(self.provider, cb_vols, limit)

    @dispatch(event="provider.storage.volumes.create",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, size: int,
               snapshot: Snapshot | str | None = None,
               description: str | None = None) -> Volume:
        OpenStackVolume.assert_valid_resource_label(label)
        zone_name = cast("OpenStackCloudProvider", self.provider).service_zone_name(self)
        snapshot_id = snapshot.id if isinstance(
            snapshot, OpenStackSnapshot) and snapshot else snapshot

        provider = cast("OpenStackCloudProvider", self.provider)
        os_vol = provider.os_conn.block_storage.create_volume(
            size=size, name=label, description=description,
            availability_zone=zone_name, snapshot_id=snapshot_id)
        return OpenStackVolume(provider, os_vol)

    @dispatch(event="provider.storage.volumes.delete",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def delete(self, volume: Volume | str) -> None:
        vol = (volume if isinstance(volume, OpenStackVolume)
               else self.get(volume))
        if vol:
            # pylint:disable=protected-access
            provider = cast("OpenStackCloudProvider", self.provider)
            provider.os_conn.block_storage.delete_volume(vol._volume)


class OpenStackSnapshotService(BaseSnapshotService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackSnapshotService, self).__init__(provider)

    @dispatch(event="provider.storage.snapshots.get",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def get(self, snapshot_id: str) -> Snapshot | None:
        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            return OpenStackSnapshot(
                provider,
                provider.os_conn.block_storage.get_snapshot(snapshot_id))
        except (NotFoundException, ResourceNotFound):
            log.debug("Snapshot %s was not found.", snapshot_id)
            return None

    @dispatch(event="provider.storage.snapshots.find",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Snapshot]:
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
        provider = cast("OpenStackCloudProvider", self.provider)
        cb_snaps = [
            OpenStackSnapshot(provider, snap) for
            snap in provider.os_conn.block_storage.snapshots(
                **search_opts)
            if snap.name == label]

        return oshelpers.to_server_paged_list(self.provider, cb_snaps)

    @dispatch(event="provider.storage.snapshots.list",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Snapshot]:
        provider = cast("OpenStackCloudProvider", self.provider)
        cb_snaps = [
            OpenStackSnapshot(provider, snap)
            for snap in provider.os_conn.block_storage.snapshots(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)
        ]
        return oshelpers.to_server_paged_list(self.provider, cb_snaps, limit)

    @dispatch(event="provider.storage.snapshots.create",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, volume: Volume | str,
               description: str | None = None) -> Snapshot:
        OpenStackSnapshot.assert_valid_resource_label(label)
        volume_id = (volume.id if isinstance(volume, OpenStackVolume)
                     else volume)

        provider = cast("OpenStackCloudProvider", self.provider)
        os_snap = provider.os_conn.block_storage.create_snapshot(
            volume_id=volume_id, name=label,
            description=description)
        return OpenStackSnapshot(provider, os_snap)

    @dispatch(event="provider.storage.snapshots.delete",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def delete(self, snapshot: Snapshot | str) -> None:
        s = (snapshot if isinstance(snapshot, OpenStackSnapshot) else
             self.get(snapshot))
        if s:
            # pylint:disable=protected-access
            provider = cast("OpenStackCloudProvider", self.provider)
            provider.os_conn.block_storage.delete_snapshot(s._snapshot)


class OpenStackBucketService(BaseBucketService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackBucketService, self).__init__(provider)

    @dispatch(event="provider.storage.buckets.get",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def get(self, bucket_id: str) -> Bucket | None:
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        provider = cast("OpenStackCloudProvider", self.provider)
        _, container_list = provider.swift.get_account(
            prefix=bucket_id)
        if container_list:
            return OpenStackBucket(provider,
                                   next((c for c in container_list
                                         if c['name'] == bucket_id), None))
        else:
            log.debug("Bucket %s was not found.", bucket_id)
            return None

    @dispatch(event="provider.storage.buckets.find",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Bucket]:
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'name'))
        provider = cast("OpenStackCloudProvider", self.provider)
        _, container_list = provider.swift.get_account()
        cb_buckets = [OpenStackBucket(provider, c)
                      for c in container_list
                      if name in c.get("name")]
        return oshelpers.to_server_paged_list(self.provider, cb_buckets)

    @dispatch(event="provider.storage.buckets.list",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Bucket]:
        provider = cast("OpenStackCloudProvider", self.provider)
        _, container_list = provider.swift.get_account(
            limit=oshelpers.os_result_limit(self.provider, limit),
            marker=marker)
        cb_buckets = [OpenStackBucket(provider, c)
                      for c in container_list]
        return oshelpers.to_server_paged_list(self.provider, cb_buckets, limit)

    @dispatch(event="provider.storage.buckets.create",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def create(self, name: str,
               location: Region | str | None = None) -> Bucket:
        OpenStackBucket.assert_valid_resource_name(name)
        provider = cast("OpenStackCloudProvider", self.provider)
        location = location or self.provider.region_name
        try:
            provider.swift.head_container(name)
            raise DuplicateResourceException(
                'Bucket already exists with name {0}'.format(name))
        except SwiftClientException:
            provider.swift.put_container(name)
            # The interface declares create() -> Bucket; the container was just
            # created above, so get() returns it (not None) here.
            return cast(Bucket, self.get(name))

    @dispatch(event="provider.storage.buckets.delete",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def delete(self, bucket: Bucket | str) -> None:
        b_id = bucket.id if isinstance(bucket, OpenStackBucket) else bucket
        provider = cast("OpenStackCloudProvider", self.provider)
        provider.swift.delete_container(b_id)


class OpenStackBucketObjectService(BaseBucketObjectService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackBucketObjectService, self).__init__(provider)

    def get(self, bucket: Bucket | str,
            name: str) -> BucketObject | None:
        """
        Retrieve a given object from this bucket.
        """
        # Swift always returns a reference for the container first,
        # followed by a list containing references to objects.
        provider = cast("OpenStackCloudProvider", self.provider)
        _, object_list = provider.swift.get_container(
            cast(Any, bucket).name, prefix=name)
        # Loop through list of objects looking for an exact name vs. a prefix
        for obj in object_list:
            if obj.get('name') == name:
                return OpenStackBucketObject(provider,
                                             bucket,
                                             obj)
        return None

    # The interface declares list(bucket, prefix, limit, marker); this impl
    # orders the optional parameters as (limit, marker, prefix).
    def list(self, bucket: Bucket | str,  # type: ignore[override]
             limit: int | None = None, marker: str | None = None,
             prefix: str | None = None) -> ResultList[BucketObject]:
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        provider = cast("OpenStackCloudProvider", self.provider)
        _, object_list = provider.swift.get_container(
            cast(Any, bucket).name,
            limit=oshelpers.os_result_limit(self.provider, limit),
            marker=marker, prefix=prefix)
        cb_objects = [OpenStackBucketObject(
                provider, bucket, obj) for obj in object_list]

        return oshelpers.to_server_paged_list(
            self.provider,
            cb_objects,
            limit)

    def find(self, bucket: Bucket | str,
             **kwargs: Any) -> ResultList[BucketObject]:
        provider = cast("OpenStackCloudProvider", self.provider)
        _, obj_list = provider.swift.get_container(cast(Any, bucket).name)
        cb_objs = [OpenStackBucketObject(provider, bucket, obj)
                   for obj in obj_list]
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, cb_objs)
        return ClientPagedResultList(self.provider, list(matches))

    def create(self, bucket: Bucket | str,
               object_name: str) -> BucketObject:
        provider = cast("OpenStackCloudProvider", self.provider)
        provider.swift.put_object(cast(Any, bucket).name, object_name, None)
        # The interface declares create() -> BucketObject; the object was just
        # uploaded above, so get() returns it (not None) here.
        return cast(BucketObject, self.get(bucket, object_name))

    @staticmethod
    def _segment_prefix(upload: MultipartUpload) -> str:
        return "{0}/slo/{1}/".format(upload.object_name, upload.id)

    @classmethod
    def _segment_name(cls, upload: MultipartUpload, part_number: int) -> str:
        return "{0}{1:08d}".format(cls._segment_prefix(upload), part_number)

    @dispatch(event="provider.storage._bucket_objects.create_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def create_multipart_upload(self, bucket: Bucket | str,
                                object_name: str) -> MultipartUpload:
        # Swift has no server-side initiation; the upload id namespaces this
        # upload's Static Large Object segments.
        return BaseMultipartUpload(self.provider, cast(Bucket, bucket),
                                   object_name, uuid.uuid4().hex)

    @dispatch(event="provider.storage._bucket_objects.upload_part",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def upload_part(self, bucket: Bucket | str, upload: MultipartUpload,
                    part_number: int, data: bytes | IO[bytes]) -> UploadPart:
        if isinstance(data, str):
            data = data.encode()
        if not isinstance(data, (bytes, bytearray)):
            data = data.read()
        segment_name = self._segment_name(upload, part_number)
        provider = cast("OpenStackCloudProvider", self.provider)
        etag = provider.swift.put_object(
            cast(Any, bucket).name, segment_name, data)
        # Retain the manifest entry needed to assemble the SLO on complete.
        return BaseUploadPart(part_number, {
            'path': "/{0}/{1}".format(cast(Any, bucket).name, segment_name),
            'etag': etag,
            'size_bytes': len(data)})

    @dispatch(event="provider.storage._bucket_objects."
                    "complete_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def complete_multipart_upload(
            self, bucket: Bucket | str, upload: MultipartUpload,
            parts: builtins.list[UploadPart]) -> BucketObject:
        ordered = sorted(parts, key=lambda p: p.part_number)
        manifest = [p.etag for p in ordered]
        provider = cast("OpenStackCloudProvider", self.provider)
        provider.swift.put_object(
            cast(Any, bucket).name, upload.object_name, json.dumps(manifest),
            query_string='multipart-manifest=put')
        # The interface declares this -> BucketObject; the SLO manifest was just
        # written above, so get() returns it (not None) here.
        return cast(BucketObject, self.get(bucket, upload.object_name))

    @dispatch(event="provider.storage._bucket_objects.abort_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def abort_multipart_upload(self, bucket: Bucket | str,
                               upload: MultipartUpload) -> None:
        prefix = self._segment_prefix(upload)
        provider = cast("OpenStackCloudProvider", self.provider)
        _, object_list = provider.swift.get_container(
            cast(Any, bucket).name, prefix=prefix)
        for obj in object_list:
            try:
                provider.swift.delete_object(
                    cast(Any, bucket).name, obj.get('name'))
            except SwiftClientException:
                pass  # idempotent: ignore already-deleted segments


class OpenStackComputeService(BaseComputeService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackComputeService, self).__init__(provider)
        self._vm_type_svc = OpenStackVMTypeService(self.provider)
        self._instance_svc = OpenStackInstanceService(self.provider)
        self._region_svc = OpenStackRegionService(self.provider)
        self._images_svc = OpenStackImageService(self.provider)
        # Region service must be defined before invoking the following
        # pylint:disable=protected-access
        os_provider = cast("OpenStackCloudProvider", self.provider)
        self.service_zone_name = os_provider._get_config_value(
            'os_compute_zone_name',
            cb_helpers.get_env(
                'OS_COMPUTE_ZONE_NAME',
                os_provider._zone_name or
                cast(Any, self.regions.current).default_zone.name))

    @property
    def images(self) -> OpenStackImageService:
        return self._images_svc

    @property
    def vm_types(self) -> OpenStackVMTypeService:
        return self._vm_type_svc

    @property
    def instances(self) -> OpenStackInstanceService:
        return self._instance_svc

    @property
    def regions(self) -> OpenStackRegionService:
        return self._region_svc


class OpenStackImageService(BaseImageService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackImageService, self).__init__(provider)

    def get(self, image_id: str) -> MachineImage | None:
        """
        Returns an Image given its id
        """
        log.debug("Getting OpenStack Image with the id: %s", image_id)
        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            return OpenStackMachineImage(
                provider, provider.os_conn.image.get_image(image_id))
        except (NotFoundException, ResourceNotFound):
            log.debug("Image %s not found", image_id)
            return None

    def find(self, **kwargs: Any) -> ResultList[MachineImage]:
        filters = ['label']
        obj_list = list(self)
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self.provider, list(matches))

    # Intentionally extends the base list() with a leading filter_by_owner
    # parameter (matches the interface's documented arguments-differ override).
    def list(self,  # type: ignore[override]
             filter_by_owner: bool = True, limit: int | None = None,
             marker: str | None = None) -> ResultList[MachineImage]:
        """
        List all images.
        """
        project_id = None
        provider = cast("OpenStackCloudProvider", self.provider)
        if filter_by_owner:
            project_id = provider.os_conn.session.get_project_id()
        os_images = provider.os_conn.image.images(
            owner=project_id,
            limit=oshelpers.os_result_limit(self.provider, limit),
            marker=marker)

        cb_images = [
            OpenStackMachineImage(provider, img)
            for img in os_images]
        return oshelpers.to_server_paged_list(self.provider, cb_images, limit)


class OpenStackInstanceService(BaseInstanceService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackInstanceService, self).__init__(provider)

    def _to_block_device_mapping(
            self, launch_config: LaunchConfig) -> builtins.list[
                dict[str, Any]]:
        """
        Extracts block device mapping information
        from a launch config and constructs a BlockDeviceMappingV2
        object.
        """
        bdm = []
        for device in cast(Any, launch_config).block_devices:
            bdm_dict: dict[str, Any] = dict()

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

    def _has_root_device(self, launch_config: LaunchConfig | None) -> bool:
        if not launch_config:
            return False
        for device in cast(Any, launch_config).block_devices:
            if device.is_root:
                return True
        return False

    def create_launch_config(self) -> LaunchConfig:
        return BaseLaunchConfig(self.provider)

    @dispatch(event="provider.compute.instances.create",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, image: MachineImage | str,
               vm_type: VMType | str, subnet: Subnet | str,
               key_pair: KeyPair | str | None = None,
               vm_firewalls: builtins.list[VMFirewall] |
               builtins.list[str] | None = None,
               user_data: str | None = None,
               launch_config: LaunchConfig | None = None,
               **kwargs: Any) -> Instance:
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
        net_id: str | None
        if isinstance(subnet, Subnet):
            subnet_id = subnet.id
            net_id = subnet.network_id
        else:
            subnet_id = subnet
            net_id = (cast(Any, self.provider.networking.subnets
                           .get(subnet_id)).network_id
                      if subnet_id else None)
        os_provider = cast("OpenStackCloudProvider", self.provider)
        zone_name = os_provider.service_zone_name(self)
        key_pair_name = key_pair.name if \
            isinstance(key_pair, KeyPair) else key_pair
        bdm = None
        if launch_config:
            bdm = self._to_block_device_mapping(launch_config)

        provider = cast("OpenStackCloudProvider", self.provider)
        # Security groups must be passed in as a list of IDs and attached to a
        # port if a port is being created. Otherwise, the security groups must
        # be passed in as a list of names to the servers.create() call.
        # OpenStack will respect the port's security groups first and then
        # fall-back to the named security groups.
        sg_name_list: Any = []
        nics = None
        if subnet_id:
            log.debug("Creating network port for %s in subnet: %s",
                      label, subnet_id)
            sg_list: Any = []
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
            port_id = provider.neutron.create_port(port_def)['port']['id']
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
        os_instance = provider.nova.servers.create(
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
        return OpenStackInstance(provider, os_instance)

    @dispatch(event="provider.compute.instances.find",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Instance]:
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        provider = cast("OpenStackCloudProvider", self.provider)
        search_opts = {'name': label,
                       'availability_zone': provider.service_zone_name(self)}
        cb_insts = [
            OpenStackInstance(provider, inst)
            for inst in provider.nova.servers.list(
                search_opts=search_opts,
                limit=oshelpers.os_result_limit(self.provider),
                marker=None)]
        return oshelpers.to_server_paged_list(self.provider, cb_insts)

    @dispatch(event="provider.compute.instances.list",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Instance]:
        """
        List all instances.
        """
        provider = cast("OpenStackCloudProvider", self.provider)
        search_opts = {'availability_zone': provider.service_zone_name(self)}
        cb_insts = [
            OpenStackInstance(provider, inst)
            for inst in provider.nova.servers.list(
                search_opts=search_opts,
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)]
        return oshelpers.to_server_paged_list(self.provider, cb_insts, limit)

    @dispatch(event="provider.compute.instances.get",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def get(self, instance_id: str) -> Instance | None:
        """
        Returns an instance given its id.
        """
        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            os_instance = provider.nova.servers.get(instance_id)
        except NovaNotFound:
            log.debug("Instance %s was not found.", instance_id)
            return None
        if (getattr(os_instance,
                    'OS-EXT-AZ:availability_zone', "")
                != cast("OpenStackCloudProvider", self.provider).service_zone_name(self)):
            log.debug("Instance %s was found in availability zone '%s' while "
                      "the OpenStack provider is in zone '%s'",
                      instance_id,
                      getattr(os_instance, 'OS-EXT-AZ:availability_zone', ""),
                      cast("OpenStackCloudProvider", self.provider).service_zone_name(self))
            return None
        return OpenStackInstance(provider, os_instance)

    @dispatch(event="provider.compute.instances.delete",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def delete(self, instance: Instance | str) -> None:
        ins = (instance if isinstance(instance, OpenStackInstance) else
               self.get(instance))
        if ins:
            # pylint:disable=protected-access
            os_instance = ins._os_instance
            # delete the port we created when launching
            # Assumption: it's the first interface in the list
            provider = cast("OpenStackCloudProvider", self.provider)
            iface_list = os_instance.interface_list()
            if iface_list:
                with cb_helpers.cleanup_action(
                        lambda: provider.neutron.delete_port(
                            iface_list[0].port_id)):
                    # Ignore errors if port can't be deleted
                    pass
            os_instance.delete()


class OpenStackVMTypeService(BaseVMTypeService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackVMTypeService, self).__init__(provider)

    @dispatch(event="provider.compute.vm_types.list",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[VMType]:
        provider = cast("OpenStackCloudProvider", self.provider)
        cb_itypes = [
            OpenStackVMType(provider, obj)
            for obj in provider.nova.flavors.list(
                limit=oshelpers.os_result_limit(self.provider, limit),
                marker=marker)]

        return oshelpers.to_server_paged_list(self.provider, cb_itypes, limit)


class OpenStackRegionService(BaseRegionService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackRegionService, self).__init__(provider)

    @dispatch(event="provider.compute.regions.get",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def get(self, region_id: str) -> Region | None:
        log.debug("Getting OpenStack Region with the id: %s", region_id)
        region = (r for r in self if r.id == region_id)
        return next(region, None)

    @dispatch(event="provider.compute.regions.list",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Region]:
        # pylint:disable=protected-access
        provider = cast("OpenStackCloudProvider", self.provider)
        if provider._keystone_version == 3:
            os_regions = [OpenStackRegion(provider, region)
                          for region in provider.keystone.regions.list()]
            return ClientPagedResultList(self.provider, os_regions,
                                         limit=limit, marker=marker)
        else:
            # Keystone v3 onwards supports directly listing regions
            # but for v2, this convoluted method is necessary.
            regions = (
                endpoint.get('region') or endpoint.get('region_id')
                for svc in provider.keystone.service_catalog.get_data()
                for endpoint in svc.get('endpoints', [])
            )
            unique_regions = set(region for region in regions if region)
            os_regions = [OpenStackRegion(provider, region)
                          for region in unique_regions]

            return ClientPagedResultList(self.provider, os_regions,
                                         limit=limit, marker=marker)

    @property
    def current(self) -> Region | None:
        provider = cast("OpenStackCloudProvider", self.provider)
        nova_region = provider.nova.client.region_name
        return self.get(nova_region) if nova_region else None


class OpenStackNetworkingService(BaseNetworkingService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackNetworkingService, self).__init__(provider)
        # pylint:disable=protected-access
        os_provider = cast("OpenStackCloudProvider", self.provider)
        self.service_zone_name = os_provider._get_config_value(
            'os_networking_zone_name', cb_helpers.get_env(
                'OS_NETWORKING_ZONE_NAME', self.provider.zone_name))
        self._network_service = OpenStackNetworkService(self.provider)
        self._subnet_service = OpenStackSubnetService(self.provider)
        self._router_service = OpenStackRouterService(self.provider)
        self._gateway_service = OpenStackGatewayService(self.provider)
        self._floating_ip_service = OpenStackFloatingIPService(self.provider)

    @property
    def networks(self) -> OpenStackNetworkService:
        return self._network_service

    @property
    def subnets(self) -> OpenStackSubnetService:
        return self._subnet_service

    @property
    def routers(self) -> OpenStackRouterService:
        return self._router_service

    @property
    def _gateways(self) -> OpenStackGatewayService:
        return self._gateway_service

    @property
    def _floating_ips(self) -> OpenStackFloatingIPService:
        return self._floating_ip_service


class OpenStackNetworkService(BaseNetworkService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackNetworkService, self).__init__(provider)

    @dispatch(event="provider.networking.networks.get",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def get(self, network_id: str) -> Network | None:
        network = (n for n in self if n.id == network_id)
        return next(network, None)

    @dispatch(event="provider.networking.networks.list",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Network]:
        provider = cast("OpenStackCloudProvider", self.provider)
        networks = [OpenStackNetwork(provider, network)
                    for network in provider.neutron.list_networks()
                    .get('networks') if network
                    # If there are no availability zones, keep the network
                    # in the results list
                    and (not network.get('availability_zones')
                         or cast("OpenStackCloudProvider", self.provider).service_zone_name(self)
                         in network.get('availability_zones'))]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.networks.find",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Network]:
        obj_list = list(self)
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    @dispatch(event="provider.networking.networks.create",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, cidr_block: str) -> Network:
        OpenStackNetwork.assert_valid_resource_label(label)
        net_info = {'name': label or ""}
        provider = cast("OpenStackCloudProvider", self.provider)
        network = provider.neutron.create_network({'network': net_info})
        cb_net = OpenStackNetwork(provider, network.get('network'))
        return cb_net

    @dispatch(event="provider.networking.networks.delete",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def delete(self, network: Network | str) -> None:
        network = (network if isinstance(network, OpenStackNetwork) else
                   self.get(network))
        if not network:
            return
        provider = cast("OpenStackCloudProvider", self.provider)
        if not network.external and network.id in str(
                provider.neutron.list_networks()):
            # If there are ports associated with the network, it won't delete
            ports = provider.neutron.list_ports(
                network_id=network.id).get('ports', [])
            for port in ports:
                try:
                    provider.neutron.delete_port(port.get('id'))
                except PortNotFoundClient:
                    # Ports could have already been deleted if instances
                    # are terminated etc. so exceptions can be safely ignored
                    pass
            provider.neutron.delete_network(network.id)


class OpenStackSubnetService(BaseSubnetService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackSubnetService, self).__init__(provider)

    @dispatch(event="provider.networking.subnets.get",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def get(self, subnet_id: str) -> Subnet | None:
        subnet = (s for s in self if s.id == subnet_id)
        return next(subnet, None)

    @dispatch(event="provider.networking.subnets.list",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def list(self, network: Network | str | None = None,
             limit: int | None = None,
             marker: str | None = None) -> ResultList[Subnet]:
        provider = cast("OpenStackCloudProvider", self.provider)
        if network:
            network_id = (network.id if isinstance(network, OpenStackNetwork)
                          else network)
            subnets = [subnet for subnet in self if network_id ==
                       subnet.network_id]
        else:
            subnets = [OpenStackSubnet(provider, subnet) for subnet in
                       provider.neutron.list_subnets().get('subnets', [])]
        return ClientPagedResultList(self.provider, subnets,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.subnets.create",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, network: Network | str,
               cidr_block: str) -> Subnet:
        OpenStackSubnet.assert_valid_resource_label(label)
        network_id = (network.id if isinstance(network, OpenStackNetwork)
                      else network)
        subnet_info = {'name': label, 'network_id': network_id,
                       'cidr': cidr_block, 'ip_version': 4}
        provider = cast("OpenStackCloudProvider", self.provider)
        subnet = (provider.neutron.create_subnet({'subnet': subnet_info})
                  .get('subnet'))
        cb_subnet = OpenStackSubnet(provider, subnet)
        return cb_subnet

    @dispatch(event="provider.networking.subnets.delete",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def delete(self, subnet: Subnet | str) -> None:
        sn_id = subnet.id if isinstance(subnet, OpenStackSubnet) else subnet
        provider = cast("OpenStackCloudProvider", self.provider)
        provider.neutron.delete_subnet(sn_id)

    # The base declares -> Subnet, but this impl can return None when the
    # default subnet cannot be found or created (NeutronClientException).
    def get_or_create_default(self) -> Subnet | None:  # type: ignore[override]
        try:
            existing = self.find(
                label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL)
            if existing:
                return existing[0]
            # No default subnet look for default network, then create subnet
            # get_or_create_default is only on the base services, not the
            # public NetworkService/RouterService interface; access via Any.
            net = cast(Any, self.provider.networking
                       .networks).get_or_create_default()
            sn = self.provider.networking.subnets.create(
                label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL,
                cidr_block=OpenStackSubnet.CB_DEFAULT_SUBNET_IPV4RANGE,
                network=net)
            router = cast(Any, self.provider.networking
                          .routers).get_or_create_default(net)
            router.attach_subnet(sn)
            gateway = net.gateways.get_or_create()
            router.attach_gateway(gateway)
            return sn
        except NeutronClientException:
            return None


class OpenStackRouterService(BaseRouterService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackRouterService, self).__init__(provider)

    @dispatch(event="provider.networking.routers.get",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def get(self, router_id: str) -> Router | None:
        provider = cast("OpenStackCloudProvider", self.provider)
        router = provider.os_conn.get_router(router_id)
        if not router:
            log.debug("Router %s was not found.", router_id)
            return None
        elif router.availability_zones and \
                cast("OpenStackCloudProvider", self.provider).service_zone_name(self) \
                not in router.availability_zones:
            log.debug("Router %s was found in availability zone '%s' while the"
                      " OpenStack provider is in zone '%s'",
                      router_id,
                      router.availability_zones,
                      cast("OpenStackCloudProvider", self.provider).service_zone_name(self))
            return None
        return OpenStackRouter(provider, router)

    @dispatch(event="provider.networking.routers.list",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Router]:
        provider = cast("OpenStackCloudProvider", self.provider)
        routers = provider.os_conn.list_routers()
        os_routers = [OpenStackRouter(provider, r) for r in routers
                      if not r.availability_zones or
                      cast("OpenStackCloudProvider", self.provider).service_zone_name(self)
                      in r.availability_zones]
        return ClientPagedResultList(self.provider, os_routers, limit=limit,
                                     marker=marker)

    @dispatch(event="provider.networking.routers.find",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Router]:
        obj_list = list(self)
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    @dispatch(event="provider.networking.routers.create",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, network: Network | str) -> Router:
        """Parameter ``network`` is not used by OpenStack."""
        provider = cast("OpenStackCloudProvider", self.provider)
        router = provider.os_conn.create_router(name=label)
        return OpenStackRouter(provider, router)

    @dispatch(event="provider.networking.routers.delete",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def delete(self, router: Router | str) -> None:
        r_id = router.id if isinstance(router, OpenStackRouter) else router
        provider = cast("OpenStackCloudProvider", self.provider)
        provider.os_conn.delete_router(r_id)


class OpenStackGatewayService(BaseGatewayService):
    """For OpenStack, an internet gateway is a just an 'external' network."""

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackGatewayService, self).__init__(provider)

    @dispatch(event="provider.networking.gateways.get_or_create",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def get_or_create(self, network: Network | str) -> InternetGateway:
        """For OS, inet gtw is any net that has `external` property set."""
        provider = cast("OpenStackCloudProvider", self.provider)
        external_nets = (n for n in self._provider.networking.networks
                         if n.external)
        for net in external_nets:
            if not cast(Any, net).shared:
                return OpenStackInternetGateway(provider, net)
        raise ProviderInternalException(
            "No external, non-shared network is available to serve as an "
            "internet gateway")

    @dispatch(event="provider.networking.gateways.delete",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def delete(self, network: Network | str, gateway: Gateway) -> None:
        pass

    @dispatch(event="provider.networking.gateways.list",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def list(self, network: Network | str, limit: int | None = None,
             marker: str | None = None) -> ResultList[InternetGateway]:
        log.debug("OpenStack listing of all current internet gateways")
        provider = cast("OpenStackCloudProvider", self.provider)
        igl = [OpenStackInternetGateway(provider, n)
               for n in self._provider.networking.networks
               if n.external and not cast(Any, n).shared]
        return ClientPagedResultList(self._provider, igl, limit=limit,
                                     marker=marker)


class OpenStackFloatingIPService(BaseFloatingIPService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackFloatingIPService, self).__init__(provider)

    @dispatch(event="provider.networking.floating_ips.get",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def get(self, gateway: Gateway, fip_id: str) -> FloatingIP | None:
        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            return OpenStackFloatingIP(
                provider,
                provider.os_conn.network.get_ip(fip_id))
        except (ResourceNotFound, NotFoundException):
            log.debug("Floating IP %s not found.", fip_id)
            return None

    @dispatch(event="provider.networking.floating_ips.list",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def list(self, gateway: Gateway, limit: int | None = None,
             marker: str | None = None) -> ResultList[FloatingIP]:
        provider = cast("OpenStackCloudProvider", self.provider)
        fips = [OpenStackFloatingIP(provider, fip)
                for fip in provider.os_conn.network.ips(
                    floating_network_id=gateway.id
                )]
        return ClientPagedResultList(self.provider, fips,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.floating_ips.create",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def create(self, gateway: Gateway) -> FloatingIP:
        provider = cast("OpenStackCloudProvider", self.provider)
        return OpenStackFloatingIP(
            provider, provider.os_conn.network.create_ip(
                floating_network_id=gateway.id))

    @dispatch(event="provider.networking.floating_ips.delete",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def delete(self, gateway: Gateway, fip: FloatingIP | str) -> None:
        provider = cast("OpenStackCloudProvider", self.provider)
        if isinstance(fip, OpenStackFloatingIP):
            # pylint:disable=protected-access
            os_ip = fip._ip
        else:
            try:
                os_ip = provider.os_conn.network.get_ip(fip)
            except (ResourceNotFound, NotFoundException):
                log.debug("Floating IP %s not found.", fip)
                return
        os_ip.delete(provider.os_conn.network)


class OpenStackDnsService(BaseDnsService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackDnsService, self).__init__(provider)

        # Initialize provider services
        self._zone_svc = OpenStackDnsZoneService(self.provider)
        self._record_svc = OpenStackDnsRecordService(self.provider)

    @property
    def host_zones(self) -> OpenStackDnsZoneService:
        return self._zone_svc

    @property
    def _records(self) -> OpenStackDnsRecordService:
        return self._record_svc


class OpenStackDnsZoneService(BaseDnsZoneService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackDnsZoneService, self).__init__(provider)

    @dispatch(event="provider.dns.host_zones.get",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def get(self, dns_zone_id: str) -> DnsZone | None:
        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            return OpenStackDnsZone(
                provider,
                provider.os_conn.dns.get_zone(dns_zone_id))
        except (ResourceNotFound, NotFoundException, BadRequestException):
            log.debug("Dns Zone %s not found.", dns_zone_id)
            return None

    @dispatch(event="provider.dns.host_zones.list",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[DnsZone]:
        provider = cast("OpenStackCloudProvider", self.provider)
        zones = [OpenStackDnsZone(provider, zone)
                 for zone in provider.os_conn.dns.zones()]
        return ClientPagedResultList(self.provider, zones,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.dns.host_zones.find",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[DnsZone]:
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, list(self))
        return ClientPagedResultList(self.provider, list(matches),
                                     limit=None, marker=None)

    @dispatch(event="provider.dns.host_zones.create",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def create(self, name: str, admin_email: str) -> DnsZone:
        OpenStackDnsZone.assert_valid_resource_name(name)

        provider = cast("OpenStackCloudProvider", self.provider)
        return OpenStackDnsZone(
            provider, provider.os_conn.dns.create_zone(
                name=self._get_fully_qualified_dns(name),
                email=admin_email, ttl=3600))

    @dispatch(event="provider.dns.host_zones.delete",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def delete(self, dns_zone: DnsZone | str) -> None:
        zone_id = (dns_zone.id if isinstance(dns_zone, OpenStackDnsZone)
                   else dns_zone)
        if zone_id:
            provider = cast("OpenStackCloudProvider", self.provider)
            provider.os_conn.dns.delete_zone(zone_id)


class OpenStackDnsRecordService(BaseDnsRecordService):

    def __init__(self, provider: CloudProvider) -> None:
        super(OpenStackDnsRecordService, self).__init__(provider)

    def _to_resource_records(self, data: str | builtins.list[str],
                             rec_type: str) -> builtins.list[str]:
        """
        Converts a record to what OpenStack expects. For example,
        OpenStack expects a fully qualified name for all CNAME records.
        """
        if isinstance(data, list):
            records = data
        else:
            records = [data]
        return [self._standardize_record(r, rec_type) for r in records]

    def get(self, dns_zone: DnsZone | str,
            rec_id: str) -> DnsRecord | None:
        provider = cast("OpenStackCloudProvider", self.provider)
        try:
            return OpenStackDnsRecord(
                provider, dns_zone,
                provider.os_conn.dns.get_recordset(
                    rec_id, cast(Any, dns_zone).id))
        except (ResourceNotFound, NotFoundException, BadRequestException):
            log.debug("Dns Record %s not found.", rec_id)
            return None

    # The PageableObjectMixin base declares list(limit, marker); this service
    # intentionally takes a leading dns_zone parameter.
    def list(self,  # type: ignore[override]
             dns_zone: DnsZone | str, limit: int | None = None,
             marker: str | None = None) -> ResultList[DnsRecord]:
        provider = cast("OpenStackCloudProvider", self.provider)
        recs = [OpenStackDnsRecord(provider, dns_zone, rec)
                for rec in provider.os_conn.dns.recordsets(
                    cast(Any, dns_zone).id)]
        return ClientPagedResultList(self.provider, recs,
                                     limit=limit, marker=marker)

    def find(self, dns_zone: DnsZone | str,
             **kwargs: Any) -> ResultList[DnsRecord]:
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs,
                                          cast(Any, dns_zone).records)
        return ClientPagedResultList(self.provider, list(matches),
                                     limit=None, marker=None)

    def create(self, dns_zone: DnsZone | str, name: str, type: str,
               data: str, ttl: int | None = None) -> DnsRecord:
        OpenStackDnsRecord.assert_valid_resource_name(name)

        provider = cast("OpenStackCloudProvider", self.provider)
        return OpenStackDnsRecord(
            provider, dns_zone,
            provider.os_conn.dns.create_recordset(
                zone=cast(Any, dns_zone).id, name=name, type=type,
                records=self._to_resource_records(data, type),
                ttl=ttl or 3600))

    def delete(self, dns_zone: DnsZone | str,
               record: DnsRecord | str) -> None:
        rec_id = (record.id if isinstance(record, OpenStackDnsRecord)
                  else record)
        if rec_id:
            provider = cast("OpenStackCloudProvider", self.provider)
            provider.os_conn.dns.delete_recordset(
                rec_id, zone=cast(Any, dns_zone).id)
