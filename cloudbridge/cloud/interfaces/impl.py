"""
Specification for a provider interface
"""
from abc import ABCMeta, abstractmethod, abstractproperty


class CloudProvider(object):

    __metaclass__ = ABCMeta

    """
    Base interface for a cloud provider
    """

    @abstractmethod
    def __init__(self, config):
        """
        Create a new provider implementation given a dictionary of
        configuration attributes.

        :type config: an object with required fields
        :param config: This can be a Bunch or any other object whose fields can
                       be accessed using dot notation. See specific provider
                       implementation for the required fields.

        :rtype: ``object`` of :class:`.CloudProvider`
        :return:  a concrete provider instance
        """
        pass

    @abstractproperty
    def config(self):
        """
        Returns the config object associated with this provider.

        :rtype: ``object``
        :return:  The config object used to initialize this provider
        """

    @abstractmethod
    def has_service(self, service_type):
        """
        Checks whether this provider supports a given service.

        :type service_type: str or :class:``.CloudProviderServiceType``
        :param service_type: Type of service the check support for.

        :rtype: bool
        :return: ``True`` if the service type is supported.
        """
        pass

    @abstractproperty
    def account(self):
        """
        Provides access to all user account related services in this provider.
        This includes listing available tenancies.

        :rtype: ``object`` of :class:`.ComputeService`
        :return:  a ComputeService object
        """
        pass

    @abstractproperty
    def compute(self):
        """
        Provides access to all compute related services in this provider.

        :rtype: ``object`` of :class:`.ComputeService`
        :return:  a ComputeService object
        """
        pass

    @abstractproperty
    def security(self):
        """
        Provides access to keypair management and firewall control

        :rtype: ``object`` of :class:`.SecurityService`
        :return: a SecurityService object
        """
        pass

    @abstractproperty
    def block_store(self):
        """
        Provides access to the volume and snapshot services in this
        provider.

        :rtype: ``object`` of :class:`.BlockStoreService`
        :return: a BlockStoreService object
        """
        pass

    @abstractproperty
    def object_store(self):
        """
        Provides access to object storage services in this provider.

        :rtype: ``object`` of :class:`.ObjectStoreService`
        :return: an ObjectStoreService object
        """
        pass


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
