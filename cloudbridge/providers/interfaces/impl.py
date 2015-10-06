"""
Specification for a provider interface
"""


class CloudProvider(object):

    """
    Base interface for a cloud provider
    """

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
        raise NotImplementedError(
            '__init__ not implemented by this provider')

    @property
    def config(self):
        """
        Returns the config object associated with this provider.

        :rtype: ``object``
        :return:  The config object used to initialize this provider
        """
        raise NotImplementedError(
            'CloudProvider.config not implemented by this provider')

    def has_service(self, service_type):
        """
        Checks whether this provider supports a given service.

        :type service_type: str or :class:``.CloudProviderServiceType``
        :param service_type: Type of service the check support for.

        :rtype: bool
        :return: ``True`` if the service type is supported.
        """
        raise NotImplementedError(
            'CloudProvider.has_service not implemented by this provider')

    @property
    def account(self):
        """
        Provides access to all user account related services in this provider.
        This includes listing available tenancies.

        :rtype: ``object`` of :class:`.ComputeService`
        :return:  a ComputeService object
        """
        raise NotImplementedError(
            'CloudProvider.Compute not implemented by this provider')

    @property
    def compute(self):
        """
        Provides access to all compute related services in this provider.

        :rtype: ``object`` of :class:`.ComputeService`
        :return:  a ComputeService object
        """
        raise NotImplementedError(
            'CloudProvider.compute not implemented by this provider')

    @property
    def images(self):
        """
        Provides access to all Image related services in this provider.
        (e.g. Glance in Openstack)

        :rtype: ``object`` of :class:`.ImageService`
        :return: an ImageService object
        """
        raise NotImplementedError(
            'CloudProvider.images not implemented by this provider')

    @property
    def security(self):
        """
        Provides access to keypair management and firewall control

        :rtype: ``object`` of :class:`.SecurityService`
        :return: a SecurityService object
        """
        raise NotImplementedError(
            'CloudProvider.security not implemented by this provider')

    @property
    def block_store(self):
        """
        Provides access to the volume and snapshot services in this
        provider.

        :rtype: ``object`` of :class:`.BlockStoreService`
        :return: a BlockStoreService object
        """
        raise NotImplementedError(
            'CloudProvider.block_store not implemented by this provider')

    @property
    def object_store(self):
        """
        Provides access to object storage services in this provider.

        :rtype: ``object`` of :class:`.ObjectStoreService`
        :return: an ObjectStoreService object
        """
        raise NotImplementedError(
            'CloudProvider.object_store not implemented by this provider')


class ContainerProvider(object):

    """
    Represents a container instance, such as Docker or LXC
    """

    def create_container(self):
        raise NotImplementedError(
            'create_container not implemented by this provider')

    def delete_container(self):
        raise NotImplementedError(
            'delete_container not implemented by this provider')


class DeploymentProvider(object):

    """
    Represents a deployment provider, such as Ansible or Shell script provider
    """

    def deploy(self, target):
        """
        Deploys on given target, where target is an Instance or Container
        """
        raise NotImplementedError(
            'deploy not implemented by this provider')
