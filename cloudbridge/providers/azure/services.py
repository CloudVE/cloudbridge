import base64
import logging
import uuid

import cloudbridge.base.helpers as cb_helpers
from cloudbridge.base.middleware import dispatch
from cloudbridge.base.resources import (BaseMultipartUpload, BaseUploadPart,
                                        ClientPagedResultList,
                                        ServerPagedResultList)
from cloudbridge.base.services import (BaseBucketObjectService,
                                       BaseBucketService, BaseComputeService,
                                       BaseDnsRecordService, BaseDnsService,
                                       BaseDnsZoneService,
                                       BaseFloatingIPService,
                                       BaseGatewayService, BaseImageService,
                                       BaseInstanceService, BaseKeyPairService,
                                       BaseNetworkingService,
                                       BaseNetworkService, BaseRegionService,
                                       BaseRouterService, BaseSecurityService,
                                       BaseSnapshotService, BaseStorageService,
                                       BaseSubnetService,
                                       BaseVMFirewallRuleService,
                                       BaseVMFirewallService,
                                       BaseVMTypeService, BaseVolumeService)
from cloudbridge.interfaces.exceptions import (DuplicateResourceException,
                                               InvalidParamException,
                                               InvalidValueException)
from cloudbridge.interfaces.resources import (MachineImage, Network, Snapshot,
                                              TrafficDirection, VMFirewall,
                                              VMType, Volume)
from azure.core.exceptions import ResourceNotFoundError

from azure.mgmt.compute.models import (CreationData, DataDisk,
                                       DiskCreateOption, HardwareProfile,
                                       ImageReference, LinuxConfiguration,
                                       ManagedDiskParameters,
                                       NetworkInterfaceReference,
                                       NetworkProfile, OSDisk, OSProfile,
                                       SshConfiguration, SshPublicKey,
                                       StorageProfile)
from azure.mgmt.network.models import (AddressSpace,
                                       NetworkInterfaceIPConfiguration,
                                       PublicIPAddressSku,
                                       PublicIPAddressSkuName, SubResource)

from .resources import (AzureBucket, AzureBucketObject, AzureDnsRecord,
                        AzureDnsZone, AzureFloatingIP, AzureInstance,
                        AzureInternetGateway, AzureKeyPair, AzureLaunchConfig,
                        AzureMachineImage, AzureNetwork, AzureRegion,
                        AzureRouter, AzureSnapshot, AzureSubnet,
                        AzureVMFirewall, AzureVMFirewallRule, AzureVMType,
                        AzureVolume)

log = logging.getLogger(__name__)


