"""
Specifications for data objects exposed through a provider or service
"""
from abc import ABCMeta, abstractmethod, abstractproperty


class CloudServiceType(object):

    """
    Defines possible service types that are offered by providers.

    Providers can implement the ``has_service`` method and clients can check
    for the availability of a service with::

        if (provider.has_service(CloudServiceTypes.OBJECTSTORE))
            ...

    """
    COMPUTE = 'compute'
    IMAGE = 'image'
    SECURITY = 'security'
    VOLUME = 'volume'
    BLOCKSTORE = 'block_store'
    OBJECTSTORE = 'object_store'


class CloudResource(object):

    """
    Base interface for any Resource supported by a provider. This interface
    has an  _provider property that can be used to access the provider
    associated with the resource, which is only intended for use by subclasses.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def _provider(self):
        """
        Returns the provider instance associated with this resource. Intended
        for use by subclasses only.

        :rtype: :class:`.CloudProvider`
        :return: a CloudProvider object
        """
        pass

    @abstractmethod
    def to_json(self):
        """
        Returns a JSON representation of the CloudResource object.
        """
        pass


class Configuration(dict):
    """
    Represents a cloudbridge configuration object
    """

    @abstractproperty
    def default_result_limit(self):
        """
        Get the default maximum number of results to return for a
        list method. The default limit will be applied to most list()
        and find() methods whenever an explicit limit is not specified.

        :rtype: ``int``
        :return: The maximum number of results to return
        """
        pass

    @property
    def default_wait_timeout(self):
        """
        Gets the default wait timeout for LifeCycleObjects. The default
        wait timeout is applied in wait_for() and wait_till_ready() methods
        if no explicit timeout is specified.

        :rtype: ``int``
        :return: The maximum length of time (in seconds) to wait for the
                 object to change to desired state.
        """
        pass

    @property
    def default_wait_interval(self):
        """
        Gets the default wait interval for LifeCycleObjects. The default
        wait interval is applied in wait_for() and wait_till_ready() methods
        if no explicit interval is specified.

        :rtype: ``int``
        :return: How frequently to poll the object's state
        """
        pass

    @abstractproperty
    def debug_mode(self):
        """
        A flag indicating whether CloudBridge is in debug mode. Setting
        this to True will cause the underlying provider's debug
        output to be turned on.

        The flag can be toggled by sending in the cb_debug value via
        the config dictionary, or setting the CB_DEBUG environment variable.

        :rtype: ``bool``
        :return: Whether debug mode is on.
        """


class ObjectLifeCycleMixin(object):

    """
    A mixin for an object with a defined life-cycle, such as an Instance,
    Volume, Image or Snapshot. An object that supports ObjectLifeCycleMixin
    will always have a state, defining which point in its life cycle it is
    currently at.

    It also defines a wait_till_ready operation, which indicates that the
    object is in a state in its life cycle where it is ready to be used by an
    end-user.

    A refresh operation allows the object to synchronise its state with the
    service provider.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def _provider(self):
        """
        Obtain the provider associated with this object. Used internally
        to access the provider config and get default timeouts/intervals.

        :rtype: :class:`.CloudProvider`
        :return: The provider associated with this Resource
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
        Refreshs this object's state and synchronize it with the underlying
        service provider.
        """
        pass

    @abstractmethod
    def wait_for(self, target_states, terminal_states=None, timeout=None,
                 interval=None):
        """
        Wait for a specified timeout for an object to reach a set of desired
        target states. If the object does not reach the desired state within
        the specified timeout, a ``WaitStateException`` will be raised.
        The optional terminal_states property can be used to specify an
        additional set of states which, should the object reach one,
        the object thereafter will not transition into the desired target
        state. Should this happen, a ``WaitStateException`` will be raised.

        Example:

        .. code-block:: python

            instance.wait_for(
                [InstanceState.TERMINATED, InstanceState.UNKNOWN],
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
        A convenience method to wait till the current object reaches a state
        which is ready for use, which is any state where the end-user can
        successfully interact with the object.
        Will throw a ``WaitStateException`` if the object is not ready within
        the specified timeout.

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
    A marker interface for objects which support paged iteration through
    a list of objects with a list(limit, marker) method.
    """

    @abstractmethod
    def __iter__(self):
        """
        Enables iteration through this object. Typically, an implementation
        will call the list(limit, marker) method to transparently page
        additional objects in as iteration progresses.
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
    This is a wrapper class around a standard Python :py:class:`list` class
    and provides some extra properties to aid with paging through a large
    number of results.

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
        This is an opaque identifier used to assist in paging through very long
        lists of objects. This marker can be provided to the list method to get
        the next set of results.
        """
        pass

    @abstractproperty
    def is_truncated(self):
        """
        Indicates whether this result list has more results
        that can be paged in.
        """
        pass

    @abstractproperty
    def supports_total(self):
        """
        Indicates whether the provider supports returning the total number of
        available results. The supports_total property should be checked
        before accessing the total_results property.
        """
        pass

    @abstractproperty
    def total_results(self):
        """
        Indicates the total number of results for a particular query. The
        supports_total property should be used to check whether the provider
        supports returning the total number of results, before accessing this
        property, or the behaviour is indeterminate.
        """
        pass

    @abstractproperty
    def supports_server_paging(self):
        """
        Indicates whether this ResultList supports client side paging or server
        side paging. If server side paging is not supported, the data property
        provides direct access to all available data.
        """
        pass

    @abstractproperty
    def data(self):
        pass


