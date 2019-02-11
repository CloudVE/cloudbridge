"""
Base implementation for services available through a provider
"""
import logging

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.base.middleware import implement
from cloudbridge.cloud.base.resources import BaseBucket
from cloudbridge.cloud.base.resources import BaseInstance
from cloudbridge.cloud.base.resources import BaseKeyPair
from cloudbridge.cloud.base.resources import BaseNetwork
from cloudbridge.cloud.base.resources import BaseRouter
from cloudbridge.cloud.base.resources import BaseSnapshot
from cloudbridge.cloud.base.resources import BaseSubnet
from cloudbridge.cloud.base.resources import BaseVMFirewall
from cloudbridge.cloud.base.resources import BaseVolume
from cloudbridge.cloud.interfaces.exceptions import \
    InvalidConfigurationException
from cloudbridge.cloud.interfaces.resources import Network
from cloudbridge.cloud.interfaces.resources import Router
from cloudbridge.cloud.interfaces.services import BucketObjectService
from cloudbridge.cloud.interfaces.services import BucketService
from cloudbridge.cloud.interfaces.services import CloudService
from cloudbridge.cloud.interfaces.services import ComputeService
from cloudbridge.cloud.interfaces.services import ImageService
from cloudbridge.cloud.interfaces.services import InstanceService
from cloudbridge.cloud.interfaces.services import KeyPairService
from cloudbridge.cloud.interfaces.services import NetworkService
from cloudbridge.cloud.interfaces.services import NetworkingService
from cloudbridge.cloud.interfaces.services import RegionService
from cloudbridge.cloud.interfaces.services import RouterService
from cloudbridge.cloud.interfaces.services import SecurityService
from cloudbridge.cloud.interfaces.services import SnapshotService
from cloudbridge.cloud.interfaces.services import StorageService
from cloudbridge.cloud.interfaces.services import SubnetService
from cloudbridge.cloud.interfaces.services import VMFirewallService
from cloudbridge.cloud.interfaces.services import VMTypeService
from cloudbridge.cloud.interfaces.services import VolumeService

from .resources import BasePageableObjectMixin
from .resources import ClientPagedResultList

log = logging.getLogger(__name__)


class BaseCloudService(CloudService):

    STANDARD_EVENT_PRIORITY = 2500

    def __init__(self, provider):
        self._service_event_pattern = "provider"
        self._provider = provider
        # discover and register all middleware
        provider.middleware.add(self)

    @property
    def provider(self):
        return self._provider

    def dispatch(self, sender, event, *args, **kwargs):
        return self._provider.events.dispatch(sender, event, *args, **kwargs)

    def _generate_event_pattern(self, func_name):
        return ".".join((self._service_event_pattern, func_name))

    def observe_function(self, func_name, priority, callback):
        event_pattern = self._generate_event_pattern(func_name)
        self.provider.events.observe(event_pattern, priority, callback)

    def intercept_function(self, func_name, priority, callback):
        event_pattern = self._generate_event_pattern(func_name)
        self.provider.events.intercept(event_pattern, priority, callback)

    def implement_function(self, func_name, priority, callback):
        event_pattern = self._generate_event_pattern(func_name)
        self.provider.events.implement(event_pattern, priority, callback)

    def dispatch_function(self, sender, func_name, *args, **kwargs):
        """
        Emits the event corresponding to the given function name for the
        current service

        :type sender: CloudService
        :param sender: The CloudBridge Service object sending the emit signal
        :type func_name: str
        :param func_name: The name of the function to be emitted. e.g.: 'get'
        :type args: CloudService

        :return:  The return value resulting from the handler chain invocations
        """
        full_event_name = self._generate_event_pattern(func_name)
        return self._provider.events.dispatch(sender, full_event_name,
                                              *args, **kwargs)


class BaseSecurityService(SecurityService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSecurityService, self).__init__(provider)


