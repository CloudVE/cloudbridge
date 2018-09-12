"""
Specifications for data objects exposed through a ``provider`` or ``service``.
"""
from abc import ABCMeta, abstractmethod, abstractproperty
from enum import Enum


class CloudServiceType(object):

    """
    Defines possible service types that are offered by providers.

    Providers can implement the ``has_service`` method and clients can check
    for the availability of a service with::

        if (provider.has_service(CloudServiceTypes.BUCKET))
            ...

    """
    COMPUTE = 'compute'
    IMAGE = 'image'
    SECURITY = 'security'
    VOLUME = 'storage.volumes'
    BUCKET = 'storage.buckets'


class CloudResource(object):

    """
    Base interface for any Resource supported by a provider.

    This interface has a  _provider property that can be used to access the
    provider associated with the resource, which is only intended for use by
    subclasses. Every cloudbridge resource also has an id, a name and a
    label property. The id property is a unique identifier for the resource.
    The name is a more user-friendly version of an id, suitable for
    display to an end-user. However, it cannot be used in place of id. See
    @name documentation. The label property is a user-assignable
    identifier for the resource.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def _provider(self):
        """
        Returns the provider instance associated with this resource.

        Intended for use by subclasses only.

        :rtype: :class:`.CloudProvider`
        :return: a CloudProvider object
        """
        pass

    @abstractproperty
    def id(self):
        """
        Get the resource identifier.

        The id property is used to uniquely identify the resource, and is an
        opaque value which should not be interpreted by cloudbridge clients,
        and is a value meaningful to the underlying cloud provider.

        :rtype: ``str`` :return: ID for this resource as returned by the cloud
        middleware.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get the name id for the resource.

        The name property is typically a user-friendly id value for the
        resource. The name is different from the id property in the
        following ways:
        1. The name property is often a more user-friendly value to
           display to the user than the id property.
        2. The name may sometimes be the same as the id, but should never
           be used in place of the id.
        3. The id is what will uniquely identify a resource, and will be used
           internally by cloudbridge for all get operations etc.
        4. All resources have a name.
        5. The name is read-only.
        6. However, the name may not necessarily be unique, which is the
           reason why it should not be used for uniquely identifying a
           resource.
        Example:
        The AWS machine image name maps to a cloudbridge name. It is not
        editable and is a user friendly name such as 'Ubuntu 14.04' and
        corresponds to the ami-name. It is distinct from the ami-id, which
        maps to cloudbridge's id property. The ami-name cannot be edited, and
        is set at creation time. It is not necessarily unique.
        In Azure, the machine image's name corresponds to cloudbridge's name
        property. In Azure, it also happens to be the same as the id property.

        The name property and the label property share the same character
        restrictions. see :py:attr:`~LabeledCloudResource.label`
        """
        pass

    @abstractmethod
    def to_json(self):
        """
        Returns a JSON representation of the CloudResource object.
        """
        pass


class LabeledCloudResource(CloudResource):

    @abstractproperty
    def label(self):
        """
        Get the resource label.

        The label property is a user-defined, editable identifier for a
        resource. It will often correspond to a user editable resource label
        in the underlying cloud provider, or be simulated through tags/labels.

        The label property adheres to the following restrictions:
        * Must be at least 3 characters in length.
        * Cannot be longer than 63 characters.
        * May only contain ASCII characters comprising of lowercase letters,
          numeric characters, and dashes.
        * Must begin with an alphanumeric character and end with one
          (i.e. cannot begin or end with a dash)

        Some resources may not support labels, in which case, a
        NotImplementedError will be thrown.

        :rtype: ``str``
        :return: Label for this resource as returned by the cloud middleware.
        :throws NotImplementedError if this resource does not support labels
        """
        pass


class Configuration(dict):
    """
    Represents a cloudbridge configuration object
    """

    @abstractproperty
    def default_result_limit(self):
        """
        Get the default maximum number of results to return for a list method.

        The default limit will be applied to most ``list()`` and ``find()``
        methods whenever an explicit limit is not specified.

        :rtype: ``int``
        :return: The maximum number of results to return
        """
        pass

    @property
    def default_wait_timeout(self):
        """
        Get the default wait timeout for ``LifeCycleObjects``.

        The default wait timeout is applied in ``wait_for()`` and
        ``wait_till_ready()`` methods if no explicit timeout is specified.

        :rtype: ``int``
        :return: The maximum length of time (in seconds) to wait for the object
                 to change to desired state.
        """
        pass

    @property
    def default_wait_interval(self):
        """
        Get the default wait interval for ``LifeCycleObjects``.

        The default wait interval is applied in ``wait_for()`` and
        ``wait_till_ready()`` methods if no explicit interval is specified.

        :rtype: ``int``
        :return: How frequently to poll the object's state.
        """
        pass

    @abstractproperty
    def debug_mode(self):
        """
        A flag indicating whether CloudBridge is in debug mode.

        Setting this to ``True`` will cause the underlying provider's debug
        output to be turned on. The flag can be toggled by sending in the
        ``cb_debug`` value via the config dictionary, or setting the
        ``CB_DEBUG`` environment variable.

        :rtype: ``bool``
        :return: Whether debug mode is on.
        """


class ObjectLifeCycleMixin(object):
    """
    A mixin for an object with a defined life-cycle.

    Object examples include an Instance, Volume, Image, or Snapshot. An object
    that supports ObjectLifeCycleMixin will always have a state, defining which
    point in its life cycle it is currently at.

    It also defines a ``wait_till_ready`` operation, which indicates that the
    object is in a state in its life cycle where it is ready to be used by an
    end-user.

    A ``refresh`` operation allows the object to synchronize its state with the
    service provider.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def _provider(self):
        """
        Obtain the provider associated with this object.

        This property is used internally to access the provider config and get
        default timeouts/intervals.

        :rtype: :class:`.CloudProvider` :return: The provider associated with
        this Resource
        """
        pass

    @abstractproperty
    def state(self):
        """
        Get the current state of this object.

        :rtype: ``str``
        :return: The current state as a string.
        """
        pass

    @abstractmethod
    def refresh(self):
        """
        Refresh this object's state and synchronize it with the provider.
        """
        pass

    @abstractmethod
    def wait_for(self, target_states, terminal_states=None, timeout=None,
                 interval=None):
        """
        Wait for for an object to reach a one of desired target states.

        If the object does not reach the desired state within the specified
        timeout, a ``WaitStateException`` will be raised. The optional
        ``terminal_states`` property can be used to specify an additional set
        of states which, should the object reach one, the object thereafter
        will not transition into the desired target state. Should this happen,
        a ``WaitStateException`` will be raised.

        Example:

        .. code-block:: python

            instance.wait_for(
                [InstanceState.DELETED, InstanceState.UNKNOWN],
                terminal_states=[InstanceState.ERROR])

        :type target_states: ``list`` of states
        :param target_states: The list of target states to wait for.

        :type terminal_states: ``list`` of states
        :param terminal_states: A list of terminal states after which the
                                object will not transition into a target state.
                                A WaitStateException will be raised if the
                                object transition into a terminal state.

        :type timeout: ``int``
        :param timeout: The maximum length of time (in seconds) to wait for the
                        object to changed to desired state. If no timeout is
                        specified, the global default_wait_timeout defined in
                        the provider config will apply.

        :type interval: ``int``
        :param interval: How frequently to poll the object's state (in
                         seconds). If no interval is specified, the global
                         default_wait_interval defined in the provider config
                         will apply.

        :rtype: ``True``
        :return: Returns ``True`` if successful. A ``WaitStateException``
                 exception may be thrown by the underlying service if the
                 object cannot  get into a ready state (e.g. if the object
                 is in an error state).
        """
        pass

    @abstractmethod
    def wait_till_ready(self, timeout, interval):
        """
        Wait till the current object reaches its ready state.

        An object's ready state is any state where the end-user can
        successfully interact with the object. Will throw a
        ``WaitStateException`` if the object is not ready within the specified
        timeout.

        :type timeout: ``int``
        :param timeout: The maximum length of time (in seconds) to wait for the
                        object to become ready.

        :type interval: ``int``
        :param interval: How frequently to poll the object's ready state (in
                         seconds).

        :rtype: ``True``
        :return: Returns ``True`` if successful. A ``WaitStateException``
                 exception may be thrown by the underlying service if the
                 object cannot  get into a ready state (e.g. if the object
                 is in an error state).
        """
        pass


