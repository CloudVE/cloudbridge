class CloudProviderFactory():
    """
    """
    def get_providers(self):
        """
        Returns a list of available providers and their interface versions.
        This function could eventually be implemented as a registry file containing all available implementations,
        or alternatively, using automatic discovery.
        """
        return [{ "name": "OPENSTACK", "implementation": [ { "class": "cloudbridge.impl.OpenstackCloudProviderV1", "version": 1 } ] },
                { "name": "EC2", "implementation": [ { "class": "cloudbridge.impl.EC2CloudProviderV1", "version": 1 } ] }
                ]

    def find_provider_impl(self, name, version=None):
        """
        Finds a provider implementation class given its name. If a version is specified, the exact corresponding implementation
        is returned. Otherwise, the latest available implementation is returned.
        """
        for provider in self.get_providers():
            if provider["name"] == name:
                if version:
                    match = [item for item in provider["implementation"] if item["version"] == version]
                    if match:
                        return match["class"]
                    else:
                        return None
                else:
                    # Return latest available version
                    return sorted((for item in provider["implementation"]), key=lambda x: x["version"])[-1]
        return None

    def get_interface_V1(self, name, config):
        """
        Searches all available providers for a CloudProvider interface with the given name, and instantiates
        it based on the given config dictionary, where the config dictionary is a dictionary understood by that
        cloud provider.
        :return:  a concrete provider instance
        :rtype: ``object`` of :class:`.CloudProviderV1`
        """
        provider = self.find_provider(name, version=1)
        if provider is None:
            raise NotImplementedError(
            'A provider by that name implementing interface v1 could not be found')
        else:
            return provider["class"].from_config(config)


class CloudProvider():
    """
    Base interface for a cloud provider
    """
    @staticmethod
    def from_config(config):
        """
        Create a new provider implementation given a dictionary of configuration attributes
        :return:  a concrete provider instance
        :rtype: ``object`` of :class:`.CloudProvider`
        """
        raise NotImplementedError(
            'list_regions not implemented by this provider')


    def Compute(self):
        """
        Provides access to all compute related services in this provider.
        :return:  a ComputeManager object
        :rtype: ``object`` of :class:`.ComputeManager`
        """
        raise NotImplementedError(
            'CloudProvider.Compute not implemented by this provider')

    def Images(self):
        """
        Provides access to all Image related services in this provider.
        (e.g. Glance in Openstack)
        :return:  an ImageManager object
        :rtype: ``object`` of :class:`.ImageManager`
        """
        raise NotImplementedError(
            'CloudProvider.Images not implemented by this provider')

    def Security(self):
        """
        Provides access to keypair management and firewall control
        :return:  a SecurityManager object
        :rtype: ``object`` of :class:`.SecurityManager`
        """
        raise NotImplementedError(
            'CloudProvider.Security not implemented by this provider')

    def BlockStore(self):
        """
        Provides access to the volume/elastic block store services in this provider
        :return:  a BlockStoreManager object
        :rtype: ``object`` of :class:`.BlockStoreManager`
        """
        raise NotImplementedError(
            'CloudProvider.BlockStore not implemented by this provider')

    def ObjectStore(self):
        """
        Provides access to object storage services in this provider
        :return:  an ObjectStoreManager object
        :rtype: ``object`` of :class:`.ObjectStoreManager`
        """
        raise NotImplementedError(
            'CloudProvider.ObjectStore not implemented by this provider')


class ComputeManager():
    """
    Base interface for compute service supported by a provider
    """
    def Provider(self):
        """
        Returns the provider instance associated with this manager
        :return:   a  provider instance
        :rtype: ``object`` of :class:`.CloudProvider`
        """
        raise NotImplementedError(
            'ComputeManager.Provider not implemented by this provider')

    def get_instance(self, id):
        """
        Returns an instance given its id
        :return:  an Instance instance
        :rtype: ``object`` of :class:`.Instance`
        """
        raise NotImplementedError(
            'get_instance not implemented by this provider')

    def find_instance(self, name):
        """
        Searches for an instance by a given list of attributes
        :return:  an Instance instance
        :rtype: ``object`` of :class:`.Instance`
        """
        raise NotImplementedError(
            'find_instance not implemented by this provider')

    def list_instances(self):
        """
        List all instances.
        :return:  list of instance objects
        :rtype: ``list`` of :class:`.Instance`
        """
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def list_instance_types(self):
        """
        List all instance types supported by this provider.
        :return:  list of instance type objects
        :rtype: ``list`` of :class:`.InstanceType`
        """
        raise NotImplementedError(
            'list_instance_types not implemented by this provider')

    def list_regions(self):
        """
        List all data center regions for this provider.
        :return:  list of region objects
        :rtype: ``list`` of :class:`.Region`
        """
        raise NotImplementedError(
            'list_regions not implemented by this provider')

    def create_instance(self):
        """
        Creates a new virtual machine instance.
        :return:  an instance of Instance
        :rtype: `object`` of :class:`.Instance`
        """
        raise NotImplementedError(
            'create_instance not implemented by this provider')


