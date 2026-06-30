from __future__ import annotations

import base64
import builtins
import logging
import uuid
from typing import Any
from typing import TYPE_CHECKING
from typing import cast

from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.compute.models import CreationData
from azure.mgmt.compute.models import DataDisk
from azure.mgmt.compute.models import DiskCreateOption
from azure.mgmt.compute.models import HardwareProfile
from azure.mgmt.compute.models import ImageReference
from azure.mgmt.compute.models import LinuxConfiguration
from azure.mgmt.compute.models import ManagedDiskParameters
from azure.mgmt.compute.models import NetworkInterfaceReference
from azure.mgmt.compute.models import NetworkProfile
from azure.mgmt.compute.models import OSDisk
from azure.mgmt.compute.models import OSProfile
from azure.mgmt.compute.models import SshConfiguration
from azure.mgmt.compute.models import SshPublicKey
from azure.mgmt.compute.models import StorageProfile
from azure.mgmt.network.models import AddressSpace
from azure.mgmt.network.models import NetworkInterfaceIPConfiguration
from azure.mgmt.network.models import PublicIPAddressSku
from azure.mgmt.network.models import PublicIPAddressSkuName
from azure.mgmt.network.models import SubResource

import cloudbridge.base.helpers as cb_helpers
from cloudbridge.base.middleware import dispatch
from cloudbridge.base.resources import BaseMultipartUpload
from cloudbridge.base.resources import BaseUploadPart
from cloudbridge.base.resources import ClientPagedResultList
from cloudbridge.base.resources import ServerPagedResultList
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
from cloudbridge.interfaces.exceptions import DuplicateResourceException
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

from .resources import AzureBucket
from .resources import AzureBucketObject
from .resources import AzureDnsRecord
from .resources import AzureDnsZone
from .resources import AzureFloatingIP
from .resources import AzureInstance
from .resources import AzureInternetGateway
from .resources import AzureKeyPair
from .resources import AzureLaunchConfig
from .resources import AzureMachineImage
from .resources import AzureNetwork
from .resources import AzureRegion
from .resources import AzureRouter
from .resources import AzureSnapshot
from .resources import AzureSubnet
from .resources import AzureVMFirewall
from .resources import AzureVMFirewallRule
from .resources import AzureVMType
from .resources import AzureVolume

if TYPE_CHECKING:
    from cloudbridge.interfaces.provider import CloudProvider
    from cloudbridge.providers.azure.provider import AzureCloudProvider

log = logging.getLogger(__name__)


