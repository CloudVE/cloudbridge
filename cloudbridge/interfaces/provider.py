"""
Specification for a provider interface
"""
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty


class CloudProvider(object):
    """
    Base interface for a cloud provider
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, config):
        """
        Create a new provider instance given a dictionary of
        configuration attributes.

        :type config: :class:`dict`
        :param config: A dictionary object containing provider initialization
                       values. Alternatively, this can be an iterable of
                       key/value pairs (as tuples or other iterables of length
                       two). See specific provider implementation for the
                       required fields.

        :rtype: :class:`.CloudProvider`
        :return:  a concrete provider instance
        """
        pass

    @abstractproperty
    def config(self):
        """
        Returns the config object associated with this provider. This object
        is a subclass of :class:`dict` and will contain the properties
        provided at initialization time, grouped under `cloud_properties` and
        `credentials` keys. In addition, it also contains extra provider-wide
        properties such as the default result limit for `list()` queries.

        Example:

        .. code-block:: python

            config = { 'aws_access_key' : '<my_key>' }
            provider = factory.create_provider(ProviderList.AWS, config)
            print(provider.config['credentials'].get('aws_access_key'))
            print(provider.config.default_result_limit))
            # change provider result limit
            provider.config.default_result_limit = 100

        :rtype: :class:`.Configuration`
        :return:  An object of class Configuration, which contains the values
                  used to initialize the provider, as well as other global
                  configuration properties.
        """
        pass

    @abstractproperty
    def middleware(self):
        """
        Returns the middleware manager associated with this provider. The
        middleware manager can be used to add or remove middleware from
        cloudbridge. Refer to pyeventsystem documentation for more information
        on how the middleware manager works.

        :rtype: :class:`.MiddlewareManager`
        :return:  An object of class MiddlewareManager, which can be used to
        add or remove middleware from cloudbridge.
        """
        pass

    @abstractmethod
    def clone(self, zone=None):
        """
        Create a clone of this provider. An optional `zone` parameter can be
        used to clone the provider to use a different zone.
        As each cloudbridge provider is restricted to a particular zone,
        this is useful when performing cross-zonal operations.

        Example:

        .. code-block:: python

            # list instances in all availability zones
            all_instances = []
            for zone in provider.compute.regions.current.zones:
                new_provider = provider.clone(zone=zone)
                all_instances.append(list(new_provider.compute.instances))
            print(all_instances)

        :param zone: Changes the provider's zone to the requested
                     AvailabilityZone
        :type zone: :class:`.PlacementZone` object

        :rtype: :class:`.CloudProvider`
        :return:  A clone of the CloudProvider, with zone changed to the
                  requested zone.
        """
        pass

    @abstractmethod
    def authenticate(self):
        """
        Checks whether a provider can be successfully authenticated with the
        configured settings. Clients are *not* required to call this method
        prior to accessing provider services, as most cloud connections are
        initialized lazily. The authenticate() method will return True if
        cloudbridge can establish a successful connection to the provider.
        It will raise an exception with the appropriate error details
        otherwise.

        Example:

        .. code-block:: python

            try:
                if provider.authenticate():
                   print("Provider connection successful")
            except ProviderConnectionException as e:
                print("Could not authenticate with provider: %s" % (e, ))

        :rtype: :class:`bool`
        :return: ``True`` if authentication is successful.
        """
        pass

    @abstractmethod
    def has_service(self, service_type):
        """
        Checks whether this provider supports a given service.

        Example:

        .. code-block:: python

            if provider.has_service(CloudServiceType.BUCKET):
               print("Provider supports object store services")
               provider.storage.buckets.list()


        :type service_type: :class:`.CloudServiceType`
        :param service_type: Type of service to check support for.

        :rtype: :class:`bool`
        :return: ``True`` if the service type is supported.
        """
        pass

    @abstractproperty
    def region_name(self):
        """
        Returns the region that this provider is connected to.
        All provider operations will take place within this region.

        :rtype: ``str``
        :return:  a zone id
        """
        pass

    @abstractproperty
    def zone_name(self):
        """
        Returns the placement zone that this provider is connected to.
        All provider operations will take place within this zone. Placement
        zone must be within the provider default region.

        :rtype: ``str``
        :return:  a zone id
        """
        pass

#     @abstractproperty
#     def account(self):
#         """
#         Provides access to all user account related services in this
#         provider. This includes listing available tenancies.
#
#         :rtype: ``object`` of :class:`.ComputeService`
#         :return:  a ComputeService object
#         """
#         pass

    @abstractproperty
    def compute(self):
        """
        Provides access to all compute related services in this provider.

        Example:

        .. code-block:: python

            regions = provider.compute.regions.list()
            vm_types = provider.compute.vm_types.list()
            instances = provider.compute.instances.list()
            images = provider.compute.images.list()

            # Alternatively
            for instance in provider.compute.instances:
               print(instance.name)

        :rtype: :class:`.ComputeService`
        :return:  a ComputeService object
        """
        pass

    @abstractproperty
    def networking(self):
        """
        Provide access to all network related services in this provider.

        Example:

        .. code-block:: python

            networks = provider.networking.networks.list()
            subnets = provider.networking.subnets.list()
            routers = provider.networking.routers.list()

        :rtype: :class:`.NetworkingService`
        :return:  a NetworkingService object
        """

    @abstractproperty
    def security(self):
        """
        Provides access to key pair management and firewall control

        Example:

        .. code-block:: python

            keypairs = provider.security.keypairs.list()
            vm_firewalls = provider.security.vm_firewalls.list()


        :rtype: ``object`` of :class:`.SecurityService`
        :return: a SecurityService object
        """
        pass

    @abstractproperty
    def storage(self):
        """
        Provides access to storage related services in this provider.
        This includes the volume, snapshot and bucket services,

        Example:

        .. code-block:: python

            volumes = provider.storage.volumes.list()
            snapshots = provider.storage.snapshots.list()
            if provider.has_service(CloudServiceType.BUCKET):
               print("Provider supports object store services")
               print(provider.storage.buckets.list())

        :rtype: :class:`.StorageService`
        :return: a StorageService object
        """
        pass

    @abstractproperty
    def dns(self):
        """
        Provides access to all DNS related services.

        Example:

        .. code-block:: python

            if provider.has_service(CloudServiceType.DNS):
               print("Provider supports DNS services")
               dns_zones = provider.dns.host_zones.list()
               print(dns_zones)

        :rtype: :class:`.DnsService`
        :return: a DNS service object
        """
        pass


class TestMockHelperMixin(object):
    """
    A helper class that providers mock drivers can use to be notified when a
    test setup/teardown occurs. This is useful when activating libraries
    like HTTPretty which take over socket communications.
    """

    def setUpMock(self):
        """
        Called before a test is started.
        """
        raise NotImplementedError(
            'TestMockHelperMixin.setUpMock not implemented')

    def tearDownMock(self):
        """
        Called before test teardown.
        """
        raise NotImplementedError(
            'TestMockHelperMixin.tearDownMock not implemented by this'
            ' provider')


class ContainerProvider(object):

    """
    Represents a container instance, such as Docker or LXC
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def create_container(self):
        pass

    @abstractmethod
    def delete_container(self):
        pass


class DeploymentProvider(object):

    """
    Represents a deployment provider, such as Ansible or Shell script provider
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def deploy(self, target):
        """
        Deploys on given target, where target is an Instance or Container
        """
        pass