class BaseKeyPairService(
        BasePageableObjectMixin, KeyPairService, BaseCloudService):

    def __init__(self, provider):
        super(BaseKeyPairService, self).__init__(provider)
        self._service_event_pattern += ".security.key_pairs"

    def get(self, key_pair_id):
        """
        Returns a key_pair given its ID. Returns ``None`` if the key_pair
        does not exist.

        :type key_pair_id: str
        :param key_pair_id: The id of the desired key pair.

        :rtype: ``KeyPair``
        :return:  ``None`` is returned if the key pair does not exist, and
                  the key pair's provider-specific CloudBridge object is
                  returned if the key pair is found.
        """
        return self.dispatch(self, "provider.security.key_pairs.get",
                             key_pair_id)

    def find(self, **kwargs):
        """
        Returns a list of key pairs filtered by the given keyword arguments.
        Accepted search arguments are: 'name'
        """
        return self.dispatch(self, "provider.security.key_pairs.find",
                             **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all key pairs.
        """
        return self.dispatch(self, "provider.security.key_pairs.list",
                             limit=limit, marker=marker)

    def create(self, name, public_key_material=None):
        """
        Create a new key pair.

        :type name: str
        :param name: The name of the key pair to be created. Note that names
                     must be unique, and are unchangeable.

        :rtype: ``KeyPair``
        :return:  The created key pair's provider-specific CloudBridge object.
        """
        BaseKeyPair.assert_valid_resource_name(name)
        return self.dispatch(self, "provider.security.key_pairs.create",
                             name,  public_key_material=public_key_material)

    def delete(self, key_pair_id):
        """
        Delete an existing key pair.

        :type key_pair_id: str
        :param key_pair_id: The ID of the key pair to be deleted.
        """
        return self.dispatch(self, "provider.security.key_pairs.delete",
                             key_pair_id)


class BaseVMFirewallService(
        BasePageableObjectMixin, VMFirewallService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVMFirewallService, self).__init__(provider)
        self._service_event_pattern += ".security.vm_firewalls"

    def get(self, vm_firewall_id):
        """
        Returns a vm_firewall given its ID. Returns ``None`` if the vm_firewall
        does not exist.

        :type vm_firewall_id: str
        :param vm_firewall_id: The id of the desired firewall.

        :rtype: ``VMFirewall``
        :return:  ``None`` is returned if the firewall does not exist, and
                  the firewall's provider-specific CloudBridge object is
                  returned if the firewall is found.
        """
        return self.dispatch(self, "provider.security.vm_firewalls.get",
                             vm_firewall_id)

    def find(self, **kwargs):
        """
        Returns a list of firewalls filtered by the given keyword arguments.
        Accepted search arguments are: 'label'
        """
        return self.dispatch(self, "provider.security.vm_firewalls.find",
                             **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all firewalls.
        """
        return self.dispatch(self, "provider.security.vm_firewalls.list",
                             limit=limit, marker=marker)

    def create(self, label, network, description=None):
        """
        Create a new firewall.

        :type label: str
        :param label: The label of the firewall to be created. Note that labels
                     do not have to be unique, and are changeable.

        :rtype: ``VMFirewall``
        :return:  The created firewall's provider-specific CloudBridge object.
        """
        BaseVMFirewall.assert_valid_resource_label(label)
        return self.dispatch(self, "provider.security.vm_firewalls.create",
                             label, network, description)

    def delete(self, vm_firewall_id):
        """
        Delete an existing firewall.

        :type vm_firewall_id: str
        :param vm_firewall_id: The ID of the firewall to be deleted.
        """
        return self.dispatch(self, "provider.security.vm_firewalls.delete",
                             vm_firewall_id)

    @implement(event_pattern="provider.security.vm_firewalls.find",
               priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        obj_list = self
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs,
                                                           ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])


class BaseStorageService(StorageService, BaseCloudService):

    def __init__(self, provider):
        super(BaseStorageService, self).__init__(provider)


