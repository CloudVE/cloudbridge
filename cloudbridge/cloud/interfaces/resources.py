"""
Specifications for data objects exposed through a provider or service
"""
from abc import ABCMeta, abstractmethod, abstractproperty


class CloudProviderServiceType(object):

    """
    Defines possible service types that are offered by providers.

    Providers can implement the ``has_service`` method and clients can check
    for the availability of a service with::

        if (provider.has_service(CloudProviderServiceTypes.OBJECTSTORE))
            ...

    """
    COMPUTE = 'compute'
    IMAGE = 'image'
    SECURITY = 'security'
    VOLUME = 'volume'
    BLOCKSTORE = 'block_store'
    OBJECTSTORE = 'object_store'


class CloudBridgeBaseException(Exception):

    """
    Base class for all CloudBridge exceptions
    """
    pass


class WaitStateException(CloudBridgeBaseException):

    """
    Marker interface for object wait exceptions.
    Thrown when a timeout or errors occurs waiting for an object does not reach
    the expected state within a specified time limit.
    """
    pass


class InvalidConfigurationException(CloudBridgeBaseException):

    """
    Marker interface for invalid launch configurations.
    Thrown when a combination of parameters in a LaunchConfig
    object results in an illegal state.
    """
    pass


class Configuration(dict):
    """
    Represents a cloudbridge configuration object
    """

    @abstractproperty
    def default_result_limit(self):
        """
        Get the maximum number of results to return for a
        list method

        :rtype: ``int``
        :return: The maximum number of results to return
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
    will always have a state, defining which point in its lifecycle it is
    currently at.

    It also defines a wait_till_ready operation, which indicates that the
    object is in a state in its lifecycle where it is ready to be used by an
    end-user.

    A refresh operation allows the object to synchronise its state with the
    service provider.
    """
    __metaclass__ = ABCMeta

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
    def wait_for(self, target_states, terminal_states=None, timeout=600,
                 interval=5):
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
                terminal_states=[InstanceState.ERROR],
                interval=self.get_test_wait_interval())

        :type target_states: ``list`` of states
        :param target_states: The list of target states to wait for.

        :type terminal_states: ``list`` of states
        :param terminal_states: A list of terminal states after which the
        object will not transition into a target state. A WaitStateException
        will be raised if the object transition into a terminal state.

        :type timeout: int
        :param timeout: The maximum length of time (in seconds) to wait for the
                        object to become ready.

        :type interval: int
        :param interval: How frequently to poll the object's ready state (in
                         seconds).

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

        :type timeout: int
        :param timeout: The maximum length of time (in seconds) to wait for the
                        object to become ready.

        :type interval: int
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


class Instance(ObjectLifeCycleMixin):

    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the instance identifier.

        :rtype: str
        :return: ID for this instance as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get the instance name.

        :rtype: str
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

        :rtype: list
        :return: A list of public IP addresses associated with this instance.
        """
        pass

    @abstractproperty
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.

        :rtype: list
        :return: A list of private IP addresses associated with this instance.
        """
        pass

    @abstractproperty
    def instance_type(self):
        """
        Get the instance type.

        :rtype: :class:``.InstanceType``
        :return: API type of this instance (e.g., ``m1.large``)
        """
        pass

    @abstractmethod
    def reboot(self):
        """
        Reboot this instance (using the cloud middleware API).

        :rtype: bool
        :return: ``True`` if the reboot was succesful; ``False`` otherwise.
        """
        pass

    @abstractmethod
    def terminate(self):
        """
        Permanently terminate this instance.

        :rtype: bool
        :return: ``True`` if the termination of the instance was succesfully
                 initiated; ``False`` otherwise.
        """
        pass

    @abstractproperty
    def image_id(self):
        """
        Get the image ID for this insance.

        :rtype: str
        :return: Image ID (i.e., AMI) this instance is using.
        """
        pass

    @abstractproperty
    def placement_zone(self):
        """
        Get the placement zone where this instance is running.

        :rtype: str
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

        :rtype: list or :class:``SecurityGroup`` objects
        :return: A list of SecurityGroup objects associated with this instance.
        """
        pass

    @abstractproperty
    def key_pair_name(self):
        """
        Get the name of the key pair associated with this instance.

        :rtype: str
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

        :type ip_address: str
        :param ip_address: The IP address to associate with the instance.
        """
        pass

    @abstractmethod
    def remove_floating_ip(self, ip_address):
        """
        Remove a public IP address from this instance.

        :type ip_address: str
        :param ip_address: The IP address to remove from the instance.
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
    Represents an advanced launch configuration object, containing
    information such as BlockDeviceMappings, NetworkInterface configurations,
    and other advanced options which may be useful when launching an instance.

    Example:

    .. code-block:: python

        lc = provider.compute.instances.create_launch_config()
        lc.add_block_device(...)
        lc.add_network_interface(...)

        inst = provider.compute.instances.create(name, image, instance_type,
                                               launch_config=lc)
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

    @abstractmethod
    def add_network_interface(self, net_id):
        """
        Add a private network info to the launch configuration.

        Example:

        .. code-block:: python

            lc = provider.compute.instances.create_launch_config()

            # 1. Add a VPC subnet for use with AWS
            lc.add_network_interface('subnet-c24aeaff')

            # 2. Add a network ID for use with OpenStack
            lc.add_network_interface('5820c766-75fe-4fc6-96ef-798f67623238')

        :type net_id: str
        :param net_id: Network ID to launch an instance into. This is a
                       preliminary implementation (pending full private cloud
                       support within cloudbridge) so native network IDs need
                       to be supplied. For OpenStack, this is the Neutron
                       network ID. For AWS, this is a VPC subnet ID. For the
                       time being, only a single network interface can be
                       supplied.
        """
        pass


class MachineImage(ObjectLifeCycleMixin):

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

    @abstractmethod
    def delete(self):
        """
        Delete this image

        :rtype: ``bool``
        :return: ``True`` if the operation succeeded.
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