class PageableObjectMixin(object):
    """
    A marker interface for objects which support paged iteration.

    The list of objects can be iterated over using the ``list(limit, marker)``
    method.
    """

    @abstractmethod
    def __iter__(self):
        """
        Enables iteration through this object.

        Typically, an implementation will call the ``list(limit, marker)``
        method to transparently page additional objects in as iteration
        progresses.
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        Returns a list of objects up to a maximum limit.

        If a limit and marker are specified, the records will be fetched up to
        the limit starting from the marker onwards. The returned list is a list
        of class ResultList, which has extra properties like is_truncated,
        supports_total and total_records to provide extra information
        about record availability.

        If limit is not specified, the limit will default to the underlying
        provider's default limit. Therefore, you need to check the is_truncated
        property to determine whether more records are available.

        The total number of results can be determined through the total_results
        property. Not all provides will support returning the total_results
        property, so the supports_total property can be used to determine
        whether a total is supported.

        To iterate through all the records, it will be easier to iterate
        directly through the instances using __iter__ instead of calling
        the list method. The __iter__ method will automatically call the list
        method to fetch a batch of records at a time.

        Example:

        .. code-block:: python

            # get first page of results
            instlist = provider.compute.instances.list(limit=50)
            for instance in instlist:
                print("Instance Data: {0}", instance)
            if instlist.supports_total:
                print("Total results: {0}".format(instlist.total_results))
            else:
                print("Total records unknown,"
                      "but has more data?: {0}".format(instlist.is_truncated))

            # Page to next set of results
            if (instlist.is_truncated)
                instlist = provider.compute.instances.list(limit=100,
                                                           marker=instlist.marker)

            # Alternative: iterate through every available record
            for instance in provider.compute.instances:
                print(instance)
        """
        pass


class ResultList(list):
    """
    Provide extra properties to aid with paging through a many results.

    This is a wrapper class around a standard Python :py:class:`list` class.

    Example:

    .. code-block:: python

        # get first page of results
        rl = provider.compute.instances.list(limit=50)
        for result in rl:
            print("Instance Data: {0}", result)
        if rl.supports_total:
            print("Total results: {0}".format(rl.total_results))
        else:
            print("Total records unknown,"
                  "but has more data?: {0}."format(rl.is_truncated))

        # Page to next set of results
        if (rl.is_truncated)
            rl = provider.compute.instances.list(limit=100,
                                                 marker=rl.marker)
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def marker(self):
        """
        An opaque identifier used in paging through very long lists of objects.

        This marker can be provided to the list method to get the next set of
        results.
        """
        pass

    @abstractproperty
    def is_truncated(self):
        """
        Indicate whether this result list has more results that can be paged.
        """
        pass

    @abstractproperty
    def supports_total(self):
        """
        Indicate whether can obtain the total number of available results.

        The ``supports_total`` property should be checked before accessing the
        ``total_results`` property. This is a provider-specific property.
        """
        pass

    @abstractproperty
    def total_results(self):
        """
        Indicate the total number of results for a particular query.

        The ``supports_total`` property should be used to check whether the
        provider supports returning the total number of results, before
        accessing this property, or the behavior is indeterminate.
        """
        pass

    @abstractproperty
    def supports_server_paging(self):
        """
        Indicate whether this ``ResultList`` supports server side paging.

        If server side paging is not supported, the result will useclient side
        paging and the data property provides direct access to all available
        data.
        """
        pass

    @abstractproperty
    def data(self):
        pass


class InstanceState(object):

    """
    Standard states for an instance.

    :cvar UNKNOWN: Instance state unknown.
    :cvar PENDING: Instance is pending
    :cvar CONFIGURING: Instance is being reconfigured in some way.
    :cvar RUNNING: Instance is running.
    :cvar REBOOTING: Instance is rebooting.
    :cvar DELETED: Instance is deleted. No further operations possible.
    :cvar STOPPED: Instance is stopped. Instance can be resumed.
    :cvar ERROR: Instance is in an error state. No further operations possible.

    """
    UNKNOWN = "unknown"
    PENDING = "pending"
    CONFIGURING = "configuring"
    RUNNING = "running"
    REBOOTING = "rebooting"
    DELETED = "deleted"
    STOPPED = "stopped"
    ERROR = "error"


class Instance(ObjectLifeCycleMixin, LabeledCloudResource):

    __metaclass__ = ABCMeta

    @LabeledCloudResource.label.setter
    @abstractmethod
    def label(self, value):
        """
        Set the instance label.
        """
        pass

    @abstractproperty
    def public_ips(self):
        """
        Get all the public IP addresses for this instance.

        :rtype: ``list``
        :return: A list of public IP addresses associated with this instance.
        """
        pass

    @abstractproperty
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.

        :rtype: ``list``
        :return: A list of private IP addresses associated with this instance.
        """
        pass

    @abstractproperty
    def vm_type_id(self):
        """
        Get the VM type id for this instance.

        This will typically be a string value like 'm1.large'. On OpenStack,
        this may be a number or UUID. To get the full :class:``.VMType``
        object, you can use the ``instance.vm_type`` property instead.

        :rtype: ``str``
        :return: VM type id for this instance (e.g., ``m1.large``)
        """
        pass

    @abstractproperty
    def vm_type(self):
        """
        Retrieve full VM type information for this instance.

        :rtype: :class:`.VMType`
        :return: VM type for this instance
        """
        pass

    @abstractmethod
    def reboot(self):
        """
        Reboot this instance (using the cloud middleware API).

        :rtype: ``bool``
        :return: ``True`` if the reboot was successful; ``False`` otherwise.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Permanently delete this instance.
        """
        pass

    @abstractproperty
    def image_id(self):
        """
        Get the image ID for this instance.

        :rtype: ``str``
        :return: Image ID (i.e., AMI) this instance is using.
        """
        pass

    @abstractproperty
    def zone_id(self):
        """
        Get the placement zone ID where this instance is running.

        :rtype: ``str``
        :return: Region/zone/placement where this instance is running.
        """
        pass

    @abstractproperty
    def subnet_id(self):
        """
        Get the subnet ID where this instance is placed.

        :rtype: ``str``
        :return: Subnet ID to which this instance is connected.
        """
        pass