class InstanceState(object):

    """
    Standard states for a node

    :cvar UNKNOWN: Instance state unknown.
    :cvar PENDING: Instance is pending
    :cvar CONFIGURING: Instance is being reconfigured in some way.
    :cvar RUNNING: Instance is running.
    :cvar REBOOTING: Instance is rebooting.
    :cvar TERMINATED: Instance is terminated. No further operations possible.
    :cvar STOPPED: Instance is stopped. Instance can be resumed.
    :cvar ERROR: Instance is in an error state. No further operations possible.

    """
    UNKNOWN = "unknown"
    PENDING = "pending"
    CONFIGURING = "configuring"
    RUNNING = "running"
    REBOOTING = "rebooting"
    TERMINATED = "terminated"
    STOPPED = "stopped"
    ERROR = "error"


class Instance(ObjectLifeCycleMixin, CloudResource):

    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the instance identifier.

        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get the instance name.

        :rtype: ``str``
        :return: Name for this instance as returned by the cloud middleware.
        """
        pass

    @name.setter
    @abstractmethod
    def name(self, value):
        """
        Set the instance name.
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
    def instance_type_id(self):
        """
        Get the instance type id for this instance. This will typically be a
        string value like 'm1.large'. On OpenStack, this may be a number or
        UUID. To get the full :class:``.InstanceType``
        object, you can use the instance.instance_type property instead.

        :rtype: ``str``
        :return: Instance type name for this instance (e.g., ``m1.large``)
        """
        pass

    @abstractproperty
    def instance_type(self):
        """
        Retrieve full instance type information for this instance.

        :rtype: :class:`.InstanceType`
        :return: Instance type for this instance
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
    def terminate(self):
        """
        Permanently terminate this instance.
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
    def security_groups(self):
        """
        Get the security groups associated with this instance.

        :rtype: list or :class:`.SecurityGroup` objects
        :return: A list of SecurityGroup objects associated with this instance.
        """
        pass

    @abstractproperty
    def security_group_ids(self):
        """
        Get the IDs of the security groups associated with this instance.

        :rtype: list or :class:``str``
        :return: A list of the SecurityGroup IDs associated with this instance.
        """
        pass

    @abstractproperty
    def key_pair_name(self):
        """
        Get the name of the key pair associated with this instance.

        :rtype: ``str``
        :return: Name of the ssh key pair associated with this instance.
        """
        pass

    @abstractmethod
    def create_image(self, name):
        """
        Create a new image based on this instance.

        :rtype: :class:``.Image``
        :return:  an Image object
        """
        pass

    @abstractmethod
    def add_floating_ip(self, ip_address):
        """
        Add a public IP address to this instance.

        :type ip_address: ``str``
        :param ip_address: The IP address to associate with the instance.
        """
        pass

    @abstractmethod
    def remove_floating_ip(self, ip_address):
        """
        Remove a public IP address from this instance.

        :type ip_address: ``str``
        :param ip_address: The IP address to remove from the instance.
        """
        pass

    @abstractmethod
    def add_security_group(self, sg):
        """
        Add a security group to this instance

        :type sg: ``SecurityGroup``
        :param sg: The SecurityGroup to associate with the instance.
        """
        pass

    @abstractmethod
    def remove_security_group(self, sg):
        """
        Remove a security group from this instance

        :type sg: ``SecurityGroup``
        :param sg: The SecurityGroup to associate with the instance.
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

    Theis object can contain information such as BlockDeviceMappings
    configurations, and other advanced options which may be useful when
    launching an instance.

    Example:

    .. code-block:: python

        lc = provider.compute.instances.create_launch_config()
        lc.add_block_device(...)

        inst = provider.compute.instances.create(name, image, instance_type,
                                                 network, launch_config=lc)
    """

    @abstractmethod
    def add_ephemeral_device(self):
        """
        Adds a new ephemeral block device mapping to the boot configuration.
        This can be used to add existing ephemeral devices to the instance.
        (The total number of ephemeral devices available for a particular
        InstanceType can be determined by querying the InstanceTypes service).
        Note that on some services, such as AWS, ephemeral devices must be
        added in as a device mapping at instance creation time, and cannot be
        added afterwards.

        Note that the device name, such as /dev/sda1, cannot be selected at
        present, since this tends to be provider and instance type specific.
        However, the order of device addition coupled with device type will
        generally determine naming order, with devices added first getting
        lower letters than instances added later.

        Example:

        .. code-block:: python

            lc = provider.compute.instances.create_launch_config()

            # 1. Add all available ephemeral devices
            inst_type = provider.compute.instance_types.find(name='m1.tiny')[0]
            for i in range(inst_type.num_ephemeral_disks):
                lc.add_ephemeral_device()
        """
        pass

    @abstractmethod
    def add_volume_device(self, source=None, is_root=None, size=None,
                          delete_on_terminate=None):
        """
        Adds a new volume based block device mapping to the boot configuration.
        The volume can be based on a snapshot, image, existing volume or
        be a blank new volume, and is specified by the source parameter.

        The property is_root can be set to True to override any existing root
        device mappings. Otherwise, the default behaviour is to add new block
        devices to the instance.

        Note that the device name, such as /dev/sda1, cannot be selected at
        present, since this tends to be provider and instance type specific.
        However, the order of device addition coupled with device type will
        generally determine naming order, with devices added first getting
        lower letters than instances added later (except when is_root is set).

        Example:

        .. code-block:: python

            lc = provider.compute.instances.create_launch_config()

            # 1. Create and attach an empty volume of size 100GB
            lc.add_volume_device(size=100, delete_on_terminate=True)

            # 2. Create and attach a volume based on a snapshot
            snap = provider.block_store.snapshots.get('<my_snapshot_id>')
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


class MachineImage(ObjectLifeCycleMixin, CloudResource):

    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the image identifier.

        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get the image name.

        :rtype: ``str``
        :return: Name for this image as returned by the cloud middleware.
        """
        pass

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
        Returns the minimum size of the disk that's required to
        boot this image (in GB)

        :rtype: ``int``
        :return: The minimum disk size needed by this image
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this image

        :rtype: ``bool``
        :return: ``True`` if the operation succeeded.
        """
        pass


class NetworkState(object):

    """
    Standard states for a network.

    :cvar UNKNOWN: Network state unknown.
    :cvar PENDING: Network is being created.
    :cvar AVAILABLE: Network is being available.
    :cvar DOWN = Network is not operational.
    :cvar ERROR = Network errored.
    """
    UNKNOWN = "unknown"
    PENDING = "pending"
    AVAILABLE = "available"
    DOWN = "down"
    ERROR = "error"


class Network(CloudResource):
    """
    Represents a software-defined network, like the Virtual Private Cloud.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the network identifier.

        :rtype: ``str``
        :return: ID for this network. Will generally correspond to the cloud
                 middleware's ID, but should be treated as an opaque value.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get the network name.

        :rtype: ``str``
        :return: Name for this network as returned by the cloud middleware.
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

    @abstractmethod
    def subnets(self):
        """
        The associated subnets.

        :rtype: ``list`` of :class:`.Subnet`
        :return: List of subnets associated with this network.
        """
        pass

    @abstractmethod
    def create_subnet(self, cidr_block, name=None, zone=None):
        """
        Create a new network subnet and associate it with this Network.

        :type cidr_block: ``str``
        :param cidr_block: CIDR block within this Network to assign to the
                           subnet.

        :type name: ``str``
        :param name: An optional subnet name. The name will be set if the
                     provider supports it.

        :type zone: ``str``
        :param zone: Placement zone where to create the subnet. Some providers
                     may not support subnet zones, in which case the value is
                     ignored.

        :rtype: ``object`` of :class:`.Subnet`
        :return:  A Subnet object
        """
        pass


