"""
Base implementation for services available through a provider
"""
import logging

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.base.events import execute
from cloudbridge.cloud.base.middleware import observe
from cloudbridge.cloud.base.resources import BaseBucket
from cloudbridge.cloud.base.resources import BaseNetwork
from cloudbridge.cloud.base.resources import BaseRouter
from cloudbridge.cloud.base.resources import BaseSubnet
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
        self._provider = provider
        # discover and register all middleware
        provider.middleware.add(self)

    @property
    def provider(self):
        return self._provider

    def emit(self, sender, event, *args, **kwargs):
        return self._provider.events.emit(sender, event, *args, **kwargs)

    def _generate_event_pattern(self, func_name):
        return ".".join((self._service_event_pattern, func_name))

    def observe(self, func_name, priority, callback):
        event_pattern = self._generate_event_pattern(func_name)
        self.provider.events.observe(event_pattern, priority, callback)

    def call(self, func_name, priority, callback, **kwargs):
        event_pattern = self._generate_event_pattern(func_name)
        return self.provider.events.call(event_pattern, priority, callback,
                                         **kwargs)


class BaseSecurityService(SecurityService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSecurityService, self).__init__(provider)
        self._service_event_pattern += ".security"


class BaseKeyPairService(
        BasePageableObjectMixin, KeyPairService, BaseSecurityService):

    def __init__(self, provider):
        super(BaseKeyPairService, self).__init__(provider)
        self._service_event_pattern += ".key_pairs"

    def delete(self, key_pair_id):
        """
        Delete an existing key pair.

        :type key_pair_id: str
        :param key_pair_id: The id of the key pair to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the key does not exist. Note that this implies
                  that the key may not have been deleted by this method but
                  instead has not existed in the first place.
        """
        log.info("Deleting the existing key pair %s", key_pair_id)
        kp = self.get(key_pair_id)
        if kp:
            kp.delete()
        return True


class BaseVMFirewallService(
        BasePageableObjectMixin, VMFirewallService, BaseSecurityService):

    def __init__(self, provider):
        super(BaseVMFirewallService, self).__init__(provider)
        self._service_event_pattern += ".vm_firewalls"

    def find(self, **kwargs):
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
        self._service_event_pattern += ".storage"


class BaseVolumeService(
        BasePageableObjectMixin, VolumeService, BaseStorageService):

    def __init__(self, provider):
        super(BaseVolumeService, self).__init__(provider)
        self._service_event_pattern += ".volumes"


class BaseSnapshotService(
        BasePageableObjectMixin, SnapshotService, BaseStorageService):

    def __init__(self, provider):
        super(BaseSnapshotService, self).__init__(provider)
        self._service_event_pattern += ".snapshots"