#     @abstractproperty
#     def mac_address(self):
#         """
#         Get the MAC address for this instance.
#
#         :rtype: str
#         :return: MAC address for ths instance.
#         """
#         pass

    @abstractproperty
    def vm_firewalls(self):
        """
        Get the firewalls (security groups) associated with this instance.

        :rtype: list or :class:`.VMFirewall` objects
        :return: A list of VMFirewall objects associated with this instance.
        """
        pass

    @abstractproperty
    def vm_firewall_ids(self):
        """
        Get the IDs of the VM firewalls associated with this instance.

        :rtype: list or :class:``str``
        :return: A list of the VMFirewall IDs associated with this instance.
        """
        pass

    @abstractproperty
    def key_pair_id(self):
        """
        Get the id of the key pair associated with this instance.

        :rtype: ``str``
        :return: Id of the ssh key pair associated with this instance.
        """
        pass

    @abstractmethod
    def create_image(self, label):
        """
        Create a new image based on this instance.

        :rtype: :class:``.Image``
        :return:  an Image object
        """
        pass

    @abstractmethod
    def add_floating_ip(self, floating_ip):
        """
        Add a public IP address to this instance.

        :type floating_ip: :class:``.FloatingIP`` or floating IP ID
        :param floating_ip: The FloatingIP object to associate with the
                            instance. Note that is not the actual public IP
                            address but the CloudBridge object encapsulating
                            the IP or the respective provider ID that
                            identifies the address.
        """
        pass

    @abstractmethod
    def remove_floating_ip(self, floating_ip):
        """
        Remove a public IP address from this instance.

        :type floating_ip: :class:``.FloatingIP`` or floating IP ID
        :param floating_ip: The FloatingIP object to remove from the
                            instance. Note that is not the actual public IP
                            address but the CloudBridge object encapsulating
                            the IP or the respective provider ID that
                            identifies the address.
        """
        pass

    @abstractmethod
    def add_vm_firewall(self, firewall):
        """
        Add a VM firewall to this instance

        :type firewall: :class:``.VMFirewall``
        :param firewall: The VMFirewall to associate with the instance.
        """
        pass

    @abstractmethod
    def remove_vm_firewall(self, firewall):
        """
        Remove a VM firewall from this instance

        :type firewall: ``VMFirewall``
        :param firewall: The VMFirewall to associate with the instance.
        """
        pass


class MachineImageState(object):

    """
    Standard states for a machine image

    :cvar UNKNOWN: Image state unknown.
    :cvar PENDING: Image is pending
    :cvar AVAILABLE: Image is available
    :cvar ERROR: Image is in an error state. Not recoverable.

    """
    UNKNOWN = "unknown"
    PENDING = "pending"
    AVAILABLE = "available"
    ERROR = "error"


class LaunchConfig(object):
    """
    Represents an advanced launch configuration object.

    This object can contain information such as ``BlockDeviceMappings``
    configurations and other advanced options, which may be useful when
    launching an instance.

    Example:

    .. code-block:: python

        lc = provider.compute.instances.create_launch_config()
        lc.add_block_device(...)

        inst = provider.compute.instances.create(
            'MyVM', image, vm_type, subnet, launch_config=lc)
    """

    @abstractmethod
    def add_ephemeral_device(self):
        """
        Add a new ephemeral block device mapping to the boot configuration.

        This can be used to add existing ephemeral devices to the instance
        (the total number of ephemeral devices available for a particular
        ``VMType`` can be determined by querying the ``VMType`` service).
        Note that on some providers, such as AWS, ephemeral devices must be
        added in as a device mapping at instance creation time and cannot be
        added afterwards.

        Note that the device name, such as */dev/sda1*, cannot be selected at
        present, since this tends to be provider and VM type specific.
        However, the order of device addition coupled with device type will
        generally determine naming order, with devices added first getting
        lower letters than instances added later.

        Example:

        .. code-block:: python

            lc = provider.compute.instances.create_launch_config()

            # 1. Add all available ephemeral devices
            vm_type = provider.compute.vm_types.find(name='m1.tiny')[0]
            for i in range(vm_type.num_ephemeral_disks):
                lc.add_ephemeral_device()
        """
        pass

    @abstractmethod
    def add_volume_device(self, source=None, is_root=None, size=None,
                          delete_on_terminate=None):
        """
        Add a new volume based block device mapping to the boot configuration.

        The volume can be based on a snapshot, image, existing volume or
        be a blank new volume, and is specified by the source parameter.

        The property ``is_root`` can be set to ``True`` to override any
        existing root device mappings. Otherwise, the default behavior is to
        add new block devices to the instance.

        Note that the device name, such as */dev/sda1*, cannot be selected at
        present since this tends to be provider and VM type specific. However,
        the order of device addition coupled with device type will generally
        determine naming order, with devices added first getting lower letters
        than instances added later (except when ``is_root`` is set).

        Example:

        .. code-block:: python

            lc = provider.compute.instances.create_launch_config()

            # 1. Create and attach an empty volume of size 100GB
            lc.add_volume_device(size=100, delete_on_terminate=True)

            # 2. Create and attach a volume based on a snapshot
            snap = provider.storage.snapshots.get('<my_snapshot_id>')
            lc.add_volume_device(source=snap)

            # 3. Create+attach a volume based on an image and set it as root
            img = provider.compute.images.get('<my_image_id>')
            lc.add_volume_device(source=img, size=100, is_root=True)

        :type  source: ``Volume``, ``Snapshot``, ``Image`` or None.
        :param source: The source ``block_device`` to add. If ``Volume``, the
                       volume will be attached directly to the instance.
                       If ``Snapshot``, a volume will be created based on the
                       Snapshot and attached to the instance. If ``Image``,
                       a volume based on the Image will be attached to the
                       instance. If ``None``, the source is assumed to be
                       a blank volume.

        :type  is_root: ``bool``
        :param is_root: Determines which device will serve as the root device.
                        If more than one device is defined as root, an
                        ``InvalidConfigurationException`` will be thrown.

        :type  size: ``int``
        :param size: The size of the volume to create. An implementation may
                     ignore this parameter for certain sources like 'Volume'.

        :type  delete_on_terminate: ``bool``
        :param delete_on_terminate: Determines whether to delete or keep the
                                    volume on instance termination.
        """
        pass