class Subnet(CloudResource):
    """
    Represents a subnet, as part of a Network.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the subnet identifier.

        :rtype: ``str``
        :return: ID for this network. Will generally correspond to the cloud
                 middleware's ID, but should be treated as an opaque value.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get the subnet name.

        :rtype: ``str``
        :return: Name for this subnet as returned by the cloud middleware.
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


class FloatingIP(CloudResource):
    """
    Represents a floating (i.e., static) IP address.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the address identifier.

        :rtype: ``str``
        :return: ID for this network. Will generally correspond to the cloud
                 middleware's ID, but should be treated as an opaque value.
        """
        pass

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

    @abstractmethod
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


class Router(CloudResource):
    """
    Represents a private network router.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the router identifier.

        :rtype: ``str``
        :return: ID for this router. Will generally correspond to the cloud
                 middleware's ID, but should be treated as an opaque value.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get the router name, if available.

        :rtype: ``str``
        :return: Name for this router.
        """
        pass

    @abstractmethod
    def refresh(self):
        """
        Update this object.
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
    def attach_network(self, network_id):
        """
        Attach this router to a network.

        :type network_id: ``str``
        :param network_id: The ID of a network to which to attach this router.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def detach_network(self):
        """
        Detach this router from a network.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def add_route(self, subnet_id):
        """
        Add a route to this router.

        Note that a router must be attached to a network (to which the supplied
        subnet belongs to) before a route can be added.

        :type subnet_id: ``str``
        :param subnet_id: The ID of a subnet to add to this router.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def remove_route(self, subnet_id):
        """
        Remove a route from this router.

        :type subnet_id: ``str``
        :param subnet_id: The ID of a subnet to remove to this router.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass


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


