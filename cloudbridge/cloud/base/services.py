"""
Base implementation for services available through a provider
"""
import logging

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.base.resources import BaseBucket
from cloudbridge.cloud.base.resources import BaseNetwork
from cloudbridge.cloud.base.resources import BaseRouter
from cloudbridge.cloud.base.resources import BaseSubnet
from cloudbridge.cloud.interfaces.exceptions import \
    InvalidConfigurationException
from cloudbridge.cloud.interfaces.resources import Network
from cloudbridge.cloud.interfaces.resources import Router
from cloudbridge.cloud.interfaces.services import BucketService
from cloudbridge.cloud.interfaces.services import BucketObjectService
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

    def __init__(self, provider):
        self._provider = provider
        self._service_event_name = "provider"

    @property
    def provider(self):
        return self._provider

    def _generate_event_name(self, func_name):
        return ".".join((self._service_event_name, func_name))

    def subscribe(self, func_name, priority, callback,
                  result_callback=False):
        event_name = self._generate_event_name(func_name)
        self.provider.events.subscribe(event_name, priority, callback,
                                       result_callback)

    def check_initialized(self, func_name):
        event_name = self._generate_event_name(func_name)
        return self.provider.events.check_initialized(event_name)

    def mark_initialized(self, func_name):
        event_name = self._generate_event_name(func_name)
        self.provider.events.mark_initialized(event_name)

    def call(self, func_name, priority, callback, **kwargs):
        event_name = self._generate_event_name(func_name)
        return self.provider.events.call(event_name, priority, callback,
                                         **kwargs)


class BaseSecurityService(SecurityService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSecurityService, self).__init__(provider)


class BaseKeyPairService(
        BasePageableObjectMixin, KeyPairService, BaseCloudService):

    def __init__(self, provider):
        super(BaseKeyPairService, self).__init__(provider)

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
        BasePageableObjectMixin, VMFirewallService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVMFirewallService, self).__init__(provider)

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


class BaseVolumeService(
        BasePageableObjectMixin, VolumeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVolumeService, self).__init__(provider)


class BaseSnapshotService(
        BasePageableObjectMixin, SnapshotService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSnapshotService, self).__init__(provider)


class BaseBucketService(
        BasePageableObjectMixin, BucketService, BaseCloudService):

    def __init__(self, provider):
        super(BaseBucketService, self).__init__(provider)
        self._service_event_name = "provider.storage.buckets"

    def _init_get(self):
        def _get_pre_log(bucket_id):
            log.debug("Getting {} bucket with the id: {}".format(
                self.provider.name, bucket_id))

        def _get_post_log(callback_result, bucket_id):
            log.debug("Returned bucket object: {}".format(callback_result))

        self.subscribe("get", 2000, _get_pre_log)
        self.subscribe("get", 3000, _get_post_log, result_callback=True)
        self.mark_initialized("get")

    def _init_find(self):
        def _find_pre_log(**kwargs):
            log.debug("Finding {} buckets with the following arguments: {}"
                      .format(self.provider.name, kwargs))

        def _find_post_log(callback_result, **kwargs):
            log.debug("Returned bucket objects: {}".format(callback_result))

        self.subscribe("find", 2000, _find_pre_log)
        self.subscribe("find", 3000, _find_post_log,
                       result_callback=True)
        self.mark_initialized("find")

    def _init_list(self):
            def _list_pre_log(limit, marker):
                message = "Listing {} buckets".format(self.provider.name)
                if limit:
                    message += " with limit: {}".format(limit)
                if marker:
                    message += " with marker: {}".format(marker)
                log.debug(message)

            def _list_post_log(callback_result, limit, marker):
                log.debug(
                    "Returned bucket objects: {}".format(callback_result))

            self.subscribe("list", 2000, _list_pre_log)
            self.subscribe("list", 3000, _list_post_log,
                           result_callback=True)
            self.mark_initialized("list")

    def _init_create(self):
        def _create_pre_log(name, location):
            message = "Creating {} bucket with name '{}'".format(
                self.provider.name, name)
            if location:
                message += " in location: {}".format(location)
            log.debug(message)

        def _create_post_log(callback_result, name, location):
            log.debug("Returned bucket object: {}".format(callback_result))

        self.subscribe("create", 2000, _create_pre_log)
        self.subscribe("create", 3000, _create_post_log,
                       result_callback=True)
        self.mark_initialized("create")

    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        if not self.check_initialized("get"):
            self._init_get()
        return self.call("get", priority=2500, callback=self._get,
                         bucket_id=bucket_id)

    # Generic find will be used for providers where we have not implemented
    # provider-specific querying for find method
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

    def find(self, **kwargs):
        """
        Returns a list of buckets filtered by the given keyword arguments.
        """
        if not self.check_initialized("find"):
            self._init_find()
        return self.call("find", priority=2500, callback=self._find,
                         **kwargs)

    def list(self, limit=None, marker=None):
        """
        List all buckets.
        """
        if not self.check_initialized("list"):
            self._init_list()
        return self.call("list", priority=2500, callback=self._list,
                         limit=limit, marker=marker)

    def create(self, name, location=None):
        """
        Create a new bucket.
        """
        if not self.check_initialized("create"):
            self._init_create()
        BaseBucket.assert_valid_resource_name(name)
        location = location or self.provider.region_name
        return self.call("create", priority=2500, callback=self._create,
                         name=name, location=location)


class BaseBucketObjectService(
        BasePageableObjectMixin, BucketObjectService, BaseCloudService):

    def __init__(self, provider):
        super(BaseBucketObjectService, self).__init__(provider)
        self._service_event_name = "provider.storage.bucket_objects"
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


class BaseImageService(
        BasePageableObjectMixin, ImageService, BaseCloudService):

    def __init__(self, provider):
        super(BaseImageService, self).__init__(provider)


class BaseInstanceService(
        BasePageableObjectMixin, InstanceService, BaseCloudService):

    def __init__(self, provider):
        super(BaseInstanceService, self).__init__(provider)


class BaseVMTypeService(
        BasePageableObjectMixin, VMTypeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVMTypeService, self).__init__(provider)

    def get(self, vm_type_id):
        vm_type = (t for t in self if t.id == vm_type_id)
        return next(vm_type, None)

    def find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseRegionService(
        BasePageableObjectMixin, RegionService, BaseCloudService):

    def __init__(self, provider):
        super(BaseRegionService, self).__init__(provider)

    def find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseNetworkingService(NetworkingService, BaseCloudService):

    def __init__(self, provider):
        super(BaseNetworkingService, self).__init__(provider)


class BaseNetworkService(
        BasePageableObjectMixin, NetworkService, BaseCloudService):

    def __init__(self, provider):
        super(BaseNetworkService, self).__init__(provider)

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
        BasePageableObjectMixin, SubnetService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSubnetService, self).__init__(provider)

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
        BasePageableObjectMixin, RouterService, BaseCloudService):

    def __init__(self, provider):
        super(BaseRouterService, self).__init__(provider)

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