class MachineImage(ObjectLifeCycleMixin, LabeledCloudResource):

    __metaclass__ = ABCMeta

    @abstractproperty
    def description(self):
        """
        Get the image description.

        :rtype: ``str``
        :return: Description for this image as returned by the cloud
                 middleware.
        """
        pass

    @abstractproperty
    def min_disk(self):
        """
        Return the minimum size of the disk that's required to boot this image.

        Value returned is in gigabytes.

        :rtype: ``int``
        :return: The minimum disk size needed by this image.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this image.

        :rtype: ``bool``
        :return: ``True`` if the operation succeeded.
        """
        pass


class NetworkState(object):

    """
    Standard states for a network.

    :cvar UNKNOWN: Network state unknown.
    :cvar PENDING: Network is being created.
    :cvar AVAILABLE: Network is available.
    :cvar DOWN: Network is not operational.
    :cvar ERROR: Network is in error state.
    """
    UNKNOWN = "unknown"
    PENDING = "pending"
    AVAILABLE = "available"
    DOWN = "down"
    ERROR = "error"


class Network(ObjectLifeCycleMixin, LabeledCloudResource):
    """
    Represents a software-defined network, like the Virtual Private Cloud.
    """
    __metaclass__ = ABCMeta

    @LabeledCloudResource.label.setter
    @abstractmethod
    def label(self, value):
        """
        Set the resource label.
        """
        pass

    @abstractproperty
    def external(self):
        """
        A flag to indicate if this network is capable of Internet-connectivity.

        :rtype: ``bool``
        :return: ``True`` if the network can be connected to the Internet.
        """
        pass

    @abstractproperty
    def state(self):
        """
        The state of the network.

        :rtype: ``str``
        :return: One of ``unknown``, ``pending``, ``available``, ``down`` or
                 ``error``.
        """
        pass

    @abstractproperty
    def cidr_block(self):
        """
        A CIDR block for this network.

        .. note:: OpenStack does not define a CIDR block for networks.

        :rtype: ``str``
        :return: A CIDR block string.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this network.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractproperty
    def subnets(self):
        """
        The associated subnets.

        :rtype: ``list`` of :class:`.Subnet`
        :return: List of subnets associated with this network.
        """
        pass

    @abstractmethod
    def create_subnet(self, label, cidr_block, zone=None):
        """
        Create a new network subnet and associate it with this Network.

        :type label: ``str``
        :param label: The subnet label. The subnet name will be derived from
                      this label.

        :type cidr_block: ``str``
        :param cidr_block: CIDR block within this Network to assign to the
                           subnet.

        :type zone: ``str``
        :param zone: Placement zone where to create the subnet. Some providers
                     may not support subnet zones, in which case the value is
                     ignored.

        :rtype: ``object`` of :class:`.Subnet`
        :return:  A Subnet object
        """
        pass

    @abstractproperty
    def gateways(self):
        """
        Provides access to the internet gateways attached to this network.

        :rtype: :class:`.GatewayContainer`
        :return: A GatewayContainer object
        """
        pass


class SubnetState(object):
    """
    Standard states for a subnet.

    :cvar UNKNOWN: Subnet state unknown.
    :cvar PENDING: Subnet is being created.
    :cvar AVAILABLE: Subnet is available.
    :cvar DOWN: Subnet is not operational.
    :cvar ERROR: Subnet is in error state.
    """
    UNKNOWN = "unknown"
    PENDING = "pending"
    AVAILABLE = "available"
    DOWN = "down"
    ERROR = "error"


class Subnet(ObjectLifeCycleMixin, LabeledCloudResource):
    """
    Represents a subnet, as part of a Network.
    """
    __metaclass__ = ABCMeta

    @LabeledCloudResource.label.setter
    @abstractmethod
    def label(self, value):
        """
        Set the resource label.
        """
        pass

    @abstractproperty
    def cidr_block(self):
        """
        A CIDR block for this subnet.

        :rtype: ``str``
        :return: A CIDR block string.
        """
        pass

    @abstractproperty
    def network_id(self):
        """
        ID of the network associated with this this subnet.

        :rtype: ``str``
        :return: Network ID.
        """
        pass

    @abstractproperty
    def network(self):
        """
        The parent network object associated with this this subnet.

        :rtype: ``Network``
        :return: `Network` object
        """
        pass

    @abstractproperty
    def zone(self):
        """
        Placement zone of the subnet.

        If the provider does not support subnet placement, return ``None``.

        :rtype: :class:`.PlacementZone` object
        :return: Placement zone of the subnet, or ``None`` if not defined.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this subnet.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass


class FloatingIPContainer(PageableObjectMixin):
    """
    Base interface for a FloatingIP Service.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, fip_id):
        """
        Returns a FloatingIP given its ID or ``None`` if not found.

        :type fip_id: ``str``
        :param fip_id: The ID of the FloatingIP to retrieve.

        :rtype: ``object`` of :class:`.FloatingIP`
        :return: a FloatingIP object
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List floating (i.e., static) IP addresses.

        :rtype: ``list`` of :class:`.FloatingIP`
        :return: list of FloatingIP objects
        """
        pass

    @abstractmethod
    def find(self, **kwargs):
        """
        Searches for a FloatingIP by a given list of attributes.

        Supported attributes: label, public_ip

        Example:

        .. code-block:: python

            fip = provider.networking.gateways.get('id').floating_ips.find(
                        public_ip='public_ip')


        :rtype: List of ``object`` of :class:`.FloatingIP`
        :return: A list of FloatingIP objects matching the supplied attributes.
        """
        pass

    @abstractmethod
    def create(self):
        """
        Allocate a new floating (i.e., static) IP address.

        :rtype: ``object`` of :class:`.FloatingIP`
        :return:  A FloatingIP object
        """
        pass

    @abstractmethod
    def delete(self, fip_id):
        """
        Delete an existing FloatingIP.

        :type fip_id: ``str``
        :param fip_id: The ID of the FloatingIP to be deleted.
        """
        pass


class FloatingIpState(object):

    """
    Standard states for a floating ip.

    :cvar UNKNOWN: Floating IP state unknown.
    :cvar AVAILABLE: Floating IP is available.
    :cvar IN_USE: Floating IP is attached to a device.
    :cvar ERROR: Floating IP is in an error state.
    """
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    IN_USE = "in_use"
    ERROR = "error"


class FloatingIP(ObjectLifeCycleMixin, CloudResource):
    """
    Represents a floating (i.e., static) IP address.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def public_ip(self):
        """
        Public IP address.

        :rtype: ``str``
        :return: IP address.
        """
        pass

    @abstractproperty
    def private_ip(self):
        """
        Private IP address this address is attached to.

        :rtype: ``str``
        :return: IP address or ``None``.
        """
        pass

    @abstractproperty
    def in_use(self):
        """
        Whether the address is in use or not.

        :rtype: ``bool``
        :return: ``True`` if the address is attached to an instance.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this address.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass


class RouterState(object):
    """
    Standard states for a router.

    :cvar UNKNOWN: Router state unknown.
    :cvar ATTACHED: Router is attached to a network and should be operational.
    :cvar DETACHED: Router is detached from a network.

    """
    UNKNOWN = "unknown"
    ATTACHED = "attached"
    DETACHED = "detached"


class Router(LabeledCloudResource):
    """
    Represents a private network router.

    This logical router is meant to roughly mimic the properties of a physical
    router. Therefore, attaching a subnet can be thought of as plugging in a
    network cable to enable routing to/from that subnet. Attaching a gateway
    can be thought of as plugging in an upstream link.
    """
    __metaclass__ = ABCMeta

    @LabeledCloudResource.label.setter
    @abstractmethod
    def label(self, value):
        """
        Set the resource label.
        """
        pass

    @abstractproperty
    def state(self):
        """
        Router state: attached or detached to a network.

        :rtype: ``str``
        :return: ``attached`` or ``detached``.
        """
        pass

    @abstractproperty
    def network_id(self):
        """
        ID of the network to which the router is attached.

        :rtype: ``str``
        :return: ID for the attached network or ``None``.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this router.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def attach_subnet(self, subnet):
        """
        Attach this router to a subnet.

        :type subnet: ``Subnet`` or ``str``
        :param subnet: The subnet to which to attach this router.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def detach_subnet(self, subnet):
        """
        Detach this subnet from a network.

        :type subnet: ``Subnet`` or ``str``
        :param subnet: The subnet to detach from this router.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractproperty
    def subnets(self):
        """
        List of subnets attached to this router.

        :rtype: ``list`` of :class:`.Subnet` objects
        :return: A list of subnets associated with this router.
        """
        pass

    @abstractmethod
    def attach_gateway(self, gateway):
        """
        Attach a gateway to this router.

        :type gateway: ``Gateway``
        :param gateway: The Gateway to attach to this router.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def detach_gateway(self, gateway):
        """
        Detach this router from a gateway.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass


class GatewayState(object):
    """
    Standard states for a gateway.

    :cvar UNKNOWN: Gateway state unknown.
    :cvar CONFIGURING: Gateway is being configured
    :cvar AVAILABLE: Gateway is ready
    :cvar ERROR: Gateway is ready

    """
    UNKNOWN = "unknown"
    CONFIGURING = "configuring"
    AVAILABLE = "available"
    ERROR = "error"


class GatewayContainer(PageableObjectMixin):
    """
    Manage internet gateway resources.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_or_create_inet_gateway(self):
        """
        Creates new or returns an existing internet gateway for a network.

        The returned gateway object can subsequently be attached to a router to
        provide internet routing to a network.

        :type  name: ``str``
        :param name: The gateway label.

        :rtype: ``object``  of :class:`.InternetGateway` or ``None``
        :return: an InternetGateway object of ``None`` if not found.
        """
        pass

    @abstractmethod
    def delete(self, gateway):
        """
        Delete a gateway.

        :type gateway: :class:`.Gateway` object
        :param gateway: Gateway object to delete.
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all available internet gateways.

        :rtype: ``list`` of :class:`.InternetGateway` or ``None``
        :return: Current list of internet gateways.
        """
        pass


class Gateway(CloudResource):
    """
    Represents a gateway resource.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def network_id(self):
        """
        ID of the network to which the gateway is attached.

        :rtype: ``str``
        :return: ID for the attached network or ``None``.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this gateway. On some providers, if the gateway
        is public/a singleton, this operation will do nothing.
        """
        pass

    @abstractproperty
    def floating_ips(self):
        """
        Provides access to floating IPs connected to this internet gateway.

        :rtype: :class:`.FloatingIPContainer`
        :return: A FloatingIPContainer object
        """
        pass


class InternetGateway(ObjectLifeCycleMixin, Gateway):
    """
    Represents an Internet gateway resource.
    """
    __metaclass__ = ABCMeta


class AttachmentInfo(object):
    """
    Contains attachment information for a volume.
    """

    @abstractproperty
    def volume(self):
        """
        Get the volume instance related to this attachment.

        :rtype: ``Volume``
        :return: Volume object that this attachment info belongs to
        """
        pass

    @abstractproperty
    def instance_id(self):
        """
        Get the instance_id related to this attachment.

        :rtype: ``str``
        :return: Instance id that this attachment info belongs to
        """
        pass

    @abstractproperty
    def device(self):
        """
        Get the device the volume is mapped as.

        :rtype: ``str``
        :return: Device that the volume is mapped as
        """
        pass


class VolumeState(object):
    """
    Standard states for a volume

    :cvar UNKNOWN: Volume state unknown.
    :cvar CREATING: Volume is being created.
    :cvar CONFIGURING: Volume is being configured in some way.
    :cvar AVAILABLE: Volume is available and can be attached to an instance.
    :cvar IN_USE: Volume is attached and in-use.
    :cvar DELETED: Volume has been deleted. No further operations possible.
    :cvar ERROR: Volume is in an error state. No further operations possible.

    """
    UNKNOWN = "unknown"
    CREATING = "creating"
    CONFIGURING = "configuring"
    AVAILABLE = "available"
    IN_USE = "in-use"
    DELETED = "deleted"
    ERROR = "error"