class BaseVolumeService(
        BasePageableObjectMixin, VolumeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVolumeService, self).__init__(provider)
        self._service_event_pattern += ".storage.volumes"

    def get(self, volume_id):
        """
        Returns a volume given its ID. Returns ``None`` if the volume
        does not exist.

        :type volume_id: str
        :param volume_id: The id of the desired volume.

        :rtype: ``Volume``
        :return:  ``None`` is returned if the volume does not exist, and
                  the volume's provider-specific CloudBridge object is
                  returned if the volume is found.
        """
        return self.dispatch(self, "provider.storage.volumes.get",
                             volume_id)

    def find(self, **kwargs):
        """
        Returns a list of volumes filtered by the given keyword arguments.
        Accepted search arguments are: 'label'
        """
        return self.dispatch(self, "provider.storage.volumes.find",
                             **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all volumes.
        """
        return self.dispatch(self, "provider.storage.volumes.list",
                             limit=limit, marker=marker)

    def create(self, label, size, zone, description=None, snapshot=None):
        """
        Create a new volume.

        :type label: str
        :param label: The label of the volume to be created. Note that labels
                     do not have to be unique, and are changeable.
        :type size: int
        :param size: The size (in Gb) of the volume to be created
        :type zone: ``PlacementZone``
        :param zone: The availability zone in which to create the volume

        :rtype: ``Volume``
        :return:  The created volume's provider-specific CloudBridge object.
        """
        BaseVolume.assert_valid_resource_label(label)
        return self.dispatch(self, "provider.storage.volumes.create",
                             label, size, zone, description, snapshot)

    def delete(self, volume_id):
        """
        Delete an existing volume.

        :type volume_id: str
        :param volume_id: The ID of the volume to be deleted.
        """
        return self.dispatch(self, "provider.storage.volumes.delete",
                             volume_id)


class BaseSnapshotService(
        BasePageableObjectMixin, SnapshotService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSnapshotService, self).__init__(provider)
        self._service_event_pattern += ".storage.snapshots"

    def get(self, snapshot_id):
        """
        Returns a snapshot given its ID. Returns ``None`` if the snapshot
        does not exist.

        :type snapshot_id: str
        :param snapshot_id: The id of the desired snapshot.

        :rtype: ``Snapshot``
        :return:  ``None`` is returned if the snapshot does not exist, and
                  the snapshot's provider-specific CloudBridge object is
                  returned if the snapshot is found.
        """
        return self.dispatch(self, "provider.storage.snapshots.get",
                             snapshot_id)

    def find(self, **kwargs):
        """
        Returns a list of snapshots filtered by the given keyword arguments.
        Accepted search arguments are: 'label'
        """
        return self.dispatch(self, "provider.storage.snapshots.find",
                             **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all snapshots.
        """
        return self.dispatch(self, "provider.storage.snapshots.list",
                             limit=limit, marker=marker)

    def create(self, label, volume, description=None):
        """
        Create a new snapshot.

        :type label: str
        :param label: The label of the snapshot to be created. Note that labels
                     do not have to be unique, and are changeable.
        :type volume: ``Volume``
        :param volume: The volume from which to create this snapshot.

        :rtype: ``Snapshot``
        :return:  The created snapshot's provider-specific CloudBridge object.
        """
        BaseSnapshot.assert_valid_resource_label(label)
        return self.dispatch(self, "provider.storage.snapshots.create",
                             label, volume, description)

    def delete(self, snapshot_id):
        """
        Delete an existing snapshot.

        :type snapshot_id: str
        :param snapshot_id: The ID of the snapshot to be deleted.
        """
        return self.dispatch(self, "provider.storage.snapshots.delete",
                             snapshot_id)


class BaseBucketService(
        BasePageableObjectMixin, BucketService, BaseCloudService):

    def __init__(self, provider):
        super(BaseBucketService, self).__init__(provider)
        self._service_event_pattern += ".storage.buckets"

    # Generic find will be used for providers where we have not implemented
    # provider-specific querying for find method
    @implement(event_pattern="*.storage.buckets.find",
               priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs,
                                                           ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.

        :type bucket_id: str
        :param bucket_id: The id of the desired bucket.

        :rtype: ``Bucket``
        :return:  ``None`` is returned if the bucket does not exist, and
                  the bucket's provider-specific CloudBridge object is
                  returned if the bucket is found.
        """
        return self.dispatch(self, "provider.storage.buckets.get", bucket_id)

    def find(self, **kwargs):
        """
        Returns a list of buckets filtered by the given keyword arguments.
        Accepted search arguments are: 'name'
        """
        return self.dispatch(self, "provider.storage.buckets.find", **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all buckets.
        """
        return self.dispatch(self, "provider.storage.buckets.list",
                             limit=limit, marker=marker)

    def create(self, name, location=None):
        """
        Create a new bucket.

        :type name: str
        :param name: The name of the bucket to be created. Note that names
                     must be unique, and are unchangeable.

        :rtype: ``Bucket``
        :return:  The created bucket's provider-specific CloudBridge object.
        """
        BaseBucket.assert_valid_resource_name(name)
        return self.dispatch(self, "provider.storage.buckets.create",
                             name, location=location)

    def delete(self, bucket_id):
        """
        Delete an existing bucket.

        :type bucket_id: str
        :param bucket_id: The ID of the bucket to be deleted.
        """
        return self.dispatch(self, "provider.storage.buckets.delete",
                             bucket_id)


class BaseBucketObjectService(
        BasePageableObjectMixin, BucketObjectService, BaseCloudService):

    def __init__(self, provider):
        super(BaseBucketObjectService, self).__init__(provider)
        self._service_event_pattern += ".storage.bucket_objects"
        self._bucket = None

    # Default bucket needs to be set in order for the service to be iterable
    def set_bucket(self, bucket):
        bucket = bucket if isinstance(bucket, BaseBucket) \
                 else self.provider.storage.buckets.get(bucket)
        self._bucket = bucket

    def __iter__(self):
        if not self._bucket:
            message = "You must set a bucket before iterating through its " \
                      "objects. We do not allow iterating through all " \
                      "buckets at this time. In order to set a bucket, use: " \
                      "`provider.storage.bucket_objects.set_bucket(my_bucket)`"
            raise InvalidConfigurationException(message)
        result_list = self.list(bucket=self._bucket)
        if result_list.supports_server_paging:
            for result in result_list:
                yield result
            while result_list.is_truncated:
                result_list = self.list(bucket=self._bucket,
                                        marker=result_list.marker)
                for result in result_list:
                    yield result
        else:
            for result in result_list.data:
                yield result


class BaseComputeService(ComputeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseComputeService, self).__init__(provider)


class BaseImageService(
        BasePageableObjectMixin, ImageService, BaseCloudService):

    def __init__(self, provider):
        super(BaseImageService, self).__init__(provider)
        self._service_event_pattern += ".compute.images"


class BaseInstanceService(
        BasePageableObjectMixin, InstanceService, BaseCloudService):

    def __init__(self, provider):
        super(BaseInstanceService, self).__init__(provider)
        self._service_event_pattern += ".compute.instances"

    def get(self, instance_id):
        """
        Returns a instance given its ID. Returns ``None`` if the instance
        does not exist.

        :type instance_id: str
        :param instance_id: The id of the desired instance.

        :rtype: ``Instance``
        :return:  ``None`` is returned if the instance does not exist, and
                  the instance's provider-specific CloudBridge object is
                  returned if the instance is found.
        """
        return self.dispatch(self, "provider.compute.instances.get",
                             instance_id)

    def find(self, **kwargs):
        """
        Returns a list of instances filtered by the given keyword arguments.
        Accepted search arguments are: 'label'
        """
        return self.dispatch(self, "provider.compute.instances.find",
                             **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all instances.
        """
        return self.dispatch(self, "provider.compute.instances.list",
                             limit=limit, marker=marker)

    def create(self, label, image, vm_type, subnet, zone,
               key_pair=None, vm_firewalls=None, user_data=None,
               launch_config=None, **kwargs):
        """
        Create a new instance.

        :type label: str
        :param label: The label of the instance to be created. Note that labels
                     do not have to be unique, and are changeable.
        :type image: ``MachineImage``
        :param image: The image to be used when creating the instance
        :type vm_type: ``VMType``
        :param vm_type: The type of virtual machine desired for this instance
        :type subnet: ``Subnet``
        :param subnet: The subnet to which the instance should be attached
        :type zone: ``PlacementZone``
        :param zone: The zone in which to place the instance

        :rtype: ``Instance``
        :return:  The created instance's provider-specific CloudBridge object.
        """
        BaseInstance.assert_valid_resource_label(label)
        return self.dispatch(self, "provider.compute.instances.create",
                             label, image, vm_type, subnet, zone,
                             key_pair=key_pair, vm_firewalls=vm_firewalls,
                             user_data=user_data, launch_config=launch_config,
                             **kwargs)

    def delete(self, instance_id):
        """
        Delete an existing instance.

        :type instance_id: str
        :param instance_id: The ID of the instance to be deleted.
        """
        return self.dispatch(self, "provider.compute.instances.delete",
                             instance_id)


class BaseVMTypeService(
        BasePageableObjectMixin, VMTypeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVMTypeService, self).__init__(provider)
        self._service_event_pattern += ".compute.vm_types"

    @implement(event_pattern="provider.compute.vm_types.get",
               priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def _get(self, vm_type_id):
        vm_type = (t for t in self if t.id == vm_type_id)
        return next(vm_type, None)

    @implement(event_pattern="provider.compute.vm_types.find",
               priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def get(self, vm_type_id):
        """
        Returns a vm_type given its ID. Returns ``None`` if the vm_type
        does not exist.

        :type vm_type_id: str
        :param vm_type_id: The id of the desired VM type.

        :rtype: ``VMType``
        :return:  ``None`` is returned if the VM type does not exist, and
                  the VM type's provider-specific CloudBridge object is
                  returned if the VM type is found.
        """
        return self.dispatch(self, "provider.compute.vm_types.get",
                             vm_type_id)

    def find(self, **kwargs):
        """
        Returns a list of VM types filtered by the given keyword arguments.
        Accepted search arguments are: 'name'
        """
        return self.dispatch(self, "provider.compute.vm_types.find",
                             **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all VM types.
        """
        return self.dispatch(self, "provider.compute.vm_types.list",
                             limit=limit, marker=marker)


class BaseRegionService(
        BasePageableObjectMixin, RegionService, BaseCloudService):

    def __init__(self, provider):
        super(BaseRegionService, self).__init__(provider)
        self._service_event_pattern += ".compute.regions"

    @implement(event_pattern="provider.compute.regions.find",
               priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def get(self, region_id):
        """
        Returns a region given its ID. Returns ``None`` if the region
        does not exist.

        :type region_id: str
        :param region_id: The id of the desired region.

        :rtype: ``Region``
        :return:  ``None`` is returned if the region does not exist, and
                  the region's provider-specific CloudBridge object is
                  returned if the region is found.
        """
        return self.dispatch(self, "provider.compute.regions.get",
                             region_id)

    def find(self, **kwargs):
        """
        Returns a list of regions filtered by the given keyword arguments.
        Accepted search arguments are: 'name'
        """
        return self.dispatch(self, "provider.compute.regions.find",
                             **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all regions.
        """
        return self.dispatch(self, "provider.compute.regions.list",
                             limit=limit, marker=marker)


class BaseNetworkingService(NetworkingService, BaseCloudService):

    def __init__(self, provider):
        super(BaseNetworkingService, self).__init__(provider)


class BaseNetworkService(
        BasePageableObjectMixin, NetworkService, BaseCloudService):

    def __init__(self, provider):
        super(BaseNetworkService, self).__init__(provider)
        self._service_event_pattern += ".networking.networks"

    @property
    def subnets(self):
        return [subnet for subnet in self.provider.subnets
                if subnet.network_id == self.id]

    def get_or_create_default(self):
        networks = self.provider.networking.networks.find(
            label=BaseNetwork.CB_DEFAULT_NETWORK_LABEL)

        if networks:
            return networks[0]
        else:
            log.info("Creating a CloudBridge-default network labeled %s",
                     BaseNetwork.CB_DEFAULT_NETWORK_LABEL)
            return self.provider.networking.networks.create(
                BaseNetwork.CB_DEFAULT_NETWORK_LABEL, '10.0.0.0/16')

    @implement(event_pattern="provider.networking.networks.find",
               priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        obj_list = self
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs,
                                                           ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    def get(self, network_id):
        """
        Returns a network given its ID. Returns ``None`` if the network
        does not exist.

        :type network_id: str
        :param network_id: The id of the desired network.

        :rtype: ``network``
        :return:  ``None`` is returned if the network does not exist, and
                  the network's provider-specific CloudBridge object is
                  returned if the network is found.
        """
        return self.dispatch(self, "provider.networking.networks.get",
                             network_id)

    def find(self, **kwargs):
        """
        Returns a list of networks filtered by the given keyword arguments.
        Accepted search arguments are: 'label'
        """
        return self.dispatch(self, "provider.networking.networks.find",
                             **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all networks.
        """
        return self.dispatch(self, "provider.networking.networks.list",
                             limit=limit, marker=marker)

    def create(self, label, cidr_block):
        """
        Create a new network.

        :type label: str
        :param label: The label of the network to be created. Note that labels
                      do not have to be unique and can be changed.
        :type cidr_block: str
        :param cidr_block: A string representing a 'Classless Inter-Domain
                           Routing' notation

        :rtype: ``Network``
        :return:  The created network's provider-specific CloudBridge object.
        """
        BaseNetwork.assert_valid_resource_label(label)
        return self.dispatch(self, "provider.networking.networks.create",
                             label, cidr_block)

    def delete(self, network_id):
        """
        Delete an existing network.

        :type network_id: str
        :param network_id: The ID of the network to be deleted.
        """
        return self.dispatch(self, "provider.networking.networks.delete",
                             network_id)


class BaseSubnetService(
        BasePageableObjectMixin, SubnetService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSubnetService, self).__init__(provider)
        self._service_event_pattern += ".networking.subnets"

    @implement(event_pattern="provider.networking.subnets.find",
               priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        obj_list = self
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def get_or_create_default(self, zone):
        # Look for a CB-default subnet
        matches = self.find(label=BaseSubnet.CB_DEFAULT_SUBNET_LABEL)
        if matches:
            return matches[0]

        # No provider-default Subnet exists, try to create it (net + subnets)
        network = self.provider.networking.networks.get_or_create_default()
        subnet = self.create(BaseSubnet.CB_DEFAULT_SUBNET_LABEL, network,
                             BaseSubnet.CB_DEFAULT_SUBNET_IPV4RANGE, zone)
        return subnet

    def get(self, subnet_id):
        """
        Returns a subnet given its ID. Returns ``None`` if the subnet
        does not exist.

        :type subnet_id: str
        :param subnet_id: The id of the desired subnet.

        :rtype: ``Subnet``
        :return:  ``None`` is returned if the subnet does not exist, and
                  the subnet's provider-specific CloudBridge object is
                  returned if the subnet is found.
        """
        return self.dispatch(self, "provider.networking.subnets.get",
                             subnet_id)

    def find(self, network=None, **kwargs):
        """
        Returns a list of subnets filtered by the given keyword arguments.
        Accepted search arguments are: 'label'
        """
        return self.dispatch(self, "provider.networking.subnets.find",
                             network=network, **kwargs)

    def list(self, network=None, limit=None, marker=None):
        """
        List all subnets.
        """
        return self.dispatch(self, "provider.networking.subnets.list",
                             network=network, limit=limit, marker=marker)

    def create(self, label, network, cidr_block, zone):
        """
        Create a new subnet.

        :type label: str
        :param label: The label of the subnet to be created. Note that labels
                      do not have to be unique and can be changed.
        :type network: ``Network``
        :param network: The network in which the subnet should be created
        :type cidr_block: str
        :param cidr_block: A string representing a 'Classless Inter-Domain
                           Routing' notation
        :type cidr_block: str
        :param cidr_block: A string representing a 'Classless Inter-Domain
                           Routing' notation
        :type zone: ``PlacementZone``
        :param zone: The availability zone in which to create the subnet

        :rtype: ``Subnet``
        :return:  The created subnet's provider-specific CloudBridge object.
        """
        BaseSubnet.assert_valid_resource_label(label)
        return self.dispatch(self, "provider.networking.subnets.create",
                             label, network, cidr_block, zone)

    def delete(self, subnet_id):
        """
        Delete an existing subnet.

        :type subnet_id: str
        :param subnet_id: The ID of the subnet to be deleted.
        """
        return self.dispatch(self, "provider.networking.subnets.delete",
                             subnet_id)


class BaseRouterService(
        BasePageableObjectMixin, RouterService, BaseCloudService):

    def __init__(self, provider):
        super(BaseRouterService, self).__init__(provider)
        self._service_event_pattern += ".networking.routers"

    def delete(self, router):
        if isinstance(router, Router):
            log.info("Router %s successful deleted.", router)
            router.delete()
        else:
            log.info("Getting router %s", router)
            router = self.get(router)
            if router:
                log.info("Router %s successful deleted.", router)
                router.delete()

    def get_or_create_default(self, network):
        net_id = network.id if isinstance(network, Network) else network
        routers = self.provider.networking.routers.find(
            label=BaseRouter.CB_DEFAULT_ROUTER_LABEL)
        for router in routers:
            if router.network_id == net_id:
                return router
        else:
            return self.provider.networking.routers.create(
                network=net_id, label=BaseRouter.CB_DEFAULT_ROUTER_LABEL)
