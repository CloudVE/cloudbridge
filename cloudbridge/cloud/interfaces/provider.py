"""
Specification for a provider interface
"""
from abc import ABCMeta, abstractmethod, abstractproperty


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
                       values. Alternatively, this can be a Bunch or any other
                       object whose fields can be accessed as members. See
                       specific provider implementation for the required
                       fields.

        :rtype: :class:`.CloudProvider`
        :return:  a concrete provider instance
        """
        pass

    @abstractproperty
    def config(self):
        """
        Returns the config object associated with this provider. This object
        is a subclass of :class:`dict` and will contain the properties
        provided at initialization time. In addition, it also contains extra
        provider-wide properties such as the default result limit for list()
        queries.

        Example:

        .. code-block:: python

            config = { 'aws_access_key' : '<my_key>' }
            provider = factory.create_provider(ProviderList.AWS, config)
            print(provider.config.get('aws_access_key'))
            print(provider.config.default_result_limit))
            # change provider result limit
            provider.config.default_result_limit = 100

        :rtype: :class:`.Configuration`
        :return:  An object of class Configuration, which contains the values
                  used to initialize the provider, as well as other global
                  configuration properties.
        """

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

            if provider.has_service(CloudServiceType.OBJECT_STORE):
               print("Provider supports object store services")
               provider.object_store.list()


        :type service_type: :class:`.CloudServiceType`
        :param service_type: Type of service to check support for.

        :rtype: :class:`bool`
        :return: ``True`` if the service type is supported.
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
            instance_types = provider.compute.instance_types.list()
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
    def network(self):
        """
        Provide access to all network related services in this provider.

        Example:

        .. code-block:: python

            networks = provider.network.list()
            network = provider.network.create(name="DevNet")

        :rtype: :class:`.NetworkService`
        :return:  a NetworkService object
        """

    @abstractproperty
    def security(self):
        """
        Provides access to key pair management and firewall control

        Example:

        .. code-block:: python

            keypairs = provider.security.keypairs.list()
            security_groups = provider.security.security_groups.list()


        :rtype: ``object`` of :class:`.SecurityService`
        :return: a SecurityService object
        """
        pass

    @abstractproperty
    def block_store(self):
        """
        Provides access to the volume and snapshot services in this
        provider.

        Example:

        .. code-block:: python

            volumes = provider.block_store.volumes.list()
            snapshots = provider.block_store.snapshots.list()

        :rtype: :class:`.BlockStoreService`
        :return: a BlockStoreService object
        """
        pass

    @abstractproperty
    def object_store(self):
        """
        Provides access to object storage services in this provider.

        Example:

        .. code-block:: python

            if provider.has_service(CloudServiceType.OBJECT_STORE):
               print("Provider supports object store services")
               print(provider.object_store.list())

        :rtype: ``object`` of :class:`.ObjectStoreService`
        :return: an ObjectStoreService object
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