class AzureSecurityService(BaseSecurityService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = AzureKeyPairService(provider)
        self._vm_firewalls = AzureVMFirewallService(provider)
        self._vm_firewall_rule_svc = AzureVMFirewallRuleService(provider)

    @property
    def key_pairs(self) -> AzureKeyPairService:
        return self._key_pairs

    @property
    def vm_firewalls(self) -> AzureVMFirewallService:
        return self._vm_firewalls

    @property
    def _vm_firewall_rules(self) -> AzureVMFirewallRuleService:
        return self._vm_firewall_rule_svc


class AzureVMFirewallService(BaseVMFirewallService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureVMFirewallService, self).__init__(provider)

    @dispatch(event="provider.security.vm_firewalls.get",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_firewall_id: str) -> VMFirewall | None:
        provider = cast("AzureCloudProvider", self.provider)
        try:
            fws = provider.azure_client.get_vm_firewall(vm_firewall_id)
            return AzureVMFirewall(provider, fws)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.security.vm_firewalls.list",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[VMFirewall]:
        provider = cast("AzureCloudProvider", self.provider)
        fws = [AzureVMFirewall(provider, fw)
               for fw in provider.azure_client.list_vm_firewall()]
        return ClientPagedResultList(self.provider, fws, limit, marker)

    @cb_helpers.deprecated_alias(network_id='network')
    @dispatch(event="provider.security.vm_firewalls.create",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, network: Network | str,
               description: str | None = None) -> VMFirewall:
        AzureVMFirewall.assert_valid_resource_label(label)
        name = AzureVMFirewall._generate_name_from_label(label, "cb-fw")
        net = network.id if isinstance(network, Network) else network
        provider = cast("AzureCloudProvider", self.provider)
        parameters: dict[str, Any] = {"location": self.provider.region_name,
                                      "tags": {'Label': label,
                                               'network_id': net}}

        if description:
            parameters['tags'].update(Description=description)

        azure_client = provider.azure_client
        fw = azure_client.create_vm_firewall(name, parameters)

        # Add default rules to negate azure default rules.
        # See: https://github.com/CloudVE/cloudbridge/issues/106
        # pylint:disable=protected-access
        for rule in fw.default_security_rules:
            rule_name = "cb-override-" + rule.name
            # Transpose rules to priority 4001 onwards, because
            # only 0-4096 are allowed for custom rules
            rule.priority = rule.priority - 61440
            rule.access = "Deny"
            azure_client.create_vm_firewall_rule(
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
        result = azure_client.create_vm_firewall_rule(
            fw.id, "cb-default-internet-outbound", parameters)
        fw.security_rules.append(result)

        cb_fw = AzureVMFirewall(provider, fw)
        return cb_fw

    @dispatch(event="provider.security.vm_firewalls.delete",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def delete(self, vm_firewall: VMFirewall | str) -> None:
        fw_id = (vm_firewall.id if isinstance(vm_firewall, AzureVMFirewall)
                 else vm_firewall)
        cast("AzureCloudProvider", self.provider).azure_client.\
            delete_vm_firewall(fw_id)


class AzureVMFirewallRuleService(BaseVMFirewallRuleService):

    def __init__(self, provider: CloudProvider) -> None:
        super(AzureVMFirewallRuleService, self).__init__(provider)

    @dispatch(event="provider.security.vm_firewall_rules.list",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def list(self, firewall: VMFirewall, limit: int | None = None,
             marker: str | None = None) -> ResultList[VMFirewallRule]:
        # Filter out firewall rules with priority < 3500 because values
        # between 3500 and 4096 are assumed to be owned by cloudbridge
        # default rules.
        # pylint:disable=protected-access
        rules = [AzureVMFirewallRule(firewall, rule) for rule
                 in cast(Any, firewall)._vm_firewall.security_rules
                 if rule.priority < 3500]
        return ClientPagedResultList(self.provider, rules,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.security.vm_firewall_rules.create",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def create(self, firewall: VMFirewall, direction: TrafficDirection,
               protocol: str | None = None, from_port: int | None = None,
               to_port: int | None = None, cidr: str | None = None,
               src_dest_fw: VMFirewall | None = None) -> VMFirewallRule:
        if protocol and from_port and to_port:
            return self._create_rule(firewall, direction, protocol, from_port,
                                     to_port, cidr)
        elif src_dest_fw:
            result = None
            fw = (self.provider.security.vm_firewalls.get(src_dest_fw)
                  if isinstance(src_dest_fw, str) else src_dest_fw)
            if fw is None:
                raise ProviderInternalException(
                    "Source firewall %s not found" % src_dest_fw)
            for rule in fw.rules:
                result = self._create_rule(
                    firewall, rule.direction, cast(str, rule.protocol),
                    rule.from_port, rule.to_port, rule.cidr)
            if result is None:
                raise ProviderInternalException(
                    "Source firewall %s has no rules to copy" % src_dest_fw)
            return result
        else:
            raise InvalidParamException(
                "Either (protocol, from_port, to_port) or src_dest_fw "
                "must be provided to create a firewall rule")

    def _create_rule(self, firewall: VMFirewall, direction: TrafficDirection,
                     protocol: str, from_port: int, to_port: int,
                     cidr: str | None) -> AzureVMFirewallRule:

        # If cidr is None, default values is set as 0.0.0.0/0
        if not cidr:
            cidr = '0.0.0.0/0'

        count = len(cast(Any, firewall)._vm_firewall.security_rules) + 1
        rule_name = "cb-rule-" + str(count)
        priority = 1000 + count
        destination_port_range = str(from_port) + "-" + str(to_port)
        source_port_range = '*'
        destination_address_prefix = "*"
        access = "Allow"
        az_direction = ("Inbound" if direction == TrafficDirection.INBOUND
                        else "Outbound")
        parameters = {"priority": priority,
                      "protocol": protocol,
                      "source_port_range": source_port_range,
                      "source_address_prefix": cidr,
                      "destination_port_range": destination_port_range,
                      "destination_address_prefix": destination_address_prefix,
                      "access": access,
                      "direction": az_direction}
        result = cast("AzureCloudProvider", self.provider).azure_client. \
            create_vm_firewall_rule(firewall.id,
                                    rule_name, parameters)
        # pylint:disable=protected-access
        cast(Any, firewall)._vm_firewall.security_rules.append(result)
        return AzureVMFirewallRule(firewall, result)

    @dispatch(event="provider.security.vm_firewall_rules.delete",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def delete(self, firewall: VMFirewall, rule: VMFirewallRule) -> None:
        rule_id = rule.id if isinstance(rule, AzureVMFirewallRule) else rule
        fw_name = firewall.name
        cast("AzureCloudProvider", self.provider).azure_client. \
            delete_vm_firewall_rule(rule_id, fw_name)
        for i, o in enumerate(cast(Any, firewall)._vm_firewall.security_rules):
            if o.id == rule_id:
                # pylint:disable=protected-access
                del cast(Any, firewall)._vm_firewall.security_rules[i]
                break


class AzureKeyPairService(BaseKeyPairService):
    PARTITION_KEY = '00000000-0000-0000-0000-000000000000'

    def __init__(self, provider: CloudProvider) -> None:
        super(AzureKeyPairService, self).__init__(provider)

    @dispatch(event="provider.security.key_pairs.get",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def get(self, key_pair_id: str) -> KeyPair | None:
        provider = cast("AzureCloudProvider", self.provider)
        try:
            key_pair = provider.azure_client.get_public_key(key_pair_id)

            if key_pair:
                return AzureKeyPair(provider, key_pair)
            return None
        except ResourceNotFoundError as error:
            log.debug("KeyPair %s was not found.", key_pair_id)
            log.debug(error)
            return None

    @dispatch(event="provider.security.key_pairs.list",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[KeyPair]:
        provider = cast("AzureCloudProvider", self.provider)
        key_pairs, resume_marker = provider.azure_client.list_public_keys(
            AzureKeyPairService.PARTITION_KEY, marker=marker,
            limit=limit or self.provider.config.default_result_limit)
        results = [AzureKeyPair(provider, key_pair)
                   for key_pair in key_pairs]
        return ServerPagedResultList(is_truncated=resume_marker,
                                     marker=resume_marker,
                                     supports_total=False,
                                     data=results)

    @dispatch(event="provider.security.key_pairs.find",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[KeyPair]:
        obj_list: list[KeyPair] = list(self)
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    @dispatch(event="provider.security.key_pairs.create",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def create(self, name: str,
               public_key_material: str | None = None) -> KeyPair:
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

        cast("AzureCloudProvider", self.provider).azure_client.\
            create_public_key(entity)
        key_pair = self.get(name)
        if key_pair is None:
            raise ProviderInternalException(
                "KeyPair %s could not be retrieved after creation" % name)
        key_pair.material = private_key
        return key_pair

    @dispatch(event="provider.security.key_pairs.delete",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def delete(self, key_pair: KeyPair | str) -> None:
        kp = (key_pair if isinstance(key_pair, AzureKeyPair) else
              self.get(key_pair))
        if kp:
            # pylint:disable=protected-access
            cast("AzureCloudProvider", self.provider).azure_client.\
                delete_public_key(cast(Any, kp)._key_pair)


class AzureStorageService(BaseStorageService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureStorageService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = AzureVolumeService(self.provider)
        self._snapshot_svc = AzureSnapshotService(self.provider)
        self._bucket_svc = AzureBucketService(self.provider)
        self._bucket_obj_svc = AzureBucketObjectService(self.provider)

    @property
    def volumes(self) -> AzureVolumeService:
        return self._volume_svc

    @property
    def snapshots(self) -> AzureSnapshotService:
        return self._snapshot_svc

    @property
    def buckets(self) -> AzureBucketService:
        return self._bucket_svc

    @property
    def _bucket_objects(self) -> AzureBucketObjectService:
        return self._bucket_obj_svc


class AzureVolumeService(BaseVolumeService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureVolumeService, self).__init__(provider)

    @dispatch(event="provider.storage.volumes.get",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def get(self, volume_id: str) -> Volume | None:
        provider = cast("AzureCloudProvider", self.provider)
        try:
            volume = provider.azure_client.get_disk(volume_id)
            return AzureVolume(provider, volume)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.storage.volumes.find",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Volume]:
        obj_list: list[Volume] = list(self)
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    @dispatch(event="provider.storage.volumes.list",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Volume]:
        provider = cast("AzureCloudProvider", self.provider)
        azure_vols = provider.azure_client.list_disks()
        cb_vols = [AzureVolume(provider, vol) for vol in azure_vols]
        return ClientPagedResultList(self.provider, cb_vols,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.storage.volumes.create",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, size: int,
               snapshot: Snapshot | str | None = None,
               description: str | None = None) -> Volume:
        AzureVolume.assert_valid_resource_label(label)
        disk_name = AzureVolume._generate_name_from_label(label, "cb-vol")
        tags = {'Label': label}

        snapshot = (self.provider.storage.snapshots.get(snapshot)
                    if snapshot and isinstance(snapshot, str) else snapshot)

        if description:
            tags.update(Description=description)

        provider = cast("AzureCloudProvider", self.provider)
        azure_client = provider.azure_client
        params: dict[str, Any]
        if snapshot:
            params = {
                'location': self.provider.region_name,
                'creation_data': CreationData(
                    create_option=cast(Any, DiskCreateOption.copy),
                    source_uri=cast(Any, snapshot).resource_id,
                ),
                'tags': tags
            }

            disk = azure_client.create_snapshot_disk(disk_name, params)

        else:
            params = {
                'location': self.provider.region_name,
                'disk_size_gb': size,
                'creation_data': CreationData(
                    create_option=cast(Any, DiskCreateOption.empty),
                ),
                'tags': tags
            }

            disk = azure_client.create_empty_disk(disk_name, params)

        azure_vol = azure_client.get_disk(disk.id)
        cb_vol = AzureVolume(provider, azure_vol)

        return cb_vol

    @dispatch(event="provider.storage.volumes.delete",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def delete(self, volume: Volume | str) -> None:
        vol_id = (volume.id if isinstance(volume, AzureVolume)
                  else volume)
        cast("AzureCloudProvider", self.provider).azure_client.\
            delete_disk(vol_id)


class AzureSnapshotService(BaseSnapshotService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureSnapshotService, self).__init__(provider)

    @dispatch(event="provider.storage.snapshots.get",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def get(self, snapshot_id: str) -> Snapshot | None:
        provider = cast("AzureCloudProvider", self.provider)
        try:
            snapshot = provider.azure_client.get_snapshot(snapshot_id)
            return AzureSnapshot(provider, snapshot)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.storage.snapshots.find",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Snapshot]:
        obj_list: list[Snapshot] = list(self)
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    @dispatch(event="provider.storage.snapshots.list",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Snapshot]:
        provider = cast("AzureCloudProvider", self.provider)
        snaps = [AzureSnapshot(provider, obj)
                 for obj in provider.azure_client.list_snapshots()]
        return ClientPagedResultList(self.provider, snaps, limit, marker)

    @dispatch(event="provider.storage.snapshots.create",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, volume: Volume | str,
               description: str | None = None) -> Snapshot:
        AzureSnapshot.assert_valid_resource_label(label)
        snapshot_name = AzureSnapshot._generate_name_from_label(label,
                                                                "cb-snap")
        tags = {'Label': label}
        if description:
            tags.update(Description=description)

        vol = (self.provider.storage.volumes.get(volume)
               if isinstance(volume, str) else volume)

        # We need to pass the Disk Object to create the snapshot
        azure_volume = cast(Any, vol)._volume

        provider = cast("AzureCloudProvider", self.provider)
        azure_snap = provider.azure_client.create_snapshot(
            snapshot_name, azure_volume, tags)

        return AzureSnapshot(provider, azure_snap)

    @dispatch(event="provider.storage.snapshots.delete",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def delete(self, snapshot: Snapshot | str) -> None:
        snap_id = (snapshot.id if isinstance(snapshot, AzureSnapshot)
                   else snapshot)
        cast("AzureCloudProvider", self.provider).azure_client.\
            delete_snapshot(snap_id)


class AzureBucketService(BaseBucketService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureBucketService, self).__init__(provider)

    @dispatch(event="provider.storage.buckets.get",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def get(self, bucket_id: str) -> Bucket | None:
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        provider = cast("AzureCloudProvider", self.provider)
        bucket = provider.azure_client.get_container(bucket_id)
        if bucket.exists():
            return AzureBucket(provider, bucket)
        else:
            return None

    @dispatch(event="provider.storage.buckets.list",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Bucket]:
        provider = cast("AzureCloudProvider", self.provider)
        buckets = [AzureBucket(provider, bucket)
                   for bucket
                   in provider.azure_client.list_containers()]
        return ClientPagedResultList(self.provider, buckets,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.storage.buckets.create",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def create(self, name: str,
               location: Region | str | None = None) -> Bucket:
        """
        Create a new bucket.
        """
        AzureBucket.assert_valid_resource_name(name)
        provider = cast("AzureCloudProvider", self.provider)
        bucket = provider.azure_client.create_container(name)
        return AzureBucket(provider, bucket)

    @dispatch(event="provider.storage.buckets.delete",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def delete(self, bucket: Bucket | str) -> None:
        """
        Delete this bucket.
        """
        b_id = bucket.id if isinstance(bucket, AzureBucket) else bucket
        cast("AzureCloudProvider", self.provider).azure_client.\
            delete_container(b_id)


class AzureBucketObjectService(BaseBucketObjectService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureBucketObjectService, self).__init__(provider)

    def get(self, bucket: Bucket | str,
            object_id: str) -> BucketObject | None:
        """
        Retrieve a given object from this bucket.
        """
        provider = cast("AzureCloudProvider", self.provider)
        azure_bucket = cast("AzureBucket", bucket)
        try:
            # pylint:disable=protected-access
            obj = cast(Any, bucket)._bucket.get_blob_client(
                object_id).get_blob_properties()
            return AzureBucketObject(provider, azure_bucket, obj)
        except ResourceNotFoundError as azureEx:
            log.exception(azureEx)
            return None

    def list(self, bucket: Bucket | str, prefix: str | None = None,
             limit: int | None = None,
             marker: str | None = None) -> ResultList[BucketObject]:
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        provider = cast("AzureCloudProvider", self.provider)
        azure_bucket = cast("AzureBucket", bucket)
        objects = [AzureBucketObject(provider, azure_bucket, obj)
                   for obj in
                   cast(Any, bucket)._bucket.list_blobs(
                       name_starts_with=prefix)]
        return ClientPagedResultList(self.provider, objects,
                                     limit=limit, marker=marker)

    def find(self, bucket: Bucket | str,
             **kwargs: Any) -> ResultList[BucketObject]:
        provider = cast("AzureCloudProvider", self.provider)
        azure_bucket = cast("AzureBucket", bucket)
        obj_list = [AzureBucketObject(provider, azure_bucket, obj)
                    for obj in
                    cast(Any, bucket)._bucket.list_blobs()]
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self.provider, list(matches))

    def create(self, bucket: Bucket | str, name: str) -> BucketObject:
        provider = cast("AzureCloudProvider", self.provider)
        azure_bucket = cast("AzureBucket", bucket)
        blob_client = cast(Any, bucket)._bucket.get_blob_client(name)
        blob_client.upload_blob('')
        return AzureBucketObject(provider, azure_bucket,
                                 blob_client.get_blob_properties())

    @staticmethod
    def _block_id(upload_id: str, part_number: int) -> str:
        # Azure requires every block id for a blob to be the same length and
        # base64-encoded. The upload id is a fixed-length uuid hex, so the
        # encoded ids are always equal length.
        raw = "{0}-{1:08d}".format(upload_id, part_number)
        return base64.b64encode(raw.encode()).decode()

    @dispatch(event="provider.storage._bucket_objects.create_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def create_multipart_upload(self, bucket: Bucket | str,
                                object_name: str) -> MultipartUpload:
        # Azure block blobs have no server-side "initiate" step; the upload id
        # only namespaces this upload's block ids.
        return BaseMultipartUpload(self.provider, cast("Bucket", bucket),
                                   object_name, uuid.uuid4().hex)

    @dispatch(event="provider.storage._bucket_objects.upload_part",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def upload_part(self, bucket: Bucket | str, upload: MultipartUpload,
                    part_number: int, data: Any) -> UploadPart:
        block_id = self._block_id(upload.id, part_number)
        cast("AzureCloudProvider", self.provider).azure_client.stage_block(
            cast("Bucket", bucket).name, upload.object_name, block_id, data)
        return BaseUploadPart(part_number, block_id)

    @dispatch(event="provider.storage._bucket_objects."
                    "complete_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def complete_multipart_upload(self, bucket: Bucket | str,
                                  upload: MultipartUpload,
                                  parts: builtins.list[UploadPart]
                                  ) -> BucketObject:
        ordered = sorted(parts, key=lambda p: p.part_number)
        cast("AzureCloudProvider", self.provider).azure_client.\
            commit_block_list(
                cast("Bucket", bucket).name, upload.object_name,
                [p.etag for p in ordered])
        obj = self.get(bucket, upload.object_name)
        if obj is None:
            raise ProviderInternalException(
                "Object %s not found after completing multipart upload"
                % upload.object_name)
        return obj

    @dispatch(event="provider.storage._bucket_objects.abort_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def abort_multipart_upload(self, bucket: Bucket | str,
                               upload: MultipartUpload) -> None:
        # Azure has no server-side abort: uncommitted blocks are garbage
        # collected automatically (after ~7 days), so there is nothing to do.
        log.debug("Azure has no multipart abort; uncommitted blocks for "
                  "%s/%s will expire automatically.",
                  cast("Bucket", bucket).name, upload.object_name)


class AzureComputeService(BaseComputeService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureComputeService, self).__init__(provider)
        self._vm_type_svc = AzureVMTypeService(self.provider)
        self._instance_svc = AzureInstanceService(self.provider)
        self._region_svc = AzureRegionService(self.provider)
        self._images_svc = AzureImageService(self.provider)

    @property
    def images(self) -> AzureImageService:
        return self._images_svc

    @property
    def vm_types(self) -> AzureVMTypeService:
        return self._vm_type_svc

    @property
    def instances(self) -> AzureInstanceService:
        return self._instance_svc

    @property
    def regions(self) -> AzureRegionService:
        return self._region_svc


class AzureImageService(BaseImageService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureImageService, self).__init__(provider)

    def get(self, image_id: str) -> MachineImage | None:
        """
        Returns an Image given its id
        """
        provider = cast("AzureCloudProvider", self.provider)
        try:
            image = provider.azure_client.get_image(image_id)
            return AzureMachineImage(provider, image)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    def find(self, **kwargs: Any) -> ResultList[MachineImage]:
        obj_list: builtins.list[MachineImage] = list(self)
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    def list(self,  # type: ignore[override]
             filter_by_owner: bool = True, limit: int | None = None,
             marker: str | None = None) -> ResultList[MachineImage]:
        # Intentional arguments-differ: image listing accepts a leading
        # filter_by_owner flag ahead of the base list(limit, marker).
        """
        List all images.
        """
        provider = cast("AzureCloudProvider", self.provider)
        azure_client = provider.azure_client
        azure_images = azure_client.list_images()
        azure_gallery_refs = azure_client.list_gallery_refs() \
            if not filter_by_owner else []
        cb_images = [AzureMachineImage(provider, img)
                     for img in azure_images + azure_gallery_refs]
        return ClientPagedResultList(self.provider, cb_images,
                                     limit=limit, marker=marker)


class AzureInstanceService(BaseInstanceService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureInstanceService, self).__init__(provider)

    def _resolve_launch_options(
            self, inst_name: str, subnet: Subnet | None = None,
            zone_id: str | None = None,
            vm_firewalls: builtins.list[VMFirewall | str] | None = None
    ) -> tuple[Any, str | None, Any]:
        if subnet:
            # subnet's zone takes precedence
            zone_id = cast(Any, subnet.zone).id
        vm_firewall_id = None

        if isinstance(vm_firewalls, list) and len(vm_firewalls) > 0:

            if isinstance(vm_firewalls[0], VMFirewall):
                vm_firewalls_ids = [cast(Any, fw).id for fw in vm_firewalls]
                vm_firewall_id = cast(Any, vm_firewalls[0]).resource_id
            else:
                vm_firewalls_ids = vm_firewalls
                vm_firewall = self.provider.security.\
                    vm_firewalls.get(vm_firewalls[0])
                vm_firewall_id = cast(Any, vm_firewall).resource_id

            if len(vm_firewalls) > 1:
                # FLAGGED FOR REVIEW: this create() omits the required
                # ``network`` argument (pre-existing bug); cast to Any so the
                # missing-arg is not masked by a fabricated value here.
                new_fw = cast(Any, self.provider.security.vm_firewalls).\
                    create(label='{0}-fw'.format(inst_name),
                           description='Merge vm firewall {0}'.
                           format(','.join(cast(Any, vm_firewalls_ids))))

                for fw in vm_firewalls:
                    cast(Any, new_fw).add_rule(src_dest_fw=fw)

                vm_firewall_id = cast(Any, new_fw).resource_id

        return cast(Any, subnet).resource_id, zone_id, vm_firewall_id

    def _create_storage_profile(self, image: MachineImage,
                                launch_config: LaunchConfig | None,
                                instance_name: str) -> StorageProfile:

        if cast(Any, image).is_gallery_image:
            # pylint:disable=protected-access
            reference = cast(Any, image)._image.as_dict()
            image_ref = ImageReference(
                publisher=reference['publisher'],
                offer=reference['offer'],
                sku=reference['sku'],
                version=reference['version'],
            )
        else:
            image_ref = ImageReference(id=cast(Any, image).resource_id)

        os_disk = OSDisk(
            name=instance_name + '_os_disk',
            create_option=cast(Any, DiskCreateOption.from_image),
        )

        data_disks = None
        if launch_config:
            data_disks, root_disk_size = self._process_block_device_mappings(
                launch_config)
            if root_disk_size:
                os_disk.disk_size_gb = root_disk_size

        return StorageProfile(
            image_reference=image_ref,
            os_disk=os_disk,
            data_disks=data_disks or None,
        )

    def _process_block_device_mappings(
            self, launch_config: LaunchConfig
    ) -> tuple[builtins.list[Any], int | None]:
        """
        Processes block device mapping information
        and returns a DataDisk model list. If new volumes
        are requested (source is None and destination is VOLUME), they will be
        created and the relevant volume ids included in the mapping.
        """
        data_disks: builtins.list[Any] = []
        root_disk_size = None

        def append_disk(disk_kwargs: dict[str, Any], device_no: int,
                        delete_on_terminate: bool,
                        managed_disk_id: str | None = None) -> None:
            # Azure has no direct equivalent of AWS' delete_on_terminate, so
            # the cleanup tag is recorded on the parent VM later; we just
            # carry the flag (and the disk id) alongside the DataDisk model.
            disk = DataDisk(lun=device_no, **disk_kwargs)
            # Stash cloudbridge-only bookkeeping on the SDK model instance.
            cast(Any, disk)._cb_delete_on_terminate = delete_on_terminate
            cast(Any, disk)._cb_managed_disk_id = managed_disk_id
            data_disks.append(disk)

        for device_no, device in enumerate(cast(Any,
                                                launch_config).block_devices):
            if device.is_volume:
                if device.is_root:
                    root_disk_size = device.size
                else:
                    # In azure, os disk automatically created,
                    # we are ignoring the root disk, if specified
                    if isinstance(device.source, Snapshot):
                        snapshot_vol = device.source.create_volume()
                        disk_kwargs = {
                            # pylint:disable=protected-access
                            'name': cast(Any, snapshot_vol)._volume.name,
                            'create_option': DiskCreateOption.attach,
                            'managed_disk': ManagedDiskParameters(
                                id=snapshot_vol.id),
                        }
                        append_disk(disk_kwargs, device_no,
                                    device.delete_on_terminate,
                                    managed_disk_id=snapshot_vol.id)
                        continue
                    elif isinstance(device.source, Volume):
                        disk_kwargs = {
                            # pylint:disable=protected-access
                            'name': cast(Any, device.source)._volume.name,
                            'create_option': DiskCreateOption.attach,
                            'managed_disk': ManagedDiskParameters(
                                id=device.source.id),
                        }
                        append_disk(disk_kwargs, device_no,
                                    device.delete_on_terminate,
                                    managed_disk_id=device.source.id)
                        continue
                    elif isinstance(device.source, MachineImage):
                        disk_kwargs = {
                            # pylint:disable=protected-access
                            'name': cast(Any, device.source)._volume.name,
                            'create_option': DiskCreateOption.from_image,
                            'source_resource_id': device.source.id,
                        }
                    else:
                        disk_kwargs = {
                            'create_option': DiskCreateOption.empty,
                            'disk_size_gb': device.size,
                        }
                    append_disk(disk_kwargs, device_no,
                                device.delete_on_terminate)
            else:  # device is ephemeral
                # in azure we cannot add the ephemeral disks explicitly
                pass

        return data_disks, root_disk_size

    def create_launch_config(self) -> LaunchConfig:
        return AzureLaunchConfig(cast("AzureCloudProvider", self.provider))

    @dispatch(event="provider.compute.instances.create",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, image: MachineImage | str,
               vm_type: VMType | str, subnet: Subnet | str,
               key_pair: KeyPair | str | None = None,
               vm_firewalls: list[VMFirewall | str] | None = None,
               user_data: str | None = None,
               launch_config: LaunchConfig | None = None,
               **kwargs: Any) -> Instance:
        AzureInstance.assert_valid_resource_label(label)
        instance_name = AzureInstance._generate_name_from_label(label,
                                                                "cb-ins")

        cb_image = (image if isinstance(image, AzureMachineImage) else
                    self.provider.compute.images.get(cast(str, image)))
        if not isinstance(cb_image, AzureMachineImage):
            raise Exception("Provided image %s is not a valid azure image"
                            % image)

        instance_size = vm_type.id if \
            isinstance(vm_type, VMType) else vm_type

        cb_subnet: Subnet | None
        if subnet:
            cb_subnet = (subnet if isinstance(subnet, AzureSubnet) else
                         self.provider.networking.subnets.get(
                             cast(str, subnet)))
        else:
            cb_subnet = cast(
                Any,
                self.provider.networking.subnets).get_or_create_default()

        zone_name = self.provider.zone_name

        subnet_id, zone_id, vm_firewall_id = \
            self._resolve_launch_options(instance_name,
                                         cb_subnet, zone_name, vm_firewalls)

        storage_profile = self._create_storage_profile(cb_image, launch_config,
                                                       instance_name)

        azure_client = cast("AzureCloudProvider", self.provider).azure_client
        nic_params: dict[str, Any] = {
            'location': self.provider.region_name,
            'ip_configurations': [NetworkInterfaceIPConfiguration(
                name=instance_name + '_ip_config',
                private_ip_allocation_method='Dynamic',
                subnet=cast(Any, SubResource(id=subnet_id)),
            )],
        }

        if vm_firewall_id:
            nic_params['network_security_group'] = SubResource(
                id=vm_firewall_id)
        nic_info = azure_client.create_nic(
            instance_name + '_nic',
            nic_params
        )
        # #! indicates shell script
        ud = '#cloud-config\n' + user_data \
            if user_data and not user_data.startswith('#!')\
            and not user_data.startswith('#cloud-config') else user_data

        # Key_pair is mandatory in azure and it should not be None.
        temp_key_pair = None
        cb_key_pair: KeyPair | None
        if key_pair:
            cb_key_pair = (key_pair if isinstance(key_pair, AzureKeyPair)
                           else self.provider.security.key_pairs.get(
                               cast(str, key_pair)))
        else:
            # Create a temporary keypair if none is provided to keep Azure
            # happy, but the private key will be discarded, so it'll be all
            # but useless. However, this will allow an instance to be launched
            # without specifying a keypair, so users may still be able to login
            # if they have a preinstalled keypair/password baked into the image
            temp_kp_name = "".join(["cb-default-kp-",
                                   str(uuid.uuid5(uuid.NAMESPACE_OID,
                                                  instance_name))[-6:]])
            cb_key_pair = self.provider.security.key_pairs.create(
                name=temp_kp_name)
            temp_key_pair = cb_key_pair

        os_profile = OSProfile(
            admin_username=cast(
                "AzureCloudProvider", self.provider).vm_default_user_name,
            computer_name=instance_name,
            linux_configuration=LinuxConfiguration(
                disable_password_authentication=True,
                ssh=SshConfiguration(public_keys=[SshPublicKey(
                    path="/home/{}/.ssh/authorized_keys".format(
                        cast("AzureCloudProvider",
                             self.provider).vm_default_user_name),
                    key_data=cast(Any, cb_key_pair)._key_pair['Key'],
                )]),
            ),
        )

        tags: dict[str, Any] = {'Label': label}
        # Surface each data disk's delete-on-terminate flag onto the parent
        # VM tags so the VM-delete path can later clean them up.
        for disk in (storage_profile.data_disks or []):
            tags['delete_on_terminate'] = getattr(
                disk, '_cb_delete_on_terminate', False)

        params: dict[str, Any] = {
            'location': zone_id,
            'os_profile': os_profile,
            'hardware_profile': HardwareProfile(vm_size=instance_size),
            'network_profile': NetworkProfile(
                network_interfaces=[NetworkInterfaceReference(
                    id=nic_info.id)],
            ),
            'storage_profile': storage_profile,
            'tags': tags,
        }

        if user_data:
            custom_data = base64.b64encode(bytes(cast(str, ud), 'utf-8'))
            params['os_profile'].custom_data = str(custom_data, 'utf-8')

        if not temp_key_pair:
            params['tags'].update(Key_Pair=cast(Any, cb_key_pair).id)

        try:
            vm = azure_client.create_vm(instance_name, params)
        except Exception as e:
            # If VM creation fails, attempt to clean up intermediary resources
            azure_client.delete_nic(nic_info.id)
            for disk in (storage_profile.data_disks or []):
                if getattr(disk, '_cb_delete_on_terminate', False):
                    disk_id = getattr(disk, '_cb_managed_disk_id', None)
                    if disk_id:
                        vol = self.provider.storage.volumes.get(disk_id)
                        if vol:
                            vol.delete()
            raise e
        finally:
            if temp_key_pair:
                temp_key_pair.delete()
        return AzureInstance(cast("AzureCloudProvider", self.provider), vm)

    @dispatch(event="provider.compute.instances.list",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Instance]:
        """
        List all instances.
        """
        provider = cast("AzureCloudProvider", self.provider)
        instances = [AzureInstance(provider, inst)
                     for inst in provider.azure_client.list_vm()]
        return ClientPagedResultList(self.provider, instances,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.compute.instances.get",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def get(self, instance_id: str) -> Instance | None:
        """
        Returns an instance given its id. Returns None
        if the object does not exist.
        """
        provider = cast("AzureCloudProvider", self.provider)
        try:
            vm = provider.azure_client.get_vm(instance_id)
            return AzureInstance(provider, vm)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.compute.instances.find",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Instance]:
        obj_list: builtins.list[Instance] = list(self)
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    @dispatch(event="provider.compute.instances.delete",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def delete(self, instance: Instance | str) -> None:
        """
        Permanently terminate this instance.
        After deleting the VM. we are deleting the network interface
        associated to the instance, and also removing OS disk and data disks
        where tag with name 'delete_on_terminate' has value True.
        """
        ins = (instance if isinstance(instance, AzureInstance) else
               self.get(cast(str, instance)))
        if not ins:
            return

        azure_client = cast("AzureCloudProvider", self.provider).azure_client
        # Remove IPs first to avoid a network interface conflict
        # pylint:disable=protected-access
        for public_ip_id in cast(Any, ins)._public_ip_ids:
            ins.remove_floating_ip(public_ip_id)
        azure_client.deallocate_vm(ins.id)
        azure_client.delete_vm(ins.id)
        # pylint:disable=protected-access
        for nic_id in cast(Any, ins)._nic_ids:
            azure_client.delete_nic(nic_id)
        # pylint:disable=protected-access
        for data_disk in cast(Any, ins)._vm.storage_profile.data_disks:
            if data_disk.managed_disk:
                # pylint:disable=protected-access
                if cast(Any, ins)._vm.tags.get('delete_on_terminate',
                                               'False') == 'True':
                    azure_client.delete_disk(data_disk.managed_disk.id)
        # pylint:disable=protected-access
        if cast(Any, ins)._vm.storage_profile.os_disk.managed_disk:
            azure_client.delete_disk(
                cast(Any, ins)._vm.storage_profile.os_disk.managed_disk.id)


class AzureVMTypeService(BaseVMTypeService):

    def __init__(self, provider: CloudProvider) -> None:
        super(AzureVMTypeService, self).__init__(provider)

    @property
    def instance_data(self) -> Any:
        """
        Fetch info about the available instances.
        """
        r = cast("AzureCloudProvider", self.provider).azure_client.\
            list_vm_types()
        return r

    @dispatch(event="provider.compute.vm_types.list",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[VMType]:
        provider = cast("AzureCloudProvider", self.provider)
        vm_types = [AzureVMType(provider, vm_type)
                    for vm_type in self.instance_data]
        return ClientPagedResultList(self.provider, vm_types,
                                     limit=limit, marker=marker)


class AzureRegionService(BaseRegionService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureRegionService, self).__init__(provider)

    @dispatch(event="provider.compute.regions.get",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def get(self, region_id: str) -> Region | None:
        provider = cast("AzureCloudProvider", self.provider)
        region = None
        for azureRegion in provider.azure_client.list_locations():
            if azureRegion.name == region_id:
                region = AzureRegion(provider, azureRegion)
                break
        return region

    @dispatch(event="provider.compute.regions.list",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Region]:
        provider = cast("AzureCloudProvider", self.provider)
        regions = [AzureRegion(provider, region)
                   for region in provider.azure_client.list_locations()]
        return ClientPagedResultList(self.provider, regions,
                                     limit=limit, marker=marker)

    @property
    def current(self) -> Region | None:
        return self.get(self.provider.region_name)


class AzureNetworkingService(BaseNetworkingService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureNetworkingService, self).__init__(provider)
        self._network_service = AzureNetworkService(self.provider)
        self._subnet_service = AzureSubnetService(self.provider)
        self._router_service = AzureRouterService(self.provider)
        self._gateway_service = AzureGatewayService(self.provider)
        self._floating_ip_service = AzureFloatingIPService(self.provider)

    @property
    def networks(self) -> AzureNetworkService:
        return self._network_service

    @property
    def subnets(self) -> AzureSubnetService:
        return self._subnet_service

    @property
    def routers(self) -> AzureRouterService:
        return self._router_service

    @property
    def _gateways(self) -> AzureGatewayService:
        return self._gateway_service

    @property
    def _floating_ips(self) -> AzureFloatingIPService:
        return self._floating_ip_service


class AzureNetworkService(BaseNetworkService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureNetworkService, self).__init__(provider)

    @dispatch(event="provider.networking.networks.get",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def get(self, network_id: str) -> Network | None:
        provider = cast("AzureCloudProvider", self.provider)
        try:
            network = provider.azure_client.get_network(network_id)
            return AzureNetwork(provider, network)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.networking.networks.list",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Network]:
        provider = cast("AzureCloudProvider", self.provider)
        networks = [AzureNetwork(provider, network)
                    for network in provider.azure_client.list_networks()]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.networks.create",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, cidr_block: str) -> Network:
        AzureNetwork.assert_valid_resource_label(label)
        provider = cast("AzureCloudProvider", self.provider)
        azure_client = provider.azure_client
        params = {
            'location': azure_client.region_name,
            'address_space': AddressSpace(
                address_prefixes=[cidr_block]),
            'tags': {'Label': label}
        }

        network_name = AzureNetwork._generate_name_from_label(label, 'cb-net')

        az_network = azure_client.create_network(network_name, params)
        cb_network = AzureNetwork(provider, az_network)
        return cb_network

    @dispatch(event="provider.networking.networks.delete",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def delete(self, network: Network | str) -> None:
        net_id = network.id if isinstance(network, AzureNetwork) else network
        if net_id:
            cast("AzureCloudProvider", self.provider).azure_client.\
                delete_network(net_id)


class AzureSubnetService(BaseSubnetService):

    def __init__(self, provider: CloudProvider) -> None:
        super(AzureSubnetService, self).__init__(provider)

    def _list_subnets(
            self, network: Network | str | None = None
    ) -> builtins.list[AzureSubnet]:
        result_list = []
        provider = cast("AzureCloudProvider", self.provider)
        azure_client = provider.azure_client
        if network:
            network_id = network.id \
                if isinstance(network, Network) else network
            result_list = azure_client.list_subnets(network_id)
        else:
            for net in self.provider.networking.networks:
                try:
                    result_list.extend(azure_client.list_subnets(
                        net.id
                    ))
                except ResourceNotFoundError as not_found_error:
                    log.exception(not_found_error)
        subnets = [AzureSubnet(provider, subnet)
                   for subnet in result_list]

        return subnets

    @dispatch(event="provider.networking.subnets.get",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def get(self, subnet_id: str) -> Subnet | None:
        """
         Azure does not provide an api to get the subnet directly by id.
         It also requires the network id.
         To make it consistent across the providers the following code
         gets the specific code from the subnet list.
        """
        provider = cast("AzureCloudProvider", self.provider)
        try:
            azure_subnet = provider.azure_client.get_subnet(subnet_id)
            return AzureSubnet(provider,
                               azure_subnet) if azure_subnet else None
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.networking.subnets.list",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def list(self, network: Network | str | None = None,
             limit: int | None = None,
             marker: str | None = None) -> ResultList[Subnet]:
        # The base SubnetService.list already accepts a leading network
        # filter ahead of list(limit, marker).
        return ClientPagedResultList(self.provider,
                                     self._list_subnets(network),
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.subnets.find",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def find(self, network: Network | None = None,
             **kwargs: Any) -> ResultList[Subnet]:
        obj_list = self._list_subnets(network)
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    @dispatch(event="provider.networking.subnets.create",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, network: Network | str,
               cidr_block: str) -> Subnet:
        AzureSubnet.assert_valid_resource_label(label)
        # Although Subnet doesn't support tags in Azure, we use the parent
        # Network's tags to track its subnets' labels
        subnet_name = AzureSubnet._generate_name_from_label(label, "cb-sn")

        network_id = network.id \
            if isinstance(network, Network) else network

        provider = cast("AzureCloudProvider", self.provider)
        subnet_info = provider.azure_client.create_subnet(
            network_id,
            subnet_name,
            {
                'address_prefix': cidr_block
            }
        )

        subnet = AzureSubnet(provider, subnet_info)
        subnet.label = label
        return subnet

    @dispatch(event="provider.networking.subnets.delete",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def delete(self, subnet: Subnet | str) -> None:
        sn = subnet if isinstance(subnet, AzureSubnet) else self.get(subnet)
        if sn:
            azure_client = cast(
                "AzureCloudProvider", self.provider).azure_client
            azure_client.delete_subnet(sn.id)
            # Although Subnet doesn't support labels, we use the parent
            # Network's tags to track the subnet's labels, thus that
            # network-level tag must be deleted with the subnet
            net_id = sn.network_id
            az_network = azure_client.get_network(net_id)
            az_network.tags.pop(sn.tag_name)
            azure_client.update_network_tags(
                az_network.id, az_network.tags)


class AzureRouterService(BaseRouterService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureRouterService, self).__init__(provider)

    @dispatch(event="provider.networking.routers.get",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def get(self, router_id: str) -> Router | None:
        provider = cast("AzureCloudProvider", self.provider)
        try:
            route = provider.azure_client.get_route_table(router_id)
            return AzureRouter(provider, route)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.networking.routers.find",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Router]:
        obj_list: builtins.list[Router] = list(self)
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    @dispatch(event="provider.networking.routers.list",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Router]:
        provider = cast("AzureCloudProvider", self.provider)
        routes = [AzureRouter(provider, route)
                  for route in provider.azure_client.list_route_tables()]
        return ClientPagedResultList(self.provider,
                                     routes,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.routers.create",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, network: Network | str) -> Router:
        router_name = AzureRouter._generate_name_from_label(label, "cb-router")

        parameters = {"location": self.provider.region_name,
                      "tags": {'Label': label}}

        provider = cast("AzureCloudProvider", self.provider)
        route = provider.azure_client.create_route_table(
            router_name, parameters)
        return AzureRouter(provider, route)

    @dispatch(event="provider.networking.routers.delete",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def delete(self, router: Router | str) -> None:
        r = router if isinstance(router, AzureRouter) else self.get(router)
        if r:
            cast("AzureCloudProvider", self.provider).azure_client.\
                delete_route_table(r.name)


class AzureGatewayService(BaseGatewayService):
    def __init__(self, provider: CloudProvider) -> None:
        super(AzureGatewayService, self).__init__(provider)

    # Azure doesn't have a notion of a route table or an internet
    # gateway as OS and AWS so create placeholder objects of the
    # AzureInternetGateway here.
    # http://bit.ly/2BqGdVh
    # Singleton returned by the list and get methods
    def _gateway_singleton(self,
                           network: Network | str) -> AzureInternetGateway:
        return AzureInternetGateway(
            cast("AzureCloudProvider", self.provider), None,
            cast("AzureNetwork | str", network))

    @dispatch(event="provider.networking.gateways.get_or_create",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def get_or_create(self, network: Network | str) -> InternetGateway:
        return self._gateway_singleton(network)

    @dispatch(event="provider.networking.gateways.list",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def list(self, network: Network | str, limit: int | None = None,
             marker: str | None = None) -> ResultList[Gateway]:
        # The base GatewayService.list already requires a leading network
        # argument ahead of list(limit, marker).
        gws = [self._gateway_singleton(network)]
        return ClientPagedResultList(self.provider,
                                     gws,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.gateways.delete",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def delete(self, network: Network | str, gateway: Gateway) -> None:
        pass


class AzureFloatingIPService(BaseFloatingIPService):

    def __init__(self, provider: CloudProvider) -> None:
        super(AzureFloatingIPService, self).__init__(provider)

    @dispatch(event="provider.networking.floating_ips.get",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def get(self, gateway: Gateway, fip_id: str) -> FloatingIP | None:
        provider = cast("AzureCloudProvider", self.provider)
        try:
            az_ip = provider.azure_client.get_floating_ip(fip_id)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None
        return AzureFloatingIP(provider, az_ip)

    @dispatch(event="provider.networking.floating_ips.list",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def list(self, gateway: Gateway, limit: int | None = None,
             marker: str | None = None) -> ResultList[FloatingIP]:
        provider = cast("AzureCloudProvider", self.provider)
        floating_ips = [AzureFloatingIP(provider, floating_ip)
                        for floating_ip in
                        provider.azure_client.list_floating_ips()]
        return ClientPagedResultList(self.provider, floating_ips,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.floating_ips.create",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def create(self, gateway: Gateway) -> FloatingIP:
        azure_client = cast("AzureCloudProvider", self.provider).azure_client
        # Basic-SKU public IPs are retired in most Azure subscriptions
        # (quota=0). Standard SKU requires Static allocation.
        public_ip_parameters = {
            'location': azure_client.region_name,
            'public_ip_allocation_method': 'Static',
            'sku': PublicIPAddressSku(name=PublicIPAddressSkuName.STANDARD),
        }

        public_ip_name = AzureFloatingIP._generate_name_from_label(
            None, 'cb-fip-')

        floating_ip = azure_client.create_floating_ip(
            public_ip_name, public_ip_parameters)
        return AzureFloatingIP(cast("AzureCloudProvider", self.provider),
                               floating_ip)

    @dispatch(event="provider.networking.floating_ips.delete",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def delete(self, gateway: Gateway, fip: FloatingIP | str) -> None:
        fip_id = fip.id if isinstance(fip, AzureFloatingIP) else fip
        cast("AzureCloudProvider", self.provider).azure_client.\
            delete_floating_ip(fip_id)


def _strip_trailing_dot(name: str | None) -> str | None:
    return name[:-1] if name and name.endswith('.') else name


def _to_relative_record_name(fqdn: str | None, zone_name: str | None) -> str:
    """Translate a cloudbridge FQDN record name to Azure's relative form.

    Azure's record set API works with names relative to the zone (e.g.
    ``foo`` inside ``example.com``) plus the special ``@`` token for the
    zone apex. cloudbridge callers pass either the bare zone (apex) or a
    dotted FQDN such as ``foo.example.com.``.
    """
    name = (_strip_trailing_dot(fqdn) or '') if fqdn else ''
    zone = (_strip_trailing_dot(zone_name) or '') if zone_name else ''
    if not name or name == zone:
        return '@'
    suffix = '.' + zone
    if name.endswith(suffix):
        return name[: -len(suffix)] or '@'
    return name


class AzureDnsService(BaseDnsService):

    def __init__(self, provider: CloudProvider) -> None:
        super(AzureDnsService, self).__init__(provider)

        # Initialize provider services
        self._zone_svc = AzureDnsZoneService(self.provider)
        self._record_svc = AzureDnsRecordService(self.provider)

    @property
    def host_zones(self) -> AzureDnsZoneService:
        return self._zone_svc

    @property
    def _records(self) -> AzureDnsRecordService:
        return self._record_svc


class AzureDnsZoneService(BaseDnsZoneService):

    def __init__(self, provider: CloudProvider) -> None:
        super(AzureDnsZoneService, self).__init__(provider)

    @dispatch(event="provider.dns.host_zones.get",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def get(self, dns_zone_id: str) -> DnsZone | None:
        provider = cast("AzureCloudProvider", self.provider)
        try:
            zone = provider.azure_client.get_dns_zone(
                _strip_trailing_dot(dns_zone_id))
            return AzureDnsZone(provider, zone)
        except ResourceNotFoundError:
            return None

    @dispatch(event="provider.dns.host_zones.list",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[DnsZone]:
        provider = cast("AzureCloudProvider", self.provider)
        zones = [AzureDnsZone(provider, z)
                 for z in provider.azure_client.list_dns_zones()]
        return ClientPagedResultList(self.provider, zones, limit, marker)

    @dispatch(event="provider.dns.host_zones.find",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[DnsZone]:
        filters = ['name']
        obj_list: builtins.list[DnsZone] = list(self)
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self.provider, list(matches),
                                     limit=None, marker=None)

    @dispatch(event="provider.dns.host_zones.create",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def create(self, name: str, admin_email: str) -> DnsZone:
        AzureDnsZone.assert_valid_resource_name(name)
        zone_name = _strip_trailing_dot(name)
        params = {
            # DNS zones in Azure are global resources but the API still
            # requires location='global'.
            'location': 'global',
            'tags': {'admin_email': admin_email},
        }
        provider = cast("AzureCloudProvider", self.provider)
        zone = provider.azure_client.create_dns_zone(zone_name, params)
        return AzureDnsZone(provider, zone)

    @dispatch(event="provider.dns.host_zones.delete",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def delete(self, dns_zone: DnsZone | str) -> None:
        zone_name = (dns_zone.id if isinstance(dns_zone, DnsZone)
                     else dns_zone)
        cast("AzureCloudProvider", self.provider).azure_client.\
            delete_dns_zone(_strip_trailing_dot(zone_name))


class AzureDnsRecordService(BaseDnsRecordService):

    def __init__(self, provider: CloudProvider) -> None:
        super(AzureDnsRecordService, self).__init__(provider)

    def _to_record_params(self, rec_type: str, data: str | builtins.list[str],
                          ttl: int | None) -> dict[str, Any]:
        """Translate cloudbridge data to Azure record-set parameters."""
        # Local imports keep the module importable when azure-mgmt-dns
        # isn't installed (e.g. on AWS-only test environments).
        from azure.mgmt.dns.models import AaaaRecord
        from azure.mgmt.dns.models import ARecord
        from azure.mgmt.dns.models import CnameRecord
        from azure.mgmt.dns.models import MxRecord
        from azure.mgmt.dns.models import NsRecord
        from azure.mgmt.dns.models import PtrRecord
        from azure.mgmt.dns.models import SrvRecord
        from azure.mgmt.dns.models import TxtRecord

        values = data if isinstance(data, list) else [data]
        params: dict[str, Any] = {'ttl': ttl or 300}

        if rec_type == 'A':
            params['a_records'] = [ARecord(ipv4_address=v) for v in values]
        elif rec_type == 'AAAA':
            params['aaaa_records'] = [
                AaaaRecord(ipv6_address=v) for v in values]
        elif rec_type == 'CNAME':
            # CNAME is a single-valued record in Azure.
            params['cname_record'] = CnameRecord(
                cname=self._standardize_record(values[0], rec_type))
        elif rec_type == 'MX':
            mx = []
            for v in values:
                preference, exchange = v.split(' ', 1)
                mx.append(MxRecord(
                    preference=int(preference),
                    exchange=self._standardize_record(exchange.strip(),
                                                      rec_type)))
            params['mx_records'] = mx
        elif rec_type == 'NS':
            params['ns_records'] = [NsRecord(nsdname=v) for v in values]
        elif rec_type == 'PTR':
            params['ptr_records'] = [PtrRecord(ptrdname=v) for v in values]
        elif rec_type == 'SRV':
            srv = []
            for v in values:
                priority, weight, port, target = v.split(' ', 3)
                srv.append(SrvRecord(
                    priority=int(priority), weight=int(weight),
                    port=int(port), target=target))
            params['srv_records'] = srv
        elif rec_type == 'TXT':
            params['txt_records'] = [
                TxtRecord(value=v if isinstance(v, list) else [v])
                for v in values]
        else:
            raise InvalidParamException(
                "Unsupported DNS record type: %s" % rec_type)
        return params

    def get(self, dns_zone: DnsZone | str,
            rec_id: str) -> DnsRecord | None:
        if not rec_id or ':' not in rec_id:
            return None
        rec_name, rec_type = rec_id.split(':', 1)
        provider = cast("AzureCloudProvider", self.provider)
        azure_zone = cast("AzureDnsZone", dns_zone)
        try:
            rec = provider.azure_client.get_dns_record(
                cast(Any, dns_zone).id, rec_name, rec_type)
            return AzureDnsRecord(provider, azure_zone, rec)
        except ResourceNotFoundError:
            return None

    # Intentional arguments-differ: the BasePageableObjectMixin.list takes
    # (limit, marker); DnsRecord listing requires a leading dns_zone.
    def list(self,  # type: ignore[override]
             dns_zone: DnsZone | str, limit: int | None = None,
             marker: str | None = None) -> ResultList[DnsRecord]:
        provider = cast("AzureCloudProvider", self.provider)
        azure_zone = cast("AzureDnsZone", dns_zone)
        records = [AzureDnsRecord(provider, azure_zone, r)
                   for r in provider.azure_client.list_dns_records(
                       cast(Any, dns_zone).id)]
        return ClientPagedResultList(self.provider, records, limit, marker)

    def find(self, dns_zone: DnsZone | str,
             **kwargs: Any) -> ResultList[DnsRecord]:
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs,
                                          cast(Any, dns_zone).records)
        return ClientPagedResultList(self.provider, list(matches),
                                     limit=None, marker=None)

    def create(self, dns_zone: DnsZone | str, name: str, type: str,
               data: str, ttl: int | None = None) -> DnsRecord:
        AzureDnsRecord.assert_valid_resource_name(name)
        relative_name = _to_relative_record_name(name, cast(Any, dns_zone).id)
        params = self._to_record_params(type, data, ttl)
        cast("AzureCloudProvider", self.provider).azure_client.\
            create_dns_record(
                cast(Any, dns_zone).id, relative_name, type, params)
        record = self.get(dns_zone, relative_name + ':' + type)
        if record is None:
            raise ProviderInternalException(
                "DNS record %s could not be retrieved after creation" % name)
        return record

    def delete(self, dns_zone: DnsZone | str,
               record: DnsRecord | str) -> None:
        if isinstance(record, AzureDnsRecord):
            rec_name = record.name
            rec_type = record.type
        else:
            rec_name, rec_type = cast(str, record).split(':', 1)
        cast("AzureCloudProvider", self.provider).azure_client.\
            delete_dns_record(cast(Any, dns_zone).id, rec_name, rec_type)