class BaseBucketService(
        BasePageableObjectMixin, BucketService, BaseStorageService):

    def __init__(self, provider):
        super(BaseBucketService, self).__init__(provider)
        self._service_event_pattern += ".buckets"

    @observe(event_pattern="provider.storage.buckets.get", priority=2000)
    def _pre_log_get(self, event_args, bucket_id):
        log.debug("Getting {} bucket with the id: {}".format(
            self.provider.name, bucket_id))

    @observe(event_pattern="provider.storage.buckets.get", priority=3000)
    def _post_log_get(self, event_args, bucket_id):
        log.debug("Returned bucket obj: {}".format(event_args.get('result')))

    @observe(event_pattern="provider.storage.buckets.find", priority=2000)
    def _pre_log_find(self, *args, **kwargs):
        log.debug("Finding {} buckets with the following arguments: {}"
                  .format(self.provider.name, kwargs))

    @observe(event_pattern="provider.storage.buckets.find", priority=3000)
    def _post_log_find(self, event_args, *args, **kwargs):
        log.debug("Returned bucket obj: {}".format(event_args.get('result')))

    def _list_pre_log(self, limit, marker):
        message = "Listing {} buckets".format(self.provider.name)
        if limit:
            message += " with limit: {}".format(limit)
        if marker:
            message += " with marker: {}".format(marker)
        log.debug(message)

    def _list_post_log(self, callback_result, limit, marker):
        log.debug("Returned bucket objects: {}".format(callback_result))

    def _create_pre_log(self, name, location):
        message = "Creating {} bucket with name '{}'".format(
            self.provider.name, name)
        if location:
            message += " in location: {}".format(location)
        log.debug(message)

    def _create_post_log(self, callback_result, name, location):
        log.debug("Returned bucket object: {}".format(callback_result))

    # Generic find will be used for providers where we have not implemented
    # provider-specific querying for find method
    @execute(event_pattern="provider.storage.buckets.find",
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
        """
        return self.emit(self, "provider.storage.buckets.get", bucket_id)

    def find(self, **kwargs):
        """
        Returns a list of buckets filtered by the given keyword arguments.
        """
        return self.emit(self, "provider.storage.buckets.find", **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all buckets.
        """
        return self.emit(self, "provider.storage.buckets.list",
                         limit=limit, marker=marker)

    def create(self, name, location=None):
        """
        Create a new bucket.
        """
        BaseBucket.assert_valid_resource_name(name)
        return self.emit(self, "provider.storage.buckets.create",
                         name, location=location)


class BaseBucketObjectService(
        BasePageableObjectMixin, BucketObjectService, BaseStorageService):

    def __init__(self, provider):
        super(BaseBucketObjectService, self).__init__(provider)
        self._service_event_pattern += ".bucket_objects"
        self._bucket = None

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
        self._service_event_pattern += ".compute"


class BaseImageService(
        BasePageableObjectMixin, ImageService, BaseComputeService):

    def __init__(self, provider):
        super(BaseImageService, self).__init__(provider)
        self._service_event_pattern += ".images"


class BaseInstanceService(
        BasePageableObjectMixin, InstanceService, BaseComputeService):

    def __init__(self, provider):
        super(BaseInstanceService, self).__init__(provider)
        self._service_event_pattern += ".instances"


class BaseVMTypeService(
        BasePageableObjectMixin, VMTypeService, BaseComputeService):

    def __init__(self, provider):
        super(BaseVMTypeService, self).__init__(provider)
        self._service_event_pattern += ".vm_types"

    def get(self, vm_type_id):
        vm_type = (t for t in self if t.id == vm_type_id)
        return next(vm_type, None)

    def find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseRegionService(
        BasePageableObjectMixin, RegionService, BaseComputeService):

    def __init__(self, provider):
        super(BaseRegionService, self).__init__(provider)
        self._service_event_pattern += ".regions"

    def find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseNetworkingService(NetworkingService, BaseCloudService):

    def __init__(self, provider):
        super(BaseNetworkingService, self).__init__(provider)
        self._service_event_pattern += ".networking"


class BaseNetworkService(
        BasePageableObjectMixin, NetworkService, BaseNetworkingService):

    def __init__(self, provider):
        super(BaseNetworkService, self).__init__(provider)
        self._service_event_pattern += ".networks"

    @property
    def subnets(self):
        return [subnet for subnet in self.provider.subnets
                if subnet.network_id == self.id]

    def delete(self, network_id):
        network = self.get(network_id)
        if network:
            log.info("Deleting network %s", network_id)
            network.delete()

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


class BaseSubnetService(
        BasePageableObjectMixin, SubnetService, BaseNetworkingService):

    def __init__(self, provider):
        super(BaseSubnetService, self).__init__(provider)
        self._service_event_pattern += ".subnets"

    def find(self, **kwargs):
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


class BaseRouterService(
        BasePageableObjectMixin, RouterService, BaseNetworkingService):

    def __init__(self, provider):
        super(BaseRouterService, self).__init__(provider)
        self._service_event_pattern += ".routers"

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