class AzureSecurityService(BaseSecurityService):
    def __init__(self, provider):
        super(AzureSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = AzureKeyPairService(provider)
        self._vm_firewalls = AzureVMFirewallService(provider)
        self._vm_firewall_rule_svc = AzureVMFirewallRuleService(provider)

    @property
    def key_pairs(self):
        return self._key_pairs

    @property
    def vm_firewalls(self):
        return self._vm_firewalls

    @property
    def _vm_firewall_rules(self):
        return self._vm_firewall_rule_svc


class AzureVMFirewallService(BaseVMFirewallService):
    def __init__(self, provider):
        super(AzureVMFirewallService, self).__init__(provider)

    @dispatch(event="provider.security.vm_firewalls.get",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_firewall_id):
        try:
            fws = self.provider.azure_client.get_vm_firewall(vm_firewall_id)
            return AzureVMFirewall(self.provider, fws)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.security.vm_firewalls.list",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        fws = [AzureVMFirewall(self.provider, fw)
               for fw in self.provider.azure_client.list_vm_firewall()]
        return ClientPagedResultList(self.provider, fws, limit, marker)

    @cb_helpers.deprecated_alias(network_id='network')
    @dispatch(event="provider.security.vm_firewalls.create",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network, description=None):
        AzureVMFirewall.assert_valid_resource_label(label)
        name = AzureVMFirewall._generate_name_from_label(label, "cb-fw")
        net = network.id if isinstance(network, Network) else network
        parameters = {"location": self.provider.region_name,
                      "tags": {'Label': label,
                               'network_id': net}}

        if description:
            parameters['tags'].update(Description=description)

        fw = self.provider.azure_client.create_vm_firewall(name,
                                                           parameters)

        # Add default rules to negate azure default rules.
        # See: https://github.com/CloudVE/cloudbridge/issues/106
        # pylint:disable=protected-access
        for rule in fw.default_security_rules:
            rule_name = "cb-override-" + rule.name
            # Transpose rules to priority 4001 onwards, because
            # only 0-4096 are allowed for custom rules
            rule.priority = rule.priority - 61440
            rule.access = "Deny"
            self.provider.azure_client.create_vm_firewall_rule(
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
        result = self.provider.azure_client.create_vm_firewall_rule(
            fw.id, "cb-default-internet-outbound", parameters)
        fw.security_rules.append(result)

        cb_fw = AzureVMFirewall(self.provider, fw)
        return cb_fw

    @dispatch(event="provider.security.vm_firewalls.delete",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def delete(self, vm_firewall):
        fw_id = (vm_firewall.id if isinstance(vm_firewall, AzureVMFirewall)
                 else vm_firewall)
        self.provider.azure_client.delete_vm_firewall(fw_id)


class AzureVMFirewallRuleService(BaseVMFirewallRuleService):

    def __init__(self, provider):
        super(AzureVMFirewallRuleService, self).__init__(provider)

    @dispatch(event="provider.security.vm_firewall_rules.list",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def list(self, firewall, limit=None, marker=None):
        # Filter out firewall rules with priority < 3500 because values
        # between 3500 and 4096 are assumed to be owned by cloudbridge
        # default rules.
        # pylint:disable=protected-access
        rules = [AzureVMFirewallRule(firewall, rule) for rule
                 in firewall._vm_firewall.security_rules
                 if rule.priority < 3500]
        return ClientPagedResultList(self.provider, rules,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.security.vm_firewall_rules.create",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def create(self, firewall, direction, protocol=None, from_port=None,
               to_port=None, cidr=None, src_dest_fw=None):
        if protocol and from_port and to_port:
            return self._create_rule(firewall, direction, protocol, from_port,
                                     to_port, cidr)
        elif src_dest_fw:
            result = None
            fw = (self.provider.security.vm_firewalls.get(src_dest_fw)
                  if isinstance(src_dest_fw, str) else src_dest_fw)
            for rule in fw.rules:
                result = self._create_rule(
                    rule.direction, rule.protocol, rule.from_port,
                    rule.to_port, rule.cidr)
            return result
        else:
            return None

    def _create_rule(self, firewall, direction, protocol,
                     from_port, to_port, cidr):

        # If cidr is None, default values is set as 0.0.0.0/0
        if not cidr:
            cidr = '0.0.0.0/0'

        count = len(firewall._vm_firewall.security_rules) + 1
        rule_name = "cb-rule-" + str(count)
        priority = 1000 + count
        destination_port_range = str(from_port) + "-" + str(to_port)
        source_port_range = '*'
        destination_address_prefix = "*"
        access = "Allow"
        direction = ("Inbound" if direction == TrafficDirection.INBOUND
                     else "Outbound")
        parameters = {"priority": priority,
                      "protocol": protocol,
                      "source_port_range": source_port_range,
                      "source_address_prefix": cidr,
                      "destination_port_range": destination_port_range,
                      "destination_address_prefix": destination_address_prefix,
                      "access": access,
                      "direction": direction}
        result = self.provider.azure_client. \
            create_vm_firewall_rule(firewall.id,
                                    rule_name, parameters)
        # pylint:disable=protected-access
        firewall._vm_firewall.security_rules.append(result)
        return AzureVMFirewallRule(firewall, result)

    @dispatch(event="provider.security.vm_firewall_rules.delete",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def delete(self, firewall, rule):
        rule_id = rule.id if isinstance(rule, AzureVMFirewallRule) else rule
        fw_name = firewall.name
        self.provider.azure_client. \
            delete_vm_firewall_rule(rule_id, fw_name)
        for i, o in enumerate(firewall._vm_firewall.security_rules):
            if o.id == rule_id:
                # pylint:disable=protected-access
                del firewall._vm_firewall.security_rules[i]
                break


class AzureKeyPairService(BaseKeyPairService):
    PARTITION_KEY = '00000000-0000-0000-0000-000000000000'

    def __init__(self, provider):
        super(AzureKeyPairService, self).__init__(provider)

    @dispatch(event="provider.security.key_pairs.get",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def get(self, key_pair_id):
        try:
            key_pair = self.provider.azure_client.\
                get_public_key(key_pair_id)

            if key_pair:
                return AzureKeyPair(self.provider, key_pair)
            return None
        except ResourceNotFoundError as error:
            log.debug("KeyPair %s was not found.", key_pair_id)
            log.debug(error)
            return None

    @dispatch(event="provider.security.key_pairs.list",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
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

    @dispatch(event="provider.security.key_pairs.find",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
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

    @dispatch(event="provider.security.key_pairs.delete",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def delete(self, key_pair):
        key_pair = (key_pair if isinstance(key_pair, AzureKeyPair) else
                    self.get(key_pair))
        if key_pair:
            # pylint:disable=protected-access
            self.provider.azure_client.delete_public_key(key_pair._key_pair)


class AzureStorageService(BaseStorageService):
    def __init__(self, provider):
        super(AzureStorageService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = AzureVolumeService(self.provider)
        self._snapshot_svc = AzureSnapshotService(self.provider)
        self._bucket_svc = AzureBucketService(self.provider)
        self._bucket_obj_svc = AzureBucketObjectService(self.provider)

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


class AzureVolumeService(BaseVolumeService):
    def __init__(self, provider):
        super(AzureVolumeService, self).__init__(provider)

    @dispatch(event="provider.storage.volumes.get",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def get(self, volume_id):
        try:
            volume = self.provider.azure_client.get_disk(volume_id)
            return AzureVolume(self.provider, volume)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.storage.volumes.find",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
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
    def list(self, limit=None, marker=None):
        azure_vols = self.provider.azure_client.list_disks()
        cb_vols = [AzureVolume(self.provider, vol) for vol in azure_vols]
        return ClientPagedResultList(self.provider, cb_vols,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.storage.volumes.create",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def create(self, label, size, snapshot=None, description=None):
        AzureVolume.assert_valid_resource_label(label)
        disk_name = AzureVolume._generate_name_from_label(label, "cb-vol")
        tags = {'Label': label}

        snapshot = (self.provider.storage.snapshots.get(snapshot)
                    if snapshot and isinstance(snapshot, str) else snapshot)

        if description:
            tags.update(Description=description)

        if snapshot:
            params = {
                'location': self.provider.region_name,
                'creation_data': CreationData(
                    create_option=DiskCreateOption.copy,
                    source_uri=snapshot.resource_id,
                ),
                'tags': tags
            }

            disk = self.provider.azure_client.create_snapshot_disk(disk_name,
                                                                   params)

        else:
            params = {
                'location': self.provider.region_name,
                'disk_size_gb': size,
                'creation_data': CreationData(
                    create_option=DiskCreateOption.empty,
                ),
                'tags': tags
            }

            disk = self.provider.azure_client.create_empty_disk(disk_name,
                                                                params)

        azure_vol = self.provider.azure_client.get_disk(disk.id)
        cb_vol = AzureVolume(self.provider, azure_vol)

        return cb_vol

    @dispatch(event="provider.storage.volumes.delete",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def delete(self, volume_id):
        vol_id = (volume_id.id if isinstance(volume_id, AzureVolume)
                  else volume_id)
        self.provider.azure_client.delete_disk(vol_id)


class AzureSnapshotService(BaseSnapshotService):
    def __init__(self, provider):
        super(AzureSnapshotService, self).__init__(provider)

    @dispatch(event="provider.storage.snapshots.get",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def get(self, snapshot_id):
        try:
            snapshot = self.provider.azure_client.get_snapshot(snapshot_id)
            return AzureSnapshot(self.provider, snapshot)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.storage.snapshots.find",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
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
    def list(self, limit=None, marker=None):
        snaps = [AzureSnapshot(self.provider, obj)
                 for obj in
                 self.provider.azure_client.list_snapshots()]
        return ClientPagedResultList(self.provider, snaps, limit, marker)

    @dispatch(event="provider.storage.snapshots.create",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def create(self, label, volume, description=None):
        AzureSnapshot.assert_valid_resource_label(label)
        snapshot_name = AzureSnapshot._generate_name_from_label(label,
                                                                "cb-snap")
        tags = {'Label': label}
        if description:
            tags.update(Description=description)

        volume = (self.provider.storage.volumes.get(volume)
                  if isinstance(volume, str) else volume)

        # We need to pass the Disk Object to create the snapshot
        volume = volume._volume

        azure_snap = self.provider.azure_client.create_snapshot(
            snapshot_name, volume, tags
        )

        return AzureSnapshot(self.provider, azure_snap)

    @dispatch(event="provider.storage.snapshots.delete",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def delete(self, snapshot_id):
        snap_id = (snapshot_id.id if isinstance(snapshot_id, AzureSnapshot)
                   else snapshot_id)
        self.provider.azure_client.delete_snapshot(snap_id)


class AzureBucketService(BaseBucketService):
    def __init__(self, provider):
        super(AzureBucketService, self).__init__(provider)

    @dispatch(event="provider.storage.buckets.get",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        bucket = self.provider.azure_client.get_container(bucket_id)
        if bucket.exists():
            return AzureBucket(self.provider, bucket)
        else:
            return None

    @dispatch(event="provider.storage.buckets.list",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        buckets = [AzureBucket(self.provider, bucket)
                   for bucket
                   in self.provider.azure_client.list_containers()]
        return ClientPagedResultList(self.provider, buckets,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.storage.buckets.create",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def create(self, name, location=None):
        """
        Create a new bucket.
        """
        AzureBucket.assert_valid_resource_name(name)
        bucket = self.provider.azure_client.create_container(name)
        return AzureBucket(self.provider, bucket)

    @dispatch(event="provider.storage.buckets.delete",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def delete(self, bucket):
        """
        Delete this bucket.
        """
        b_id = bucket.id if isinstance(bucket, AzureBucket) else bucket
        self.provider.azure_client.delete_container(b_id)


class AzureBucketObjectService(BaseBucketObjectService):
    def __init__(self, provider):
        super(AzureBucketObjectService, self).__init__(provider)

    def get(self, bucket, object_id):
        """
        Retrieve a given object from this bucket.
        """
        try:
            # pylint:disable=protected-access
            obj = bucket._bucket.get_blob_client(object_id).get_blob_properties()
            return AzureBucketObject(self.provider, bucket, obj)
        except ResourceNotFoundError as azureEx:
            log.exception(azureEx)
            return None

    def list(self, bucket, limit=None, marker=None, prefix=None):
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        objects = [AzureBucketObject(self.provider, bucket, obj)
                   for obj in
                   bucket._bucket.list_blobs(name_starts_with=prefix)]
        return ClientPagedResultList(self.provider, objects,
                                     limit=limit, marker=marker)

    def find(self, bucket, **kwargs):
        obj_list = [AzureBucketObject(self.provider, bucket, obj)
                    for obj in
                    bucket._bucket.list_blobs()]
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self.provider, list(matches))

    def create(self, bucket, name):
        blob_client = bucket._bucket.get_blob_client(name)
        blob_client.upload_blob('')
        return AzureBucketObject(self.provider, bucket, blob_client.get_blob_properties())

    @staticmethod
    def _block_id(upload_id, part_number):
        # Azure requires every block id for a blob to be the same length and
        # base64-encoded. The upload id is a fixed-length uuid hex, so the
        # encoded ids are always equal length.
        raw = "{0}-{1:08d}".format(upload_id, part_number)
        return base64.b64encode(raw.encode()).decode()

    @dispatch(event="provider.storage._bucket_objects.create_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def create_multipart_upload(self, bucket, object_name):
        # Azure block blobs have no server-side "initiate" step; the upload id
        # only namespaces this upload's block ids.
        return BaseMultipartUpload(self.provider, bucket, object_name,
                                   uuid.uuid4().hex)

    @dispatch(event="provider.storage._bucket_objects.upload_part",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def upload_part(self, bucket, upload, part_number, data):
        block_id = self._block_id(upload.id, part_number)
        self.provider.azure_client.stage_block(
            bucket.name, upload.object_name, block_id, data)
        return BaseUploadPart(part_number, block_id)

    @dispatch(event="provider.storage._bucket_objects."
                    "complete_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def complete_multipart_upload(self, bucket, upload, parts):
        ordered = sorted(parts, key=lambda p: p.part_number)
        self.provider.azure_client.commit_block_list(
            bucket.name, upload.object_name, [p.etag for p in ordered])
        return self.get(bucket, upload.object_name)

    @dispatch(event="provider.storage._bucket_objects.abort_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def abort_multipart_upload(self, bucket, upload):
        # Azure has no server-side abort: uncommitted blocks are garbage
        # collected automatically (after ~7 days), so there is nothing to do.
        log.debug("Azure has no multipart abort; uncommitted blocks for "
                  "%s/%s will expire automatically.",
                  bucket.name, upload.object_name)


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
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    def find(self, **kwargs):
        obj_list = self
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    def list(self, filter_by_owner=True, limit=None, marker=None):
        """
        List all images.
        """
        azure_images = self.provider.azure_client.list_images()
        azure_gallery_refs = self.provider.azure_client.list_gallery_refs() \
            if not filter_by_owner else []
        cb_images = [AzureMachineImage(self.provider, img)
                     for img in azure_images + azure_gallery_refs]
        return ClientPagedResultList(self.provider, cb_images,
                                     limit=limit, marker=marker)


class AzureInstanceService(BaseInstanceService):
    def __init__(self, provider):
        super(AzureInstanceService, self).__init__(provider)

    def _resolve_launch_options(self, inst_name, subnet=None, zone_id=None,
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
                    create(label='{0}-fw'.format(inst_name),
                           description='Merge vm firewall {0}'.
                           format(','.join(vm_firewalls_ids)))

                for fw in vm_firewalls:
                    new_fw.add_rule(src_dest_fw=fw)

                vm_firewall_id = new_fw.resource_id

        return subnet.resource_id, zone_id, vm_firewall_id

    def _create_storage_profile(self, image, launch_config, instance_name):

        if image.is_gallery_image:
            # pylint:disable=protected-access
            reference = image._image.as_dict()
            image_ref = ImageReference(
                publisher=reference['publisher'],
                offer=reference['offer'],
                sku=reference['sku'],
                version=reference['version'],
            )
        else:
            image_ref = ImageReference(id=image.resource_id)

        os_disk = OSDisk(
            name=instance_name + '_os_disk',
            create_option=DiskCreateOption.from_image,
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

    def _process_block_device_mappings(self, launch_config):
        """
        Processes block device mapping information
        and returns a DataDisk model list. If new volumes
        are requested (source is None and destination is VOLUME), they will be
        created and the relevant volume ids included in the mapping.
        """
        data_disks = []
        root_disk_size = None

        def append_disk(disk_kwargs, device_no, delete_on_terminate,
                        managed_disk_id=None):
            # Azure has no direct equivalent of AWS' delete_on_terminate, so
            # the cleanup tag is recorded on the parent VM later; we just
            # carry the flag (and the disk id) alongside the DataDisk model.
            disk = DataDisk(lun=device_no, **disk_kwargs)
            disk._cb_delete_on_terminate = delete_on_terminate
            disk._cb_managed_disk_id = managed_disk_id
            data_disks.append(disk)

        for device_no, device in enumerate(launch_config.block_devices):
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
                            'name': snapshot_vol._volume.name,
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
                            'name': device.source._volume.name,
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
                            'name': device.source._volume.name,
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

    def create_launch_config(self):
        return AzureLaunchConfig(self.provider)

    @dispatch(event="provider.compute.instances.create",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def create(self, label, image, vm_type, subnet,
               key_pair=None, vm_firewalls=None, user_data=None,
               launch_config=None, **kwargs):
        AzureInstance.assert_valid_resource_label(label)
        instance_name = AzureInstance._generate_name_from_label(label,
                                                                "cb-ins")

        image = (image if isinstance(image, AzureMachineImage) else
                 self.provider.compute.images.get(image))
        if not isinstance(image, AzureMachineImage):
            raise Exception("Provided image %s is not a valid azure image"
                            % image)

        instance_size = vm_type.id if \
            isinstance(vm_type, VMType) else vm_type

        if subnet:
            subnet = (subnet if isinstance(subnet, AzureSubnet) else
                      self.provider.networking.subnets.get(subnet))
        else:
            subnet = self.provider.networking.subnets.get_or_create_default()

        zone_name = self.provider.zone_name

        subnet_id, zone_id, vm_firewall_id = \
            self._resolve_launch_options(instance_name,
                                         subnet, zone_name, vm_firewalls)

        storage_profile = self._create_storage_profile(image, launch_config,
                                                       instance_name)

        nic_params = {
            'location': self.provider.region_name,
            'ip_configurations': [NetworkInterfaceIPConfiguration(
                name=instance_name + '_ip_config',
                private_ip_allocation_method='Dynamic',
                subnet=SubResource(id=subnet_id),
            )],
        }

        if vm_firewall_id:
            nic_params['network_security_group'] = SubResource(
                id=vm_firewall_id)
        nic_info = self.provider.azure_client.create_nic(
            instance_name + '_nic',
            nic_params
        )
        # #! indicates shell script
        ud = '#cloud-config\n' + user_data \
            if user_data and not user_data.startswith('#!')\
            and not user_data.startswith('#cloud-config') else user_data

        # Key_pair is mandatory in azure and it should not be None.
        temp_key_pair = None
        if key_pair:
            key_pair = (key_pair if isinstance(key_pair, AzureKeyPair)
                        else self.provider.security.key_pairs.get(key_pair))
        else:
            # Create a temporary keypair if none is provided to keep Azure
            # happy, but the private key will be discarded, so it'll be all
            # but useless. However, this will allow an instance to be launched
            # without specifying a keypair, so users may still be able to login
            # if they have a preinstalled keypair/password baked into the image
            temp_kp_name = "".join(["cb-default-kp-",
                                   str(uuid.uuid5(uuid.NAMESPACE_OID,
                                                  instance_name))[-6:]])
            key_pair = self.provider.security.key_pairs.create(
                name=temp_kp_name)
            temp_key_pair = key_pair

        os_profile = OSProfile(
            admin_username=self.provider.vm_default_user_name,
            computer_name=instance_name,
            linux_configuration=LinuxConfiguration(
                disable_password_authentication=True,
                ssh=SshConfiguration(public_keys=[SshPublicKey(
                    path="/home/{}/.ssh/authorized_keys".format(
                        self.provider.vm_default_user_name),
                    key_data=key_pair._key_pair['Key'],
                )]),
            ),
        )

        tags = {'Label': label}
        # Surface each data disk's delete-on-terminate flag onto the parent
        # VM tags so the VM-delete path can later clean them up.
        for disk in (storage_profile.data_disks or []):
            tags['delete_on_terminate'] = getattr(
                disk, '_cb_delete_on_terminate', False)

        params = {
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
            custom_data = base64.b64encode(bytes(ud, 'utf-8'))
            params['os_profile'].custom_data = str(custom_data, 'utf-8')

        if not temp_key_pair:
            params['tags'].update(Key_Pair=key_pair.id)

        try:
            vm = self.provider.azure_client.create_vm(instance_name, params)
        except Exception as e:
            # If VM creation fails, attempt to clean up intermediary resources
            self.provider.azure_client.delete_nic(nic_info.id)
            for disk in (storage_profile.data_disks or []):
                if getattr(disk, '_cb_delete_on_terminate', False):
                    disk_id = getattr(disk, '_cb_managed_disk_id', None)
                    if disk_id:
                        vol = self.provider.storage.volumes.get(disk_id)
                        vol.delete()
            raise e
        finally:
            if temp_key_pair:
                temp_key_pair.delete()
        return AzureInstance(self.provider, vm)

    @dispatch(event="provider.compute.instances.list",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        """
        List all instances.
        """
        instances = [AzureInstance(self.provider, inst)
                     for inst in self.provider.azure_client.list_vm()]
        return ClientPagedResultList(self.provider, instances,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.compute.instances.get",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def get(self, instance_id):
        """
        Returns an instance given its id. Returns None
        if the object does not exist.
        """
        try:
            vm = self.provider.azure_client.get_vm(instance_id)
            return AzureInstance(self.provider, vm)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.compute.instances.find",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
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
    def delete(self, instance):
        """
        Permanently terminate this instance.
        After deleting the VM. we are deleting the network interface
        associated to the instance, and also removing OS disk and data disks
        where tag with name 'delete_on_terminate' has value True.
        """
        ins = (instance if isinstance(instance, AzureInstance) else
               self.get(instance))
        if not instance:
            return

        # Remove IPs first to avoid a network interface conflict
        # pylint:disable=protected-access
        for public_ip_id in ins._public_ip_ids:
            ins.remove_floating_ip(public_ip_id)
        self.provider.azure_client.deallocate_vm(ins.id)
        self.provider.azure_client.delete_vm(ins.id)
        # pylint:disable=protected-access
        for nic_id in ins._nic_ids:
            self.provider.azure_client.delete_nic(nic_id)
        # pylint:disable=protected-access
        for data_disk in ins._vm.storage_profile.data_disks:
            if data_disk.managed_disk:
                # pylint:disable=protected-access
                if ins._vm.tags.get('delete_on_terminate',
                                    'False') == 'True':
                    self.provider.azure_client. \
                        delete_disk(data_disk.managed_disk.id)
        # pylint:disable=protected-access
        if ins._vm.storage_profile.os_disk.managed_disk:
            self.provider.azure_client. \
                delete_disk(ins._vm.storage_profile.os_disk.managed_disk.id)


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

    @dispatch(event="provider.compute.vm_types.list",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        vm_types = [AzureVMType(self.provider, vm_type)
                    for vm_type in self.instance_data]
        return ClientPagedResultList(self.provider, vm_types,
                                     limit=limit, marker=marker)


class AzureRegionService(BaseRegionService):
    def __init__(self, provider):
        super(AzureRegionService, self).__init__(provider)

    @dispatch(event="provider.compute.regions.get",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def get(self, region_id):
        region = None
        for azureRegion in self.provider.azure_client.list_locations():
            if azureRegion.name == region_id:
                region = AzureRegion(self.provider, azureRegion)
                break
        return region

    @dispatch(event="provider.compute.regions.list",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        regions = [AzureRegion(self.provider, region)
                   for region in self.provider.azure_client.list_locations()]
        return ClientPagedResultList(self.provider, regions,
                                     limit=limit, marker=marker)

    @property
    def current(self):
        return self.get(self.provider.region_name)


class AzureNetworkingService(BaseNetworkingService):
    def __init__(self, provider):
        super(AzureNetworkingService, self).__init__(provider)
        self._network_service = AzureNetworkService(self.provider)
        self._subnet_service = AzureSubnetService(self.provider)
        self._router_service = AzureRouterService(self.provider)
        self._gateway_service = AzureGatewayService(self.provider)
        self._floating_ip_service = AzureFloatingIPService(self.provider)

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


class AzureNetworkService(BaseNetworkService):
    def __init__(self, provider):
        super(AzureNetworkService, self).__init__(provider)

    @dispatch(event="provider.networking.networks.get",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def get(self, network_id):
        try:
            network = self.provider.azure_client.get_network(network_id)
            return AzureNetwork(self.provider, network)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.networking.networks.list",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        networks = [AzureNetwork(self.provider, network)
                    for network in self.provider.azure_client.list_networks()]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.networks.create",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def create(self, label, cidr_block):
        AzureNetwork.assert_valid_resource_label(label)
        params = {
            'location': self.provider.azure_client.region_name,
            'address_space': AddressSpace(
                address_prefixes=[cidr_block]),
            'tags': {'Label': label}
        }

        network_name = AzureNetwork._generate_name_from_label(label, 'cb-net')

        az_network = self.provider.azure_client.create_network(network_name,
                                                               params)
        cb_network = AzureNetwork(self.provider, az_network)
        return cb_network

    @dispatch(event="provider.networking.networks.delete",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def delete(self, network):
        net_id = network.id if isinstance(network, AzureNetwork) else network
        if net_id:
            self.provider.azure_client.delete_network(net_id)


class AzureSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(AzureSubnetService, self).__init__(provider)

    def _list_subnets(self, network=None):
        result_list = []
        if network:
            network_id = network.id \
                if isinstance(network, Network) else network
            result_list = self.provider.azure_client.list_subnets(network_id)
        else:
            for net in self.provider.networking.networks:
                try:
                    result_list.extend(self.provider.azure_client.list_subnets(
                        net.id
                    ))
                except ResourceNotFoundError as not_found_error:
                    log.exception(not_found_error)
        subnets = [AzureSubnet(self.provider, subnet)
                   for subnet in result_list]

        return subnets

    @dispatch(event="provider.networking.subnets.get",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def get(self, subnet_id):
        """
         Azure does not provide an api to get the subnet directly by id.
         It also requires the network id.
         To make it consistent across the providers the following code
         gets the specific code from the subnet list.
        """
        try:
            azure_subnet = self.provider.azure_client.get_subnet(subnet_id)
            return AzureSubnet(self.provider,
                               azure_subnet) if azure_subnet else None
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.networking.subnets.list",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def list(self, network=None, limit=None, marker=None):
        return ClientPagedResultList(self.provider,
                                     self._list_subnets(network),
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.subnets.find",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def find(self, network=None, **kwargs):
        obj_list = self._list_subnets(network)
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    @dispatch(event="provider.networking.subnets.create",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network, cidr_block):
        AzureSubnet.assert_valid_resource_label(label)
        # Although Subnet doesn't support tags in Azure, we use the parent
        # Network's tags to track its subnets' labels
        subnet_name = AzureSubnet._generate_name_from_label(label, "cb-sn")

        network_id = network.id \
            if isinstance(network, Network) else network

        subnet_info = self.provider.azure_client\
            .create_subnet(
                network_id,
                subnet_name,
                {
                    'address_prefix': cidr_block
                }
            )

        subnet = AzureSubnet(self.provider, subnet_info)
        subnet.label = label
        return subnet

    @dispatch(event="provider.networking.subnets.delete",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def delete(self, subnet):
        sn = subnet if isinstance(subnet, AzureSubnet) else self.get(subnet)
        if sn:
            self.provider.azure_client.delete_subnet(sn.id)
            # Although Subnet doesn't support labels, we use the parent
            # Network's tags to track the subnet's labels, thus that
            # network-level tag must be deleted with the subnet
            net_id = sn.network_id
            az_network = self.provider.azure_client.get_network(net_id)
            az_network.tags.pop(sn.tag_name)
            self.provider.azure_client.update_network_tags(
                az_network.id, az_network.tags)


class AzureRouterService(BaseRouterService):
    def __init__(self, provider):
        super(AzureRouterService, self).__init__(provider)

    @dispatch(event="provider.networking.routers.get",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def get(self, router_id):
        try:
            route = self.provider.azure_client.get_route_table(router_id)
            return AzureRouter(self.provider, route)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None

    @dispatch(event="provider.networking.routers.find",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
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
    def list(self, limit=None, marker=None):
        routes = [AzureRouter(self.provider, route)
                  for route in
                  self.provider.azure_client.list_route_tables()]
        return ClientPagedResultList(self.provider,
                                     routes,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.routers.create",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network):
        router_name = AzureRouter._generate_name_from_label(label, "cb-router")

        parameters = {"location": self.provider.region_name,
                      "tags": {'Label': label}}

        route = self.provider.azure_client. \
            create_route_table(router_name, parameters)
        return AzureRouter(self.provider, route)

    @dispatch(event="provider.networking.routers.delete",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def delete(self, router):
        r = router if isinstance(router, AzureRouter) else self.get(router)
        if r:
            self.provider.azure_client.delete_route_table(r.name)


class AzureGatewayService(BaseGatewayService):
    def __init__(self, provider):
        super(AzureGatewayService, self).__init__(provider)

    # Azure doesn't have a notion of a route table or an internet
    # gateway as OS and AWS so create placeholder objects of the
    # AzureInternetGateway here.
    # http://bit.ly/2BqGdVh
    # Singleton returned by the list and get methods
    def _gateway_singleton(self, network):
        return AzureInternetGateway(self.provider, None, network)

    @dispatch(event="provider.networking.gateways.get_or_create",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def get_or_create(self, network):
        return self._gateway_singleton(network)

    @dispatch(event="provider.networking.gateways.list",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def list(self, network, limit=None, marker=None):
        gws = [self._gateway_singleton(network)]
        return ClientPagedResultList(self.provider,
                                     gws,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.gateways.delete",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def delete(self, network, gateway):
        pass


class AzureFloatingIPService(BaseFloatingIPService):

    def __init__(self, provider):
        super(AzureFloatingIPService, self).__init__(provider)

    @dispatch(event="provider.networking.floating_ips.get",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def get(self, gateway, fip_id):
        try:
            az_ip = self.provider.azure_client.get_floating_ip(fip_id)
        except (ResourceNotFoundError, InvalidValueException) as cloud_error:
            # Azure raises the cloud error if the resource not available
            log.exception(cloud_error)
            return None
        return AzureFloatingIP(self.provider, az_ip)

    @dispatch(event="provider.networking.floating_ips.list",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def list(self, gateway, limit=None, marker=None):
        floating_ips = [AzureFloatingIP(self.provider, floating_ip)
                        for floating_ip in self.provider.azure_client.
                        list_floating_ips()]
        return ClientPagedResultList(self.provider, floating_ips,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.floating_ips.create",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def create(self, gateway):
        # Basic-SKU public IPs are retired in most Azure subscriptions
        # (quota=0). Standard SKU requires Static allocation.
        public_ip_parameters = {
            'location': self.provider.azure_client.region_name,
            'public_ip_allocation_method': 'Static',
            'sku': PublicIPAddressSku(name=PublicIPAddressSkuName.STANDARD),
        }

        public_ip_name = AzureFloatingIP._generate_name_from_label(
            None, 'cb-fip-')

        floating_ip = self.provider.azure_client.\
            create_floating_ip(public_ip_name, public_ip_parameters)
        return AzureFloatingIP(self.provider, floating_ip)

    @dispatch(event="provider.networking.floating_ips.delete",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def delete(self, gateway, fip):
        fip_id = fip.id if isinstance(fip, AzureFloatingIP) else fip
        self.provider.azure_client.delete_floating_ip(fip_id)


def _strip_trailing_dot(name):
    return name[:-1] if name and name.endswith('.') else name


def _to_relative_record_name(fqdn, zone_name):
    """Translate a cloudbridge FQDN record name to Azure's relative form.

    Azure's record set API works with names relative to the zone (e.g.
    ``foo`` inside ``example.com``) plus the special ``@`` token for the
    zone apex. cloudbridge callers pass either the bare zone (apex) or a
    dotted FQDN such as ``foo.example.com.``.
    """
    name = _strip_trailing_dot(fqdn) if fqdn else ''
    zone = _strip_trailing_dot(zone_name) if zone_name else ''
    if not name or name == zone:
        return '@'
    suffix = '.' + zone
    if name.endswith(suffix):
        return name[: -len(suffix)] or '@'
    return name


class AzureDnsService(BaseDnsService):

    def __init__(self, provider):
        super(AzureDnsService, self).__init__(provider)

        # Initialize provider services
        self._zone_svc = AzureDnsZoneService(self.provider)
        self._record_svc = AzureDnsRecordService(self.provider)

    @property
    def host_zones(self):
        return self._zone_svc

    @property
    def _records(self):
        return self._record_svc


class AzureDnsZoneService(BaseDnsZoneService):

    def __init__(self, provider):
        super(AzureDnsZoneService, self).__init__(provider)

    @dispatch(event="provider.dns.host_zones.get",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def get(self, dns_zone_id):
        try:
            zone = self.provider.azure_client.get_dns_zone(
                _strip_trailing_dot(dns_zone_id))
            return AzureDnsZone(self.provider, zone)
        except ResourceNotFoundError:
            return None

    @dispatch(event="provider.dns.host_zones.list",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        zones = [AzureDnsZone(self.provider, z)
                 for z in self.provider.azure_client.list_dns_zones()]
        return ClientPagedResultList(self.provider, zones, limit, marker)

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
        AzureDnsZone.assert_valid_resource_name(name)
        zone_name = _strip_trailing_dot(name)
        params = {
            # DNS zones in Azure are global resources but the API still
            # requires location='global'.
            'location': 'global',
            'tags': {'admin_email': admin_email},
        }
        zone = self.provider.azure_client.create_dns_zone(zone_name, params)
        return AzureDnsZone(self.provider, zone)

    @dispatch(event="provider.dns.host_zones.delete",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def delete(self, dns_zone):
        zone_name = (dns_zone.id if isinstance(dns_zone, AzureDnsZone)
                     else dns_zone)
        self.provider.azure_client.delete_dns_zone(
            _strip_trailing_dot(zone_name))


class AzureDnsRecordService(BaseDnsRecordService):

    def __init__(self, provider):
        super(AzureDnsRecordService, self).__init__(provider)

    def _to_record_params(self, rec_type, data, ttl):
        """Translate cloudbridge data to Azure record-set parameters."""
        # Local imports keep the module importable when azure-mgmt-dns
        # isn't installed (e.g. on AWS-only test environments).
        from azure.mgmt.dns.models import (AaaaRecord, ARecord, CnameRecord,
                                           MxRecord, NsRecord, PtrRecord,
                                           SrvRecord, TxtRecord)

        values = data if isinstance(data, list) else [data]
        params = {'ttl': ttl or 300}

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

    def get(self, dns_zone, rec_id):
        if not rec_id or ':' not in rec_id:
            return None
        rec_name, rec_type = rec_id.split(':', 1)
        try:
            rec = self.provider.azure_client.get_dns_record(
                dns_zone.id, rec_name, rec_type)
            return AzureDnsRecord(self.provider, dns_zone, rec)
        except ResourceNotFoundError:
            return None

    def list(self, dns_zone, limit=None, marker=None):
        records = [AzureDnsRecord(self.provider, dns_zone, r)
                   for r in self.provider.azure_client.list_dns_records(
                       dns_zone.id)]
        return ClientPagedResultList(self.provider, records, limit, marker)

    def find(self, dns_zone, **kwargs):
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, dns_zone.records)
        return ClientPagedResultList(self.provider, list(matches),
                                     limit=None, marker=None)

    def create(self, dns_zone, name, type, data, ttl=None):
        AzureDnsRecord.assert_valid_resource_name(name)
        relative_name = _to_relative_record_name(name, dns_zone.id)
        params = self._to_record_params(type, data, ttl)
        self.provider.azure_client.create_dns_record(
            dns_zone.id, relative_name, type, params)
        return self.get(dns_zone, relative_name + ':' + type)

    def delete(self, dns_zone, record):
        if isinstance(record, AzureDnsRecord):
            rec_name = record.name
            rec_type = record.type
        else:
            rec_name, rec_type = record.split(':', 1)
        self.provider.azure_client.delete_dns_record(
            dns_zone.id, rec_name, rec_type)