class Volume(ObjectLifeCycleMixin, LabeledCloudResource):
    """
    Represents a block storage device (aka volume).
    """

    __metaclass__ = ABCMeta

    @LabeledCloudResource.label.setter
    @abstractmethod
    def label(self, value):
        """
        Set the volume label.
        """
        pass

    @abstractproperty
    def description(self):
        """
        Get the volume description.

        Some cloud providers may not support this property, and will return the
        volume label instead.

        :rtype: ``str``
        :return: Description for this volume as returned by the cloud
                 middleware.
        """
        pass

    @description.setter
    @abstractmethod
    def description(self, value):
        """
        Set the volume description.

        Some cloud providers may not support this property, and setting the
        description may have no effect (providers that do not support this
        property will always return the volume label as the description).
        """
        pass

    @abstractproperty
    def size(self):
        """
        Get the volume size (in GB).

        :rtype: ``int``
        :return: Size for this volume as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def create_time(self):
        """
        Get the creation data and time for this volume.

        :rtype: ``DateTime``
        :return: Creation time for this volume as returned by the cloud
                 middleware.
        """
        pass

    @abstractproperty
    def zone_id(self):
        """
        Get the placement zone id that this volume belongs to.

        :rtype: ``str``
        :return: PlacementZone for this volume as returned by the cloud
                 middleware.
        """
        pass

    @abstractproperty
    def source(self):
        """
        If available, get the source that this volume is based on.

        This can be a ``Snapshot``, an ``Image``, or ``None`` if no source.

        :rtype: ``Snapshot``, ``Image``, or ``None``
        :return: Snapshot or Image source for this volume as returned by the
                 cloud middleware.
        """
        pass

    @abstractproperty
    def attachments(self):
        """
        Get attachment information for this volume.

        :rtype: ``AttachmentInfo``
        :return: Returns an AttachmentInfo object.
        """
        pass

    @abstractmethod
    def attach(self, instance, device):
        """
        Attach this volume to an instance.

        :type instance: ``str`` or :class:`.Instance` object
        :param instance: The ID of an instance or an ``Instance`` object to
                         which this volume will be attached.

        :type device: ``str``
        :param device: The device on the instance through which the
                       volume will be exposed (e.g. /dev/sdh).

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def detach(self, force=False):
        """
        Detach this volume from an instance.

        :type force: ``bool``
        :param force: Forces detachment if the previous detachment attempt
                      did not occur cleanly. This option is supported on select
                      clouds only. This option can lead to data loss or a
                      corrupted file system. Use this option only as a last
                      resort to detach a volume from a failed instance. The
                      instance will not have an opportunity to flush file
                      system caches nor file system meta data. If you
                      use this option, you must perform file system check and
                      repair procedures.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def create_snapshot(self, label, description=None):
        """
        Create a snapshot of this Volume.

        :type label: ``str``
        :param label: The label for this snapshot.

        :type description: ``str``
        :param description: A description of the snapshot.
                            Limited to 256 characters.

        :rtype: :class:`.Snapshot`
        :return: The created Snapshot object.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this volume.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass


class SnapshotState(object):
    """
    Standard states for a snapshot

    :cvar UNKNOWN: Snapshot state unknown.
    :cvar PENDING: Snapshot is pending.
    :cvar CONFIGURING: Snapshot is being configured in some way.
    :cvar AVAILABLE: Snapshot has been completed and is ready for use.
    :cvar ERROR: Snapshot is in an error state. No further operations possible.

    """
    UNKNOWN = "unknown"
    PENDING = "pending"
    CONFIGURING = "configuring"
    AVAILABLE = "available"
    ERROR = "error"


class Snapshot(ObjectLifeCycleMixin, LabeledCloudResource):
    """
    Represents a snapshot of a block storage device.
    """

    __metaclass__ = ABCMeta

    @LabeledCloudResource.label.setter
    @abstractmethod
    def label(self, value):
        """
        Set the snapshot label.
        """
        pass

    @abstractproperty
    def description(self):
        """
        Get the snapshot description.

        Some cloud providers may not support this property, and will return the
        snapshot label instead.

        :rtype: ``str``
        :return: Description for this snapshot as returned by the cloud
                 middleware.
        """
        pass

    @description.setter
    @abstractmethod
    def description(self, value):
        """
        Set the snapshot description.

        Some cloud providers may not support this property, and setting the
        description may have no effect (providers that do not support this
        property will always return the snapshot label as the description).

        :type value: ``str``
        :param value: The value for the snapshot description.
        """
        pass

    @abstractproperty
    def size(self):
        """
        Get the snapshot size (in GB).

        :rtype: ``int``
        :return: Size for this snapshot as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def volume_id(self):
        """
        Get the id of the volume that this snapshot is based on.

        This method may return ``None`` if the source volume no longer exists.

        :rtype: ``int``
        :return: Id of the volume that this snapshot is based on
        """
        pass

    @abstractproperty
    def create_time(self):
        """
        Get the creation data and time for this snapshot.

        :rtype: ``DateTime``
        :return: Creation time for this snapshot as returned by the cloud
                 middleware.
        """
        pass

    @abstractmethod
    def create_volume(self, placement, size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.

        :type placement: ``str``
        :param placement: The availability zone where to create the Volume.

        :type size: ``int``
        :param size: The size of the new volume, in GiB (optional). Defaults to
                     the size of the snapshot.

        :type volume_type: ``str``
        :param volume_type: The type of the volume (optional). Availability and
                            valid values depend on the provider.

        :type iops: ``int``
        :param iops: The provisioned IOPs you want to associate with
                     this volume (optional). Availability depends on the
                     provider.

        :rtype: :class:`.Volume`
        :return: An instance of the created Volume.
        """
        pass

#     @abstractmethod
#     def share(self, user_ids=None):
#         """
#         Share this Snapshot.
#
#         :type user_ids: list of strings
#         :param user_ids: A list of cloud provider compatible user IDs. If no
#                          IDs are specified, the snapshot is made public.
#
#         :rtype: bool
#         :return: ``True`` if successful.
#         """
#         pass
#
#     @abstractmethod
#     def unshare(self, user_ids=None):
#         """
#         Unshare this Snapshot.
#
#         :type user_ids: list of strings
#         :param user_ids: A list of cloud provider compatible user IDs. If no
#                          IDs are specified, the snapshot is made private.
#
#         :rtype: bool
#         :return: ``True`` if successful.
#         """
#         pass

    @abstractmethod
    def delete(self):
        """
        Delete this snapshot.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass


class KeyPair(CloudResource):
    """
    Represents an ssh key pair.
    """

    __metaclass__ = ABCMeta

    @abstractproperty
    def material(self):
        """
        Unencrypted private key.

        :rtype: ``str``
        :return: Unencrypted private key or ``None`` if not available.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this key pair.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass


class Region(CloudResource):
    """
    Represents a cloud region.

    A cloud region is typically a separate geographic area and will contain at
    least one placement zone.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def zones(self):
        """
        Access information about placement zones within this region.

        :rtype: Iterable
        :return: Iterable of available placement zones in this region.
        """
        pass


class PlacementZone(CloudResource):
    """
    Represents a placement zone.

    A placement zone is contained within a Region.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def region_name(self):
        """
        A region this placement zone is associated with.

        :rtype: ``str``
        :return: The id of the region the zone is associated with.
        """
        pass


class VMType(CloudResource):
    """
    A VM type object.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def family(self):
        """
        The family/group that this VM type belongs to.

        For example, General Purpose Instances or High-Memory Instances. If
        the provider does not support such a grouping, it may return ``None``.

        :rtype: ``str``
        :return: Name of the instance family or ``None``.
        """
        pass

    @abstractproperty
    def vcpus(self):
        """
        The number of VCPUs supported by this VM type.

        :rtype: ``int``
        :return: Number of VCPUs.
        """
        pass

    @abstractproperty
    def ram(self):
        """
        The amount of RAM (in GB) supported by this VM type.

        :rtype: ``float``
        :return: Total RAM (in GB).
        """
        pass

    @abstractproperty
    def size_root_disk(self):
        """
        The size of this VM types's root disk (in GB).

        :rtype: ``int``
        :return: Size of root disk (in GB).
        """
        pass

    @abstractproperty
    def size_ephemeral_disks(self):
        """
        The size of this VM types's total ephemeral storage (in GB).

        :rtype: ``int``
        :return: Size of ephemeral disks (in GB).
        """
        pass

    @abstractproperty
    def num_ephemeral_disks(self):
        """
        The total number of ephemeral disks on this VM type.

        :rtype: ``int``
        :return: Number of ephemeral disks available.
        """
        pass

    @abstractproperty
    def size_total_disk(self):
        """
        The total disk space available on this VM type
        (root_disk + ephemeral).

        :rtype: ``int``
        :return: Size of total disk space (in GB).
        """
        pass

    @abstractproperty
    def extra_data(self):
        """
        A dictionary of extra data about this instance. May contain
        nested dictionaries, but all key value pairs are strings or integers.

        :rtype: ``dict``
        :return: Extra attributes for this VM type.
        """
        pass


class VMFirewall(LabeledCloudResource):
    """
    Represents a firewall resource applied to virtual machines.

    This is in contrast to a firewall for a network, for example.
    """

    __metaclass__ = ABCMeta

    @LabeledCloudResource.label.setter
    @abstractmethod
    def label(self, value):
        """
        Set the resource label.
        """
        pass

    @abstractproperty
    def description(self):
        """
        Return the description of this VM firewall.

        :rtype: ``str``
        :return: A description of this VM firewall.
        """
        pass

    @abstractproperty
    def network_id(self):
        """
        Network ID with which this VM firewall is associated.

        :rtype: ``str``
        :return: Provider-supplied network ID or ``None`` is not available.
        """
        pass

    @abstractproperty
    def rules(self):
        """
        Get a container for the rules belonging to this VM firewall.

        This object can be used for further operations on rules, such as get,
        list, create, etc.

        :rtype: An object of :class:`.VMFirewallRuleContainer`
        :return: A VMFirewallRuleContainer for further operations
        """
        pass


class VMFirewallRuleContainer(PageableObjectMixin):
    """
    Base interface for Firewall rules.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, rule_id):
        """
        Return a firewall rule given its ID.

        Returns ``None`` if the rule does not exist.

        Example:

        .. code-block:: python

            fw = provider.security.vm_firewalls.get('my_fw_id')
            rule = fw.rules.get('rule_id')
            print(rule.id, rule.label)

        :rtype: :class:`.FirewallRule`
        :return:  a FirewallRule instance
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all firewall rules associated with this firewall.

        :rtype: ``list`` of :class:`.FirewallRule`
        :return:  list of Firewall rule objects
        """
        pass

    @abstractmethod
    def create(self,  direction, protocol=None, from_port=None,
               to_port=None, cidr=None, src_dest_fw=None):
        """
        Create a VM firewall rule.

        If a matching rule already exists, return it.

        Example:

        .. code-block:: python
            from cloudbridge.cloud.interfaces.resources import TrafficDirection

            fw = provider.security.vm_firewalls.get('my_fw_id')
            fw.rules.create(TrafficDirection.INBOUND, protocol='tcp',
                            from_port=80, to_port=80, cidr='10.0.0.0/16')
            fw.rules.create(TrafficDirection.INBOUND, src_dest_fw=fw)
            fw.rules.create(TrafficDirection.OUTBOUND, src_dest_fw=fw)

        You need to pass in either ``src_dest_fw`` OR ``protocol`` AND
        ``from_port``, ``to_port``, ``cidr``. In other words, either
        you are authorizing another group or you are authorizing some
        IP-based rule.

        :type direction: :class:``.TrafficDirection``
        :param direction: Either ``TrafficDirection.INBOUND`` |
                          ``TrafficDirection.OUTBOUND``

        :type protocol: ``str``
        :param protocol: Either ``tcp`` | ``udp`` | ``icmp``.

        :type from_port: ``int``
        :param from_port: The beginning port number you are enabling.

        :type to_port: ``int``
        :param to_port: The ending port number you are enabling.

        :type cidr: ``str`` or list of ``str``
        :param cidr: The CIDR block you are providing access to.

        :type src_dest_fw: :class:`.VMFirewall`
        :param src_dest_fw: The VM firewall object which is the
                            source/destination of the traffic, depending on
                            whether it's ingress/egress traffic.

        :rtype: :class:`.VMFirewallRule`
        :return: Rule object if successful or ``None``.
        """
        pass

    @abstractmethod
    def find(self, **kwargs):
        """
        Find a firewall rule filtered by the given parameters.

        :type label: str
        :param label: The label of the VM firewall to retrieve.

        :type protocol: ``str``
        :param protocol: Either ``tcp`` | ``udp`` | ``icmp``.

        :type from_port: ``int``
        :param from_port: The beginning port number you are enabling.

        :type to_port: ``int``
        :param to_port: The ending port number you are enabling.

        :type cidr: ``str`` or list of ``str``
        :param cidr: The CIDR block you are providing access to.

        :type src_dest_fw: :class:`.VMFirewall`
        :param src_dest_fw: The VM firewall object which is the
                            source/destination of the traffic, depending on
                            whether it's ingress/egress traffic.

        :type src_dest_fw_id: :class:`.str`
        :param src_dest_fw_id: The VM firewall id which is the
                               source/destination of the traffic, depending on
                               whether it's ingress/egress traffic.

        :rtype: list of :class:`VMFirewallRule`
        :return: A list of VMFirewall objects or an empty list if none
                 found.
        """
        pass

    @abstractmethod
    def delete(self, rule_id):
        """
        Delete an existing VMFirewall rule.

        :type rule_id: str
        :param rule_id: The VM firewall rule to be deleted.
        """
        pass