class VolumeManager():
    """
    Base interface for a Volume Manager
    """
    def Provider(self):
        """
        Returns the provider instance associated with this manager
        :return:   a  provider instance
        :rtype: ``object`` of :class:`.CloudProvider`
        """
        raise NotImplementedError(
            'ComputeManager.Provider not implemented by this provider')

    def get_volume(self, id):
        """
        Returns a volume given its id
        :return:  a volume instance
        :rtype: ``object`` of :class:`.Volume`
        """
        raise NotImplementedError(
            'get_volume not implemented by this provider')

    def find_volume(self, name):
        """
        Searches for a volume by a given list of attributes
        :return:  an Instance instance
        :rtype: ``object`` of :class:`.Instance`
        """
        raise NotImplementedError(
            'find_instance not implemented by this provider')

    def list_volumes(self):
        """
        List all volumes.
        :return:  list of instance objects
        :rtype: ``list`` of :class:`.Instance`
        """
        raise NotImplementedError(
            'list_volumes not implemented by this provider')


    def list_volume_snapshots(self):
        """
        List all volume snapshots.
        :return:  list of instance objects
        :rtype: ``list`` of :class:`.Instance`
        """
        raise NotImplementedError(
            'list_volume_snapshots not implemented by this provider')

    def create_volume(self):
        """
        Creates a new volume.
        :return:  list of instance objects
        :rtype: ``list`` of :class:`.Instance`
        """
        raise NotImplementedError(
            'create_volume not implemented by this provider')


class ImageManager():
    """
    Base interface for an Image Manager
    """
    def Provider(self):
        """
        Returns the provider instance associated with this manager
        :return:   a  provider instance
        :rtype: ``object`` of :class:`.CloudProvider`
        """
        raise NotImplementedError(
            'ComputeManager.Provider not implemented by this provider')

    def get_image(self, id):
        """
        Returns an Image given its id
        :return:  an Image instance
        :rtype: ``object`` of :class:`.Image`
        """
        raise NotImplementedError(
            'get_volume get_image implemented by this provider')

    def find_image(self, name):
        """
        Searches for an image by a given list of attributes
        :return:  an Image instance
        :rtype: ``object`` of :class:`.Image`
        """
        raise NotImplementedError(
            'find_image not implemented by this provider')

    def list_images(self):
        """
        List all images.
        :return:  list of image objects
        :rtype: ``list`` of :class:`.Image`
        """
        raise NotImplementedError(
            'list_images not implemented by this provider')

    def create_image(self):
        """
        Create a new image.
        :return:  an Image object
        :rtype: ``object`` of :class:`.Image`
        """
        raise NotImplementedError(
            'create_image not implemented by this provider')

class SecurityManager():
    """
    Base interface for an Image Manager
    """
    def Provider(self):
        """
        Returns the provider instance associated with this manager
        :return:   a  provider instance
        :rtype: ``object`` of :class:`.CloudProvider`
        """
        raise NotImplementedError(
            'ComputeManager.Provider not implemented by this provider')


    def list_key_pairs(self):
        """
        List all key pairs.
        :return:  list of KeyPair objects
        :rtype: ``list`` of :class:`.KeyPair`
        """
        raise NotImplementedError(
            'list_key_pairs not implemented by this provider')

    def create_key_pair(self):
        """
        Create a new keypair.
        :return:  A keypair instance
        :rtype: ``object`` of :class:`.KeyPair`
        """
        raise NotImplementedError(
            'create_key_pair not implemented by this provider')

class Instance():
    def name(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def public_ips(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def private_ips(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def instance_type(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def reboot(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def delete(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

class Volume():
    def attach(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def detach(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def snapshot(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def delete(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')


class Region():
    def name(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def list_zones(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

class ContainerProvider():
    """
    Represents a container instance, such as Docker or LXC
    """
    def create_container(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def delete_container(self):
        raise NotImplementedError(
            'list_instances not implemented by this provider')


class DeploymentProvider():
    """
    Represents a deployment provider, such as Ansible or Shell script provider
    """
    def deploy(self, target):
        """
        Deploys on given target, where target is an Instance or Container
        """
        raise NotImplementedError(
            'list_instances not implemented by this provider')