class Volume(ObjectLifeCycleMixin):

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

    @abstractmethod
    def attach(self, instance_id, device):
        """
        Attach this volume to an instance.

        :type instance_id: str
        :param instance_id: The ID of the instance to which it will
                            be attached.

        :type device: str
        :param device: The device on the instance through which the
                       volume will be exposed (e.g. /dev/sdh).

        :rtype: bool
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def detach(self, force=False):
        """
        Detach this volume from an instance.

        :type force: bool
        :param force: Forces detachment if the previous detachment attempt
                      did not occur cleanly. This option is supported on select
                      clouds only. This option can lead to data loss or a
                      corrupted file system. Use this option only as a last
                      resort to detach a volume from a failed instance. The
                      instance will not have an opportunity to flush file
                      system caches nor file system meta data. If you
                      use this option, you must perform file system check and
                      repair procedures.

        :rtype: bool
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def create_snapshot(self, name, description=None):
        """
        Create a snapshot of this Volume.

        :type name: str
        :param name: The name of this snapshot.

        :type description: str
        :param description: A description of the snapshot.
                            Limited to 256 characters.

        :rtype: :class:``.Snapshot``
        :return: The created Snapshot object.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this volume.

        :rtype: bool
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


class Snapshot(ObjectLifeCycleMixin):

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
        set the snapshot name.
        """
        pass

    @abstractmethod
    def create_volume(self, placement, size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.

        :type zone: str
        :param zone: The availability zone in which the Volume will be created.

        :type size: int
        :param size: The size of the new volume, in GiB (optional). Defaults to
                     the size of the snapshot.

        :type volume_type: str
        :param volume_type: The type of the volume (optional). Availability and
                            valid values depend on the provider.

        :type iops: int
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

        :rtype: bool
        :return: ``True`` if successful.
        """
        pass


class KeyPair(object):

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

        :rtype: str
        :return: A name of this ssh key pair.
        """
        pass

    @abstractproperty
    def material(self):
        """
        Unencrypted private key.

        :rtype: str
        :return: Unencrypted private key or ``None`` if not available.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this key pair.

        :rtype: bool
        :return: ``True`` is successful.
        """
        pass


class Region(object):

    """
    Represents a cloud region, typically a separate geographic area and will
    contain at least one placement zone.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        The id for this region

        :rtype: str
        :return: ID of the region.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Name of the region.

        :rtype: str
        :return: Name of the region.
        """
        pass

    @abstractproperty
    def zones(self):
        """
        Accesss information about placement zones within this region.

        :rtype: iterable
        :return: Iterable of available placement zones in this region.
        """
        pass


class PlacementZone(object):

    """
    Represents a placement zone. A placement zone is contained within a Region.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Name of the placement zone.

        :rtype: str
        :return: Name of the placement zone.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Name of the placement zone.

        :rtype: str
        :return: Name of the placement zone.
        """
        pass

    @abstractproperty
    def region(self):
        """
        A region this placement zone is associated with.

        :rtype: str
        :return: The name of the region the zone is associated with.
        """
        pass


class InstanceType(object):

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

        :rtype: str
        :return: Name of the instance family or ``None``.
        """
        pass

    @abstractproperty
    def vcpus(self):
        """
        The number of VCPUs supported by this instance type.

        :rtype: int
        :return: Number of VCPUs.
        """
        pass

    @abstractproperty
    def ram(self):
        """
        The amount of RAM (in mb) supported by this instance type.

        :rtype: int
        :return: Total RAM (in MB).
        """
        pass

    @abstractproperty
    def size_root_disk(self):
        """
        The size of this instance types's root disk (in GB).

        :rtype: int
        :return: Size of root disk (in GB).
        """
        pass

    @abstractproperty
    def size_ephemeral_disks(self):
        """
        The size of this instance types's total ephemeral storage (in GB).

        :rtype: int
        :return: Size of ephemeral disks (in GB).
        """
        pass

    @abstractproperty
    def num_ephemeral_disks(self):
        """
        The total number of ephemeral disks on this instance type.

        :rtype: int
        :return: Number of ephemeral disks available.
        """
        pass

    @abstractproperty
    def size_total_disk(self):
        """
        The total disk space available on this instance type
        (root_disk + ephemeral).

        :rtype: int
        :return: Size of total disk space (in GB).
        """
        pass

    @abstractproperty
    def extra_data(self):
        """
        A dictionary of extra data about this instance. May contain
        nested dictionaries, but all key value pairs are strings or integers.

        :rtype: dict
        :return: Extra attributes for this instance type.
        """
        pass


class SecurityGroup(object):

    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get the ID of this security group.

        :rtype: str
        :return: Security group ID.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Return the name of this security group.

        :rtype: str
        :return: A name of this security group.
        """
        pass

    @abstractproperty
    def description(self):
        """
        Return the description of this security group.

        :rtype: str
        :return: A description of this security group.
        """
        pass

    @abstractproperty
    def rules(self):
        """
        Get the list of rules for this security group.

        :rtype: list of :class:``.SecurityGroupRule``
        :return: A list of security group rule objects.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this security group.

        :rtype: bool
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def add_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        """
        Create a security group rule.

        You need to pass in either ``src_group`` OR ``ip_protocol``,
        ``from_port``, ``to_port``, and ``cidr_ip``.  In other words, either
        you are authorizing another group or you are authorizing some
        ip-based rule.

        :type ip_protocol: str
        :param ip_protocol: Either ``tcp`` | ``udp`` | ``icmp``.

        :type from_port: int
        :param from_port: The beginning port number you are enabling.

        :type to_port: int
        :param to_port: The ending port number you are enabling.

        :type cidr_ip: str or list of strings
        :param cidr_ip: The CIDR block you are providing access to.

        :type src_group: :class:``.SecurityGroup``
        :param src_group: The Security Group object you are granting access to.

        :rtype: bool
        :return: ``True`` if successful.
        """
        pass


class SecurityGroupRule(object):

    """
    Represents a security group rule.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def ip_protocol(self):
        """
        IP protocol used. Either ``tcp`` | ``udp`` | ``icmp``.
        """
        pass

    @abstractproperty
    def from_port(self):
        """
        Lowest port number opened as part of this rule.
        """
        pass

    @abstractproperty
    def to_port(self):
        """
        Highest port number opened as part of this rule.
        """
        pass

    @abstractproperty
    def cidr_ip(self):
        """
        CIDR block this security group is providing access to.
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


class BucketObject(object):

    """
    Represents an object stored within a bucket.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get this object's id.

        :rtype: id
        :return: id of this object as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get this object's name.

        :rtype: str
        :return: Name of this object as returned by the cloud middleware.
        """
        pass

    @abstractmethod
    def download(self, target_stream):
        """
        Download this object and write its contents to the ``target_stream``.

        :rtype: bool
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def upload(self, source_stream):
        """
        Set the contents of this object to the data read from the source
        stream.

        :rtype: bool
        :return: ``True`` if successful.
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete this object.

        :rtype: bool
        :return: ``True`` if successful.
        """
        pass


class Bucket(PageableObjectMixin):

    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        """
        Get this bucket's id.

        :rtype: id
        :return: id of this bucket as returned by the cloud middleware.
        """
        pass

    @abstractproperty
    def name(self):
        """
        Get this bucket's name.

        :rtype: str
        :return: Name of this bucket as returned by the cloud middleware.
        """
        pass

    @abstractmethod
    def get(self, key):
        """
        Retrieve a given object from this bucket.

        :type key: str
        :param key: the identifier of the object to retrieve

        :rtype: :class:``.BucketObject``
        :return: The BucketObject or ``None`` if it cannot be found.
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all objects within this bucket.

        :rtype: :class:``.BucketObject``
        :return: List of all available BucketObjects within this bucket.
        """
        pass

    @abstractmethod
    def delete(self, delete_contents=False):
        """
        Delete this bucket.

        :type delete_contents: bool
        :param delete_contents: If ``True``, all objects within the bucket
                                will be deleted.

        :rtype: bool
        :return: ``True`` if successful.
        """
        pass