class TrafficDirection(Enum):
    """
    Direction of data flow in a firewall.
    """
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'


class VMFirewallRule(CloudResource):
    """
    Represents a VM firewall rule.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def direction(self):
        """
        Direction of traffic to which this rule applies.

        Either ``TrafficDirection.INBOUND`` or ``TrafficDirection.OUTBOUND``.

        :rtype: ``str``
        :return: Direction of traffic to which this rule applies.
        """
        pass

    @abstractproperty
    def protocol(self):
        """
        IP protocol used. Either ``tcp`` | ``udp`` | ``icmp``.

        :rtype: ``str``
        :return: Active protocol.
        """
        pass

    @abstractproperty
    def from_port(self):
        """
        Lowest port number opened as part of this rule.

        :rtype: ``int``
        :return: Lowest port number or 0 if not set.
        """
        pass

    @abstractproperty
    def to_port(self):
        """
        Highest port number opened as part of this rule.

        :rtype: ``int``
        :return: Highest port number or 0 if not set.
        """
        pass

    @abstractproperty
    def cidr(self):
        """
        CIDR block this VM firewall is providing access to.

        :rtype: ``str``
        :return: CIDR block.
        """
        pass

    @abstractproperty
    def src_dest_fw_id(self):
        """
        VM firewall id given access permissions by this rule.

        :rtype: ``str``
        :return: The VM firewall granted access.
        """
        pass

    @abstractproperty
    def src_dest_fw(self):
        """
        VM firewall given access permissions by this rule.

        :rtype: :class:``.VMFirewall``
        :return: The VM firewall granted access.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this rule.
        """
        pass


class BucketObject(CloudResource):
    """
    Represents an object stored within a bucket.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        """
        Retrieve the name of the current object.

        The bucket object name adheres to a naming requirement that is more
        relaxed than the naming requirement enforced across CloudBridge. More
        details are available here: http://docs.aws.amazon.com/AmazonS3/latest/
        dev/UsingMetadata.html#object-key-guidelines

        :rtype: ``str``
        :return: Name for this object as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def size(self):
        """
        Get this object's size.

        :rtype: ``int``
        :return: Size of this object in bytes.
        """
        pass

    @abstractproperty
    def last_modified(self):
        """
        Get the date and time this object was last modified.

        :rtype: ``str``
        :return: Date and time formatted string %Y-%m-%dT%H:%M:%S.%f
        """
        pass

    @abstractmethod
    def iter_content(self):
        """
        Returns this object's content as an iterable.

        :rtype: Iterable
        :return: An iterable of the file contents

        """
        pass

    @abstractmethod
    def save_content(self, target_stream):
        """
        Save this object and write its contents to the ``target_stream``.
        """
        pass

    @abstractmethod
    def upload(self, source_stream):
        """
        Set the contents of the object to the data read from the source stream.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def upload_from_file(self, path):
        """
        Store the contents of the file pointed by the "path" variable.

        :type path: ``str``
        :param path: Absolute path to the file to be uploaded to S3.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this object.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def generate_url(self, expires_in):
        """
        Generate a URL to this object.

        If the object is public, `expires_in` argument is not necessary, but if
        the object is private, the lifetime of URL is set using `expires_in`
        argument.

        :type expires_in: ``int``
        :param expires_in: Time to live of the generated URL in seconds.

        :rtype: ``str``
        :return: A URL to access the object.
        """
        pass

    @abstractmethod
    def refresh(self):
        """
        Refresh this object's state and synchronize it with the underlying
        service provider.
        """
        pass


class Bucket(CloudResource):
    """
    Represents a namespace for objects (eg, object store bucket or container).
    """

    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        """
        Retrieve the name of the current bucket.

        :rtype: ``str``
        :return: Name for this instance as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def objects(self):
        """
        Get a container for the objects belonging to this Bucket.

        This object can be used to iterate through bucket objects, as well as
        perform further operations on buckets, such as ``get``, ``list``,
        ``create``, etc.

        .. code-block:: python

            # Show all objects in bucket
            print(list(bucket.objects))

            # Find an object by name
            print(bucket.objects.find(name='my_obj.txt'))

            # Get first page of bucket list
            print(bucket.objects.list())

            # Create a new object within this bucket
            obj = bucket.objects.create('my_obj.txt')

        :rtype: :class:`.BucketContainer`
        :return: A BucketContainer for further operations.
        """
        pass

    @abstractmethod
    def delete(self, delete_contents=False):
        """
        Delete this bucket.

        :type delete_contents: ``bool``
        :param delete_contents: If ``True``, all objects within the bucket
                                will be deleted.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass


class BucketContainer(PageableObjectMixin):
    """
    A container service for objects within a bucket.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, name):
        """
        Retrieve a given object from this bucket.

        :type name: ``str``
        :param name: The identifier of the object to retrieve

        :rtype: :class:``.BucketObject``
        :return: The BucketObject or ``None`` if it cannot be found.
        """
        pass

    @abstractmethod
    # pylint:disable=arguments-differ
    def list(self, limit=None, marker=None, prefix=None):
        """
        List objects in this bucket.

        :type limit: ``int``
        :param limit: Maximum number of elements to return.

        :type marker: ``int``
        :param marker: Fetch results after this offset.

        :type prefix: ``str``
        :param prefix: Prefix criteria by which to filter listed objects.

        :rtype: List of ``objects`` of :class:``.BucketObject``
        :return: List of all available BucketObjects within this bucket.
        """
        pass

    @abstractmethod
    def find(self, **kwargs):
        """
        Search for an object by a given list of attributes.

        Supported attributes: ``name``

        :rtype: List of ``objects`` of :class:`.BucketObject`
        :return: A list of BucketObjects matching the supplied attributes.

        :type limit: ``int``
        :param limit: Maximum number of elements to return.

        :type marker: ``int``
        :param marker: Fetch results after this offset.
        """
        pass

    @abstractmethod
    def create(self, name):
        """
        Create a new object within this bucket.

        :rtype: :class:``.BucketObject``
        :return: The newly created bucket object
        """
        pass