class Volume(ObjectLifeCycleMixin, CloudResource):

    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the volume identifier.

        :rtype: ``str``
        :return: ID for this volume. Will generally correspond to the cloud
                 middleware's ID, but should be treated as an opaque value.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get the volume name.

        :rtype: ``str``
        :return: Name for this volume as returned by the cloud middleware.
        """
        pass

    @name.setter
    @abstractmethod
    def name(self, value):
        """
        Set the volume name.
        """
        pass

    @abstractproperty
    def description(self):
        """
        Get the volume description. Some cloud providers may not support this
        property, and will return the volume name instead.

        :rtype: ``str``
        :return: Description for this volume as returned by the cloud
                 middleware.
        """
        pass

    @description.setter
    @abstractmethod
    def description(self, value):
        """
        Set the volume description. Some cloud providers may not support this
        property, and setting the description may have no effect. (Providers
        that do not support this property will always return the volume name
        as the description)
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
        If available, get the source that this volume is based on (can be
        a Snapshot or an Image). Returns None if no source.

        :rtype: ``Snapshot` or ``Image``
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
    def create_snapshot(self, name, description=None):
        """
        Create a snapshot of this Volume.

        :type name: ``str``
        :param name: The name of this snapshot.

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


class Snapshot(ObjectLifeCycleMixin, CloudResource):

    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the snapshot identifier.

        :rtype: ``str``
        :return: ID for this snapshot. Will generally correspond to the cloud
                 middleware's ID, but should be treated as an opaque value.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get the snapshot name.
        """
        pass

    @name.setter
    @abstractmethod
    def name(self, value):
        """
        Set the snapshot name.
        """
        pass

    @abstractproperty
    def description(self):
        """
        Get the snapshot description. Some cloud providers may not support this
        property, and will return the snapshot name instead.

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
        property will always return the snapshot name as the description).

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
        May return None if the source volume no longer exists.

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

    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Return the id of this key pair.

        :rtype: ``str``
        :return: ID for this snapshot. Will generally correspond to the cloud
                 middleware's name, but should be treated as an opaque value.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Return the name of this key pair.

        :rtype: ``str``
        :return: A name of this ssh key pair.
        """
        pass

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
    Represents a cloud region, typically a separate geographic area and will
    contain at least one placement zone.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        The id for this region

        :rtype: ``str``
        :return: ID of the region.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Name of the region.

        :rtype: ``str``
        :return: Name of the region.
        """
        pass

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
    Represents a placement zone. A placement zone is contained within a Region.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Name of the placement zone.

        :rtype: ``str``
        :return: Name of the placement zone.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Name of the placement zone.

        :rtype: ``str``
        :return: Name of the placement zone.
        """
        pass

    @abstractproperty
    def region_name(self):
        """
        A region this placement zone is associated with.

        :rtype: ``str``
        :return: The name of the region the zone is associated with.
        """
        pass


class InstanceType(CloudResource):

    """
    An instance type object.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        pass

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def family(self):
        """
        The family/group that this instance type belongs to.

        For example, General Purpose Instances or High-Memory Instances. If
        the provider does not support such a grouping, it may return ``None``.

        :rtype: ``str``
        :return: Name of the instance family or ``None``.
        """
        pass

    @abstractproperty
    def vcpus(self):
        """
        The number of VCPUs supported by this instance type.

        :rtype: ``int``
        :return: Number of VCPUs.
        """
        pass

    @abstractproperty
    def ram(self):
        """
        The amount of RAM (in MB) supported by this instance type.

        :rtype: ``int``
        :return: Total RAM (in MB).
        """
        pass

    @abstractproperty
    def size_root_disk(self):
        """
        The size of this instance types's root disk (in GB).

        :rtype: ``int``
        :return: Size of root disk (in GB).
        """
        pass

    @abstractproperty
    def size_ephemeral_disks(self):
        """
        The size of this instance types's total ephemeral storage (in GB).

        :rtype: ``int``
        :return: Size of ephemeral disks (in GB).
        """
        pass

    @abstractproperty
    def num_ephemeral_disks(self):
        """
        The total number of ephemeral disks on this instance type.

        :rtype: ``int``
        :return: Number of ephemeral disks available.
        """
        pass

    @abstractproperty
    def size_total_disk(self):
        """
        The total disk space available on this instance type
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
        :return: Extra attributes for this instance type.
        """
        pass


class SecurityGroup(CloudResource):

    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the ID of this security group.

        :rtype: ``str``
        :return: Security group ID.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Return the name of this security group.

        :rtype: ``str``
        :return: A name of this security group.
        """
        pass

    @abstractproperty
    def description(self):
        """
        Return the description of this security group.

        :rtype: ``str``
        :return: A description of this security group.
        """
        pass

    @abstractproperty
    def network_id(self):
        """
        Network ID with which this security group is associated.

        :rtype: ``str``
        :return: Provider-supplied network ID or ``None`` is not available.
        """
        pass

    @abstractproperty
    def rules(self):
        """
        Get the list of rules for this security group.

        :rtype: list of :class:`.SecurityGroupRule`
        :return: A list of security group rule objects.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this security group.

        :rtype: ``bool``
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def add_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        """
        Create a security group rule. If the rule already exists, simply
        returns it.

        You need to pass in either ``src_group`` OR ``ip_protocol`` AND
        ``from_port``, ``to_port``, ``cidr_ip``. In other words, either
        you are authorizing another group or you are authorizing some
        ip-based rule.

        :type ip_protocol: ``str``
        :param ip_protocol: Either ``tcp`` | ``udp`` | ``icmp``.

        :type from_port: ``int``
        :param from_port: The beginning port number you are enabling.

        :type to_port: ``int``
        :param to_port: The ending port number you are enabling.

        :type cidr_ip: ``str`` or list of ``str``
        :param cidr_ip: The CIDR block you are providing access to.

        :type src_group: :class:`.SecurityGroup`
        :param src_group: The Security Group object you are granting access to.

        :rtype: :class:`.SecurityGroupRule`
        :return: Rule object if successful or ``None``.
        """
        pass

    def get_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        """
        Get a security group rule with the specified parameters.

        You need to pass in either ``src_group`` OR ``ip_protocol`` AND
        ``from_port``, ``to_port``, and ``cidr_ip``. Note that when retrieving
        a group rule, this method will return only one rule although possibly
        several rules exist for the group rule. In that case, use the
        ``.rules`` property and filter the results as desired.

        :type ip_protocol: ``str``
        :param ip_protocol: Either ``tcp`` | ``udp`` | ``icmp``.

        :type from_port: ``int``
        :param from_port: The beginning port number you are enabling.

        :type to_port: ``int``
        :param to_port: The ending port number you are enabling.

        :type cidr_ip: ``str`` or list of ``str``
        :param cidr_ip: The CIDR block you are providing access to.

        :type src_group: :class:`.SecurityGroup`
        :param src_group: The Security Group object you are granting access to.

        :rtype: :class:`.SecurityGroupRule`
        :return: Role object if one can be found or ``None``.
        """
        pass


class SecurityGroupRule(CloudResource):

    """
    Represents a security group rule.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        ID for this rule.

        Note that this may be a CloudBridge-specific ID if the underlying
        provider does not support rule IDs.

        :rtype: ``str``
        :return: Role ID.
        """
        pass

    @abstractproperty
    def ip_protocol(self):
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
    def cidr_ip(self):
        """
        CIDR block this security group is providing access to.

        :rtype: ``str``
        :return: CIDR block.
        """
        pass

    @abstractproperty
    def group(self):
        """
        Security group given access permissions by this rule.

        :rtype: :class:``.SecurityGroup``
        :return: The Security Group with granting access.
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
    def id(self):
        """
        Get this object's id.

        :rtype: ``str``
        :return: id of this object as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get this object's name.

        :rtype: ``str``
        :return: Name of this object as returned by the cloud middleware.
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
        Set the contents of this object to the data read from the source
        stream.

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
    def generate_url(self, expires_in=0):
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


class Bucket(PageableObjectMixin, CloudResource):

    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get this bucket's id.

        :rtype: ``str``
        :return: ID of this bucket as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get this bucket's name.

        :rtype: ``str``
        :return: Name of this bucket as returned by the cloud middleware.
        """
        pass

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
    def list(self, limit=None, marker=None, prefix=None):
        """
        List objects in this bucket.

        :type limit: ``int``
        :param limit: Maximum number of elements to return.

        :type marker: ``int``
        :param marker: Fetch results after this offset.

        :type prefix: ``str``
        :param prefix: Prefix criteria by which to filter listed objects.

        :rtype: :class:``.BucketObject``
        :return: List of all available BucketObjects within this bucket.
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

    @abstractmethod
    def create_object(self, name):
        """
        Create a new object within this bucket.

        :rtype: :class:``.BucketObject``
        :return: The newly created bucket object
        """
        pass
