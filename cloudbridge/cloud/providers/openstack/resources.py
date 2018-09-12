"""
DataTypes used by this provider
"""
import inspect
import ipaddress
import logging
import os
try:
    from urllib.parse import urlparse
    from urllib.parse import urljoin
except ImportError:  # python 2
    from urlparse import urlparse
    from urlparse import urljoin

from keystoneclient.v3.regions import Region

from neutronclient.common.exceptions import PortNotFoundClient

import novaclient.exceptions as novaex

from openstack.exceptions import HttpException
from openstack.exceptions import NotFoundException
from openstack.exceptions import ResourceNotFound

import swiftclient
from swiftclient.service import SwiftService, SwiftUploadObject
from swiftclient.utils import generate_temp_url

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.base.resources import BaseAttachmentInfo
from cloudbridge.cloud.base.resources import BaseBucket
from cloudbridge.cloud.base.resources import BaseBucketContainer
from cloudbridge.cloud.base.resources import BaseBucketObject
from cloudbridge.cloud.base.resources import BaseFloatingIP
from cloudbridge.cloud.base.resources import BaseFloatingIPContainer
from cloudbridge.cloud.base.resources import BaseGatewayContainer
from cloudbridge.cloud.base.resources import BaseInstance
from cloudbridge.cloud.base.resources import BaseInternetGateway
from cloudbridge.cloud.base.resources import BaseKeyPair
from cloudbridge.cloud.base.resources import BaseMachineImage
from cloudbridge.cloud.base.resources import BaseNetwork
from cloudbridge.cloud.base.resources import BasePlacementZone
from cloudbridge.cloud.base.resources import BaseRegion
from cloudbridge.cloud.base.resources import BaseRouter
from cloudbridge.cloud.base.resources import BaseSnapshot
from cloudbridge.cloud.base.resources import BaseSubnet
from cloudbridge.cloud.base.resources import BaseVMFirewall
from cloudbridge.cloud.base.resources import BaseVMFirewallRule
from cloudbridge.cloud.base.resources import BaseVMFirewallRuleContainer
from cloudbridge.cloud.base.resources import BaseVMType
from cloudbridge.cloud.base.resources import BaseVolume
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.interfaces.exceptions import InvalidValueException
from cloudbridge.cloud.interfaces.resources import GatewayState
from cloudbridge.cloud.interfaces.resources import InstanceState
from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.interfaces.resources import NetworkState
from cloudbridge.cloud.interfaces.resources import RouterState
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import SubnetState
from cloudbridge.cloud.interfaces.resources import TrafficDirection
from cloudbridge.cloud.interfaces.resources import VolumeState
from cloudbridge.cloud.providers.openstack import helpers as oshelpers

ONE_GIG = 1048576000  # in bytes
FIVE_GIG = ONE_GIG * 5  # in bytes

log = logging.getLogger(__name__)


class OpenStackMachineImage(BaseMachineImage):

    # ref: http://docs.openstack.org/developer/glance/statuses.html
    IMAGE_STATE_MAP = {
        'queued': MachineImageState.PENDING,
        'saving': MachineImageState.PENDING,
        'active': MachineImageState.AVAILABLE,
        'killed': MachineImageState.ERROR,
        'deleted': MachineImageState.UNKNOWN,
        'pending_delete': MachineImageState.PENDING,
        'deactivated': MachineImageState.ERROR
    }

    def __init__(self, provider, os_image):
        super(OpenStackMachineImage, self).__init__(provider)
        if isinstance(os_image, OpenStackMachineImage):
            # pylint:disable=protected-access
            self._os_image = os_image._os_image
        else:
            self._os_image = os_image

    @property
    def id(self):
        """
        Get the image identifier.
        """
        return self._os_image.id

    @property
    def name(self):
        """
        Get the image identifier.
        """
        return self._os_image.id

    @property
    def label(self):
        """
        Get the image label.
        """
        return self._os_image.name

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        """
        Set the image label.
        """
        self.assert_valid_resource_label(value)
        self._provider.os_conn.image.update_image(
            self._os_image, name=value or "")

    @property
    def description(self):
        """
        Get the image description.
        """
        return None

    @property
    def min_disk(self):
        """
        Returns the minimum size of the disk that's required to
        boot this image (in GB)

        :rtype: ``int``
        :return: The minimum disk size needed by this image
        """
        return self._os_image.min_disk

    def delete(self):
        """
        Delete this image
        """
        self._os_image.delete(self._provider.os_conn.session)

    @property
    def state(self):
        return OpenStackMachineImage.IMAGE_STATE_MAP.get(
            self._os_image.status, MachineImageState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        log.debug("Refreshing OpenStack Machine Image")
        image = self._provider.compute.images.get(self.id)
        if image:
            self._os_image = image._os_image  # pylint:disable=protected-access
        else:
            # The image no longer exists and cannot be refreshed.
            # set the status to unknown
            self._os_image.status = 'unknown'


class OpenStackPlacementZone(BasePlacementZone):

    def __init__(self, provider, zone, region):
        super(OpenStackPlacementZone, self).__init__(provider)
        if isinstance(zone, OpenStackPlacementZone):
            # pylint:disable=protected-access
            self._os_zone = zone._os_zone
            # pylint:disable=protected-access
            self._os_region = zone._os_region
        else:
            self._os_zone = zone
            self._os_region = region

    @property
    def id(self):
        """
        Get the zone id

        :rtype: ``str``
        :return: ID for this zone as returned by the cloud middleware.
        """
        return self._os_zone

    @property
    def name(self):
        """
        Get the zone name.

        :rtype: ``str``
        :return: Name for this zone as returned by the cloud middleware.
        """
        # return self._os_zone.zoneName
        return self._os_zone

    @property
    def region_name(self):
        """
        Get the region that this zone belongs to.

        :rtype: ``str``
        :return: Name of this zone's region as returned by the cloud middleware
        """
        return self._os_region


class OpenStackVMType(BaseVMType):

    def __init__(self, provider, os_flavor):
        super(OpenStackVMType, self).__init__(provider)
        self._os_flavor = os_flavor

    @property
    def id(self):
        return self._os_flavor.id

    @property
    def name(self):
        return self._os_flavor.name

    @property
    def family(self):
        # TODO: This may not be standardised across OpenStack
        # but NeCTAR is using it this way
        return self.extra_data.get('flavor_class:name')

    @property
    def vcpus(self):
        return self._os_flavor.vcpus

    @property
    def ram(self):
        return int(self._os_flavor.ram) / 1024

    @property
    def size_root_disk(self):
        return self._os_flavor.disk

    @property
    def size_ephemeral_disks(self):
        return 0 if self._os_flavor.ephemeral == 'N/A' else \
            self._os_flavor.ephemeral

    @property
    def num_ephemeral_disks(self):
        return 0 if self._os_flavor.ephemeral == 'N/A' else \
            self._os_flavor.ephemeral

    @property
    def extra_data(self):
        extras = self._os_flavor.get_keys()
        extras['rxtx_factor'] = self._os_flavor.rxtx_factor
        extras['swap'] = self._os_flavor.swap
        extras['is_public'] = self._os_flavor.is_public
        return extras


class OpenStackInstance(BaseInstance):

    # ref: http://docs.openstack.org/developer/nova/v2/2.0_server_concepts.html
    # and http://developer.openstack.org/api-ref-compute-v2.html
    INSTANCE_STATE_MAP = {
        'ACTIVE': InstanceState.RUNNING,
        'BUILD': InstanceState.PENDING,
        'DELETED': InstanceState.DELETED,
        'ERROR': InstanceState.ERROR,
        'HARD_REBOOT': InstanceState.REBOOTING,
        'PASSWORD': InstanceState.PENDING,
        'PAUSED': InstanceState.STOPPED,
        'REBOOT': InstanceState.REBOOTING,
        'REBUILD': InstanceState.CONFIGURING,
        'RESCUE': InstanceState.CONFIGURING,
        'RESIZE': InstanceState.CONFIGURING,
        'REVERT_RESIZE': InstanceState.CONFIGURING,
        'SOFT_DELETED': InstanceState.STOPPED,
        'STOPPED': InstanceState.STOPPED,
        'SUSPENDED': InstanceState.STOPPED,
        'SHUTOFF': InstanceState.STOPPED,
        'UNKNOWN': InstanceState.UNKNOWN,
        'VERIFY_RESIZE': InstanceState.CONFIGURING
    }

    def __init__(self, provider, os_instance):
        super(OpenStackInstance, self).__init__(provider)
        self._os_instance = os_instance

    @property
    def id(self):
        """
        Get the instance identifier.
        """
        return self._os_instance.id

    @property
    def name(self):
        """
        Get the instance identifier.
        """
        return self.id

    @property
    # pylint:disable=arguments-differ
    def label(self):
        """
        Get the instance label.
        """
        return self._os_instance.name

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        """
        Set the instance label.
        """
        self.assert_valid_resource_label(value)

        self._os_instance.name = value
        self._os_instance.update(name=value or "cb-inst")

    @property
    def public_ips(self):
        """
        Get all the public IP addresses for this instance.
        """
        # OpenStack doesn't provide an easy way to figure our whether an IP is
        # public or private, since the returned IPs are grouped by an arbitrary
        # network label. Therefore, it's necessary to parse the address and
        # determine whether it's public or private
        return [address
                for _, addresses in self._os_instance.networks.items()
                for address in addresses
                if not ipaddress.ip_address(address).is_private]

    @property
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        return [address
                for _, addresses in self._os_instance.networks.items()
                for address in addresses
                if ipaddress.ip_address(address).is_private]

    @property
    def vm_type_id(self):
        """
        Get the VM type name.
        """
        return self._os_instance.flavor.get('id')

    @property
    def vm_type(self):
        """
        Get the VM type object.
        """
        flavor = self._provider.nova.flavors.get(
            self._os_instance.flavor.get('id'))
        return OpenStackVMType(self._provider, flavor)

    def reboot(self):
        """
        Reboot this instance (using the cloud middleware API).
        """
        self._os_instance.reboot()

    def delete(self):
        """
        Permanently delete this instance.
        """
        # delete the port we created when launching
        # Assumption: it's the first interface in the list
        iface_list = self._os_instance.interface_list()
        if iface_list:
            self._provider.neutron.delete_port(iface_list[0].port_id)
        self._os_instance.delete()

    @property
    def image_id(self):
        """
        Get the image ID for this instance.
        """
        # In OpenStack, the Machine Image of a running instance may
        # be deleted, so make sure the image exists before attempting to
        # retrieve its id
        return (self._os_instance.image.get("id")
                if self._os_instance.image else "")

    @property
    def zone_id(self):
        """
        Get the placement zone where this instance is running.
        """
        return getattr(self._os_instance, 'OS-EXT-AZ:availability_zone', None)

    @property
    def subnet_id(self):
        """
        Extract (one) subnet id associated with this instance.

        In OpenStack, instances are associated with ports instead of
        subnets so we need to dig through several connections to retrieve
        the subnet_id. Further, there can potentially be several ports each
        connected to different subnets. This implementation retrieves one
        subnet, the one corresponding to port associated with the first
        private IP associated with the instance.
        """
        # MAC address can be used to identify a port so extract the MAC
        # address corresponding to the (first) private IP associated with the
        # instance.
        for net in self._os_instance.to_dict().get('addresses').keys():
            for iface in self._os_instance.to_dict().get('addresses')[net]:
                if iface.get('OS-EXT-IPS:type') == 'fixed':
                    port = iface.get('OS-EXT-IPS-MAC:mac_addr')
                    addr = iface.get('addr')
                    break
        # Now get a handle to a port with the given MAC address and get the
        # subnet to which the private IP is connected as the desired id.
        for prt in self._provider.neutron.list_ports().get('ports'):
            if prt.get('mac_address') == port:
                for ip in prt.get('fixed_ips'):
                    if ip.get('ip_address') == addr:
                        return ip.get('subnet_id')

    @property
    def vm_firewalls(self):
        return [
            self._provider.security.vm_firewalls.get(group.id)
            for group in self._os_instance.list_security_group()
        ]

    @property
    def vm_firewall_ids(self):
        """
        Get the VM firewall IDs associated with this instance.
        """
        return [fw.id for fw in self.vm_firewalls]

    @property
    def key_pair_id(self):
        """
        Get the id of the key pair associated with this instance.
        """
        return self._os_instance.key_name

    def create_image(self, label):
        """
        Create a new image based on this instance.
        """
        log.debug("Creating OpenStack Image with the label %s", label)
        self.assert_valid_resource_label(label)
        name = self._generate_name_from_label(label, 'cb-img')

        image_id = self._os_instance.create_image(name)
        img = OpenStackMachineImage(
            self._provider, self._provider.compute.images.get(image_id))
        img.label = label
        return img

    def _get_fip(self, floating_ip):
        """Get a floating IP object based on the supplied ID."""
        return OpenStackFloatingIP(
            self._provider,
            self._provider.os_conn.network.get_ip(floating_ip))

    def add_floating_ip(self, floating_ip):
        """
        Add a floating IP address to this instance.
        """
        log.debug("Adding floating IP adress: %s", floating_ip)
        fip = (floating_ip if isinstance(floating_ip, OpenStackFloatingIP)
               else self._get_fip(floating_ip))
        self._provider.os_conn.compute.add_floating_ip_to_server(
            self.id, fip.public_ip)

    def remove_floating_ip(self, floating_ip):
        """
        Remove a floating IP address from this instance.
        """
        log.debug("Removing floating IP adress: %s", floating_ip)
        fip = (floating_ip if isinstance(floating_ip, OpenStackFloatingIP)
               else self._get_fip(floating_ip))
        self._provider.os_conn.compute.remove_floating_ip_from_server(
            self.id, fip.public_ip)

    def add_vm_firewall(self, firewall):
        """
        Add a VM firewall to this instance
        """
        log.debug("Adding firewall: %s", firewall)
        self._os_instance.add_security_group(firewall.id)

    def remove_vm_firewall(self, firewall):
        """
        Remove a VM firewall from this instance
        """
        log.debug("Removing firewall: %s", firewall)
        self._os_instance.remove_security_group(firewall.id)

    @property
    def state(self):
        return OpenStackInstance.INSTANCE_STATE_MAP.get(
            self._os_instance.status, InstanceState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        instance = self._provider.compute.instances.get(
            self.id)
        if instance:
            # pylint:disable=protected-access
            self._os_instance = instance._os_instance
        else:
            # The instance no longer exists and cannot be refreshed.
            # set the status to unknown
            self._os_instance.status = 'unknown'


class OpenStackRegion(BaseRegion):

    def __init__(self, provider, os_region):
        super(OpenStackRegion, self).__init__(provider)
        self._os_region = os_region

    @property
    def id(self):
        return (self._os_region.id if type(self._os_region) == Region else
                self._os_region)

    @property
    def name(self):
        return self.id

    @property
    def zones(self):
        # ``detailed`` param must be set to ``False`` because the (default)
        # ``True`` value requires Admin privileges
        if self.name == self._provider.region_name:  # optimisation
            zones = self._provider.nova.availability_zones.list(detailed=False)
        else:
            try:
                # pylint:disable=protected-access
                region_nova = self._provider._connect_nova_region(self.name)
                zones = region_nova.availability_zones.list(detailed=False)
            except novaex.EndpointNotFound:
                # This region may not have a compute endpoint. If so just
                # return an empty list
                zones = []

        return [OpenStackPlacementZone(self._provider, z.zoneName, self.name)
                for z in zones]


class OpenStackVolume(BaseVolume):

    # Ref: http://developer.openstack.org/api-ref-blockstorage-v2.html
    VOLUME_STATE_MAP = {
        'creating': VolumeState.CREATING,
        'available': VolumeState.AVAILABLE,
        'attaching': VolumeState.CONFIGURING,
        'in-use': VolumeState.IN_USE,
        'deleting': VolumeState.CONFIGURING,
        'error': VolumeState.ERROR,
        'error_deleting': VolumeState.ERROR,
        'backing-up': VolumeState.CONFIGURING,
        'restoring-backup': VolumeState.CONFIGURING,
        'error_restoring': VolumeState.ERROR,
        'error_extending': VolumeState.ERROR
    }

    def __init__(self, provider, volume):
        super(OpenStackVolume, self).__init__(provider)
        self._volume = volume

    @property
    def id(self):
        return self._volume.id

    @property
    def name(self):
        return self.id

    @property
    # pylint:disable=arguments-differ
    def label(self):
        """
        Get the volume label.
        """
        return self._volume.name

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        """
        Set the volume label.
        """
        self.assert_valid_resource_label(value)
        self._volume.name = value
        self._volume.update(name=value or "")

    @property
    def description(self):
        return self._volume.description

    @description.setter
    def description(self, value):
        self._volume.description = value
        self._volume.update(description=value)

    @property
    def size(self):
        return self._volume.size

    @property
    def create_time(self):
        return self._volume.created_at

    @property
    def zone_id(self):
        return self._volume.availability_zone

    @property
    def source(self):
        if self._volume.snapshot_id:
            return self._provider.storage.snapshots.get(
                self._volume.snapshot_id)
        return None

    @property
    def attachments(self):
        if self._volume.attachments:
            return BaseAttachmentInfo(
                self,
                self._volume.attachments[0].get('server_id'),
                self._volume.attachments[0].get('device'))
        else:
            return None

    def attach(self, instance, device):
        """
        Attach this volume to an instance.
        """
        log.debug("Attaching %s to %s instance", device, instance)
        instance_id = instance.id if isinstance(
            instance,
            OpenStackInstance) else instance
        self._volume.attach(instance_id, device)

    def detach(self, force=False):
        """
        Detach this volume from an instance.
        """
        self._volume.detach()

    def create_snapshot(self, label, description=None):
        """
        Create a snapshot of this Volume.
        """
        log.debug("Creating snapchat of volume: %s with the "
                  "description: %s", label, description)
        return self._provider.storage.snapshots.create(
            label, self, description=description)

    def delete(self):
        """
        Delete this volume.
        """
        self._volume.delete()

    @property
    def state(self):
        return OpenStackVolume.VOLUME_STATE_MAP.get(
            self._volume.status, VolumeState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        vol = self._provider.storage.volumes.get(
            self.id)
        if vol:
            self._volume = vol._volume  # pylint:disable=protected-access
        else:
            # The volume no longer exists and cannot be refreshed.
            # set the status to unknown
            self._volume.status = 'unknown'


class OpenStackSnapshot(BaseSnapshot):

    # Ref: http://developer.openstack.org/api-ref-blockstorage-v2.html
    SNAPSHOT_STATE_MAP = {
        'creating': SnapshotState.PENDING,
        'available': SnapshotState.AVAILABLE,
        'deleting': SnapshotState.CONFIGURING,
        'error': SnapshotState.ERROR,
        'error_deleting': SnapshotState.ERROR
    }

    def __init__(self, provider, snapshot):
        super(OpenStackSnapshot, self).__init__(provider)
        self._snapshot = snapshot

    @property
    def id(self):
        return self._snapshot.id

    @property
    def name(self):
        return self.id

    @property
    # pylint:disable=arguments-differ
    def label(self):
        """
        Get the snapshot label.
        """
        return self._snapshot.name

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        """
        Set the snapshot label.
        """
        self.assert_valid_resource_label(value)
        self._snapshot.name = value
        self._snapshot.update(name=value or "")

    @property
    def description(self):
        return self._snapshot.description

    @description.setter
    def description(self, value):
        self._snapshot.description = value
        self._snapshot.update(description=value)

    @property
    def size(self):
        return self._snapshot.size

    @property
    def volume_id(self):
        return self._snapshot.volume_id

    @property
    def create_time(self):
        return self._snapshot.created_at

    @property
    def state(self):
        return OpenStackSnapshot.SNAPSHOT_STATE_MAP.get(
            self._snapshot.status, SnapshotState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        snap = self._provider.storage.snapshots.get(
            self.id)
        if snap:
            self._snapshot = snap._snapshot  # pylint:disable=protected-access
        else:
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            self._snapshot.status = 'unknown'

    def delete(self):
        """
        Delete this snapshot.
        """
        self._snapshot.delete()

    def create_volume(self, placement, size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.
        """
        vol_label = "from-snap-{0}".format(self.id or self.label)
        name = self._generate_name_from_label(vol_label, 'cb-vol')
        size = size if size else self._snapshot.size
        os_vol = self._provider.cinder.volumes.create(
            size, name=name, availability_zone=placement,
            snapshot_id=self._snapshot.id)
        cb_vol = OpenStackVolume(self._provider, os_vol)
        cb_vol.label = vol_label
        return cb_vol


class OpenStackGatewayContainer(BaseGatewayContainer):
    """For OpenStack, an internet gateway is a just an 'external' network."""

    def __init__(self, provider, network):
        super(OpenStackGatewayContainer, self).__init__(provider, network)

    def _check_fip_connectivity(self, external_net):
        # Due to current limitations in OpenStack:
        # https://bugs.launchpad.net/neutron/+bug/1743480, it's not
        # possible to differentiate between floating ip networks and provider
        # external networks. Therefore, we systematically step through
        # all available networks and perform an assignment test to infer valid
        # floating ip nets.
        dummy_router = self._provider.networking.routers.create(
            label='cb-conn-test-router', network=self._network)
        with cb_helpers.cleanup_action(lambda: dummy_router.delete()):
            try:
                dummy_router.attach_gateway(external_net)
                return True
            except Exception:
                return False

    def get_or_create_inet_gateway(self):
        """For OS, inet gtw is any net that has `external` property set."""
        external_nets = (n for n in self._provider.networking.networks
                         if n.external)
        for net in external_nets:
            if self._check_fip_connectivity(net):
                return OpenStackInternetGateway(self._provider, net)
        return None

    def delete(self, gateway):
        log.debug("Deleting OpenStack Gateway: %s", gateway)
        gateway.delete()

    def list(self, limit=None, marker=None):
        log.debug("OpenStack listing of all current internet gateways")
        igl = [OpenStackInternetGateway(self._provider, n)
               for n in self._provider.networking.networks
               if n.external and self._check_fip_connectivity(n)]
        return ClientPagedResultList(self._provider, igl, limit=limit,
                                     marker=marker)


class OpenStackNetwork(BaseNetwork):

    # Ref: https://github.com/openstack/neutron/blob/master/neutron/plugins/
    #      common/constants.py
    _NETWORK_STATE_MAP = {
        'PENDING_CREATE': NetworkState.PENDING,
        'PENDING_UPDATE': NetworkState.PENDING,
        'PENDING_DELETE': NetworkState.PENDING,
        'CREATED': NetworkState.PENDING,
        'INACTIVE': NetworkState.PENDING,
        'DOWN': NetworkState.DOWN,
        'ERROR': NetworkState.ERROR,
        'ACTIVE': NetworkState.AVAILABLE
    }

    def __init__(self, provider, network):
        super(OpenStackNetwork, self).__init__(provider)
        self._network = network
        self._gateway_service = OpenStackGatewayContainer(provider, self)

    @property
    def id(self):
        return self._network.get('id', None)

    @property
    def name(self):
        return self.id

    @property
    def label(self):
        return self._network.get('name', None)

    @label.setter
    def label(self, value):  # pylint:disable=arguments-differ
        """
        Set the network label.
        """
        self.assert_valid_resource_label(value)
        self._provider.neutron.update_network(
            self.id, {'network': {'name': value or ""}})
        self.refresh()

    @property
    def external(self):
        return self._network.get('router:external', False)

    @property
    def state(self):
        self.refresh()
        return OpenStackNetwork._NETWORK_STATE_MAP.get(
            self._network.get('status', None),
            NetworkState.UNKNOWN)

    @property
    def cidr_block(self):
        # OpenStack does not define a CIDR block for networks
        return ''

    def delete(self):
        if not self.external and self.id in str(
                self._provider.neutron.list_networks()):
            # If there are ports associated with the network, it won't delete
            ports = self._provider.neutron.list_ports(
                network_id=self.id).get('ports', [])
            for port in ports:
                try:
                    self._provider.neutron.delete_port(port.get('id'))
                except PortNotFoundClient:
                    # Ports could have already been deleted if instances
                    # are terminated etc. so exceptions can be safely ignored
                    pass
            self._provider.neutron.delete_network(self.id)

    @property
    def subnets(self):
        subnets = (self._provider.neutron.list_subnets(network_id=self.id)
                   .get('subnets', []))
        return [OpenStackSubnet(self._provider, subnet) for subnet in subnets]

    def refresh(self):
        """Refresh the state of this network by re-querying the provider."""
        network = self._provider.networking.networks.get(self.id)
        if network:
            # pylint:disable=protected-access
            self._network = network._network
        else:
            # subnet no longer exists
            self._network.state = NetworkState.UNKNOWN

    @property
    def gateways(self):
        return self._gateway_service


class OpenStackSubnet(BaseSubnet):

    def __init__(self, provider, subnet):
        super(OpenStackSubnet, self).__init__(provider)
        self._subnet = subnet
        self._state = None

    @property
    def id(self):
        return self._subnet.get('id', None)

    @property
    def name(self):
        return self.id

    @property
    def label(self):
        return self._subnet.get('name', None)

    @label.setter
    def label(self, value):  # pylint:disable=arguments-differ
        """
        Set the subnet label.
        """
        self.assert_valid_resource_label(value)
        self._provider.neutron.update_subnet(
            self.id, {'subnet': {'name': value or ""}})
        self._subnet['name'] = value

    @property
    def cidr_block(self):
        return self._subnet.get('cidr', None)

    @property
    def network_id(self):
        return self._subnet.get('network_id', None)

    @property
    def zone(self):
        """
        OpenStack does not have a notion of placement zone for subnets.

        Default to None.
        """
        return None

    def delete(self):
        if self.id in str(self._provider.neutron.list_subnets()):
            self._provider.neutron.delete_subnet(self.id)

    @property
    def state(self):
        return SubnetState.UNKNOWN if self._state == SubnetState.UNKNOWN \
             else SubnetState.AVAILABLE

    def refresh(self):
        subnet = self._provider.networking.subnets.get(self.id)
        if subnet:
            # pylint:disable=protected-access
            self._subnet = subnet._subnet
            self._state = SubnetState.AVAILABLE
        else:
            # subnet no longer exists
            self._state = SubnetState.UNKNOWN


class OpenStackFloatingIPContainer(BaseFloatingIPContainer):

    def __init__(self, provider, gateway):
        super(OpenStackFloatingIPContainer, self).__init__(provider, gateway)

    def get(self, fip_id):
        try:
            return OpenStackFloatingIP(
                self._provider, self._provider.os_conn.network.get_ip(fip_id))
        except (ResourceNotFound, NotFoundException):
            log.debug("Floating IP %s not found.", fip_id)
            return None

    def list(self, limit=None, marker=None):
        fips = [OpenStackFloatingIP(self._provider, fip)
                for fip in self._provider.os_conn.network.ips(
                    floating_network_id=self.gateway.id
                )]
        return ClientPagedResultList(self._provider, fips,
                                     limit=limit, marker=marker)

    def create(self):
        return OpenStackFloatingIP(
            self._provider, self._provider.os_conn.network.create_ip(
                floating_network_id=self.gateway.id))


class OpenStackFloatingIP(BaseFloatingIP):

    def __init__(self, provider, floating_ip):
        super(OpenStackFloatingIP, self).__init__(provider)
        self._ip = floating_ip

    @property
    def id(self):
        return self._ip.id

    @property
    def public_ip(self):
        return self._ip.floating_ip_address

    @property
    def private_ip(self):
        return self._ip.fixed_ip_address

    @property
    def in_use(self):
        return bool(self._ip.port_id)

    def delete(self):
        self._ip.delete(self._provider.os_conn.session)

    def refresh(self):
        net = self._provider.networking.networks.get(
            self._ip.floating_network_id)
        gw = net.gateways.get_or_create_inet_gateway()
        fip = gw.floating_ips.get(self.id)
        # pylint:disable=protected-access
        self._ip = fip._ip


class OpenStackRouter(BaseRouter):

    def __init__(self, provider, router):
        super(OpenStackRouter, self).__init__(provider)
        self._router = router

    @property
    def id(self):
        return self._router.get('id', None)

    @property
    def name(self):
        return self.id

    @property
    def label(self):
        return self._router.get('name', None)

    @label.setter
    def label(self, value):  # pylint:disable=arguments-differ
        """
        Set the router label.
        """
        self.assert_valid_resource_label(value)
        self._provider.neutron.update_router(
            self.id, {'router': {'name': value or ""}})
        self.refresh()

    def refresh(self):
        self._router = self._provider.neutron.show_router(self.id)['router']

    @property
    def state(self):
        if self._router.get('external_gateway_info'):
            return RouterState.ATTACHED
        return RouterState.DETACHED

    @property
    def network_id(self):
        if self.state == RouterState.ATTACHED:
            return self._router.get('external_gateway_info', {}).get(
                'network_id', None)
        return None

    def delete(self):
        self._provider.neutron.delete_router(self.id)

    def attach_subnet(self, subnet):
        router_interface = {'subnet_id': subnet.id}
        ret = self._provider.neutron.add_interface_router(
            self.id, router_interface)
        if subnet.id in ret.get('subnet_ids', ""):
            return True
        return False

    def detach_subnet(self, subnet):
        router_interface = {'subnet_id': subnet.id}
        ret = self._provider.neutron.remove_interface_router(
            self.id, router_interface)
        if subnet.id in ret.get('subnet_ids', ""):
            return True
        return False

    @property
    def subnets(self):
        # A router and a subnet are linked via a port, so traverse all ports
        # to find a list of subnets associated with the current router.
        subnets = []
        for prt in self._provider.neutron.list_ports().get('ports'):
            if prt.get('device_id') == self.id and \
               prt.get('device_owner') == 'network:router_interface':
                for fixed_ip in prt.get('fixed_ips'):
                    subnets.append(self._provider.networking.subnets.get(
                        fixed_ip.get('subnet_id')))
        return subnets

    def attach_gateway(self, gateway):
        self._provider.neutron.add_gateway_router(
            self.id, {'network_id': gateway.id})

    def detach_gateway(self, gateway):
        self._provider.neutron.remove_gateway_router(
            self.id).get('router', self._router)


class OpenStackInternetGateway(BaseInternetGateway):

    GATEWAY_STATE_MAP = {
        NetworkState.AVAILABLE: GatewayState.AVAILABLE,
        NetworkState.DOWN: GatewayState.ERROR,
        NetworkState.ERROR: GatewayState.ERROR,
        NetworkState.PENDING: GatewayState.CONFIGURING,
        NetworkState.UNKNOWN: GatewayState.UNKNOWN
    }

    def __init__(self, provider, gateway_net):
        super(OpenStackInternetGateway, self).__init__(provider)
        if isinstance(gateway_net, OpenStackNetwork):
            # pylint:disable=protected-access
            gateway_net = gateway_net._network
        self._gateway_net = gateway_net
        self._fips_container = OpenStackFloatingIPContainer(provider, self)

    @property
    def id(self):
        return self._gateway_net.get('id', None)

    @property
    def name(self):
        return self._gateway_net.get('name', None)

    @property
    def network_id(self):
        return self._gateway_net.get('id')

    def refresh(self):
        """Refresh the state of this network by re-querying the provider."""
        network = self._provider.networking.networks.get(self.id)
        if network:
            # pylint:disable=protected-access
            self._gateway_net = network._network
        else:
            # subnet no longer exists
            self._gateway_net.state = NetworkState.UNKNOWN

    @property
    def state(self):
        return self.GATEWAY_STATE_MAP.get(
            self._gateway_net.state, GatewayState.UNKNOWN)

    def delete(self):
        """Do nothing on openstack"""
        pass

    @property
    def floating_ips(self):
        return self._fips_container


class OpenStackKeyPair(BaseKeyPair):

    def __init__(self, provider, key_pair):
        super(OpenStackKeyPair, self).__init__(provider, key_pair)


class OpenStackVMFirewall(BaseVMFirewall):

    def __init__(self, provider, vm_firewall):
        super(OpenStackVMFirewall, self).__init__(provider, vm_firewall)
        self._rule_svc = OpenStackVMFirewallRuleContainer(provider, self)

    @property
    def network_id(self):
        """
        OpenStack does not associate a SG with a network so default to None.

        :return: Always return ``None``.
        """
        return None

    @property
    def name(self):
        """
        Return the name of this VM firewall.
        """
        return self.id

    @property
    def label(self):
        return self._vm_firewall.name

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._provider.os_conn.network.update_security_group(
            self.id, name=value or "")
        self.refresh()

    @property
    def rules(self):
        return self._rule_svc

    def delete(self):
        return self._vm_firewall.delete(self._provider.os_conn.session)

    def refresh(self):
        self._vm_firewall = self._provider.os_conn.network.get_security_group(
            self.id)

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = json_rules
        return js


class OpenStackVMFirewallRuleContainer(BaseVMFirewallRuleContainer):

    def __init__(self, provider, firewall):
        super(OpenStackVMFirewallRuleContainer, self).__init__(
            provider, firewall)

    def list(self, limit=None, marker=None):
        # pylint:disable=protected-access
        rules = [OpenStackVMFirewallRule(self.firewall, r)
                 for r in self.firewall._vm_firewall.security_group_rules]
        return ClientPagedResultList(self._provider, rules,
                                     limit=limit, marker=marker)

    def create(self,  direction, protocol=None, from_port=None,
               to_port=None, cidr=None, src_dest_fw=None):
        src_dest_fw_id = (src_dest_fw.id if isinstance(src_dest_fw,
                                                       OpenStackVMFirewall)
                          else src_dest_fw)

        try:
            if direction == TrafficDirection.INBOUND:
                os_direction = 'ingress'
            elif direction == TrafficDirection.OUTBOUND:
                os_direction = 'egress'
            else:
                raise InvalidValueException("direction", direction)
            # pylint:disable=protected-access
            rule = self._provider.os_conn.network.create_security_group_rule(
                security_group_id=self.firewall.id,
                direction=os_direction,
                port_range_max=to_port,
                port_range_min=from_port,
                protocol=protocol,
                remote_ip_prefix=cidr,
                remote_group_id=src_dest_fw_id)
            self.firewall.refresh()
            return OpenStackVMFirewallRule(self.firewall, rule.to_dict())
        except HttpException as e:
            self.firewall.refresh()
            # 409=Conflict, raised for duplicate rule
            if e.status_code == 409:
                existing = self.find(direction=direction, protocol=protocol,
                                     from_port=from_port, to_port=to_port,
                                     cidr=cidr, src_dest_fw_id=src_dest_fw_id)
                return existing[0]
            else:
                raise e


class OpenStackVMFirewallRule(BaseVMFirewallRule):

    def __init__(self, parent_fw, rule):
        super(OpenStackVMFirewallRule, self).__init__(parent_fw, rule)

    @property
    def id(self):
        return self._rule.get('id')

    @property
    def direction(self):
        direction = self._rule.get('direction')
        if direction == 'ingress':
            return TrafficDirection.INBOUND
        elif direction == 'egress':
            return TrafficDirection.OUTBOUND
        else:
            return None

    @property
    def protocol(self):
        return self._rule.get('protocol')

    @property
    def from_port(self):
        return self._rule.get('port_range_min')

    @property
    def to_port(self):
        return self._rule.get('port_range_max')

    @property
    def cidr(self):
        return self._rule.get('remote_ip_prefix')

    @property
    def src_dest_fw_id(self):
        fw = self.src_dest_fw
        if fw:
            return fw.id
        return None

    @property
    def src_dest_fw(self):
        fw_id = self._rule.get('remote_group_id')
        if fw_id:
            return self._provider.security.vm_firewalls.get(fw_id)
        return None

    def delete(self):
        self._provider.os_conn.network.delete_security_group_rule(self.id)
        self.firewall.refresh()


class OpenStackBucketObject(BaseBucketObject):

    def __init__(self, provider, cbcontainer, obj):
        super(OpenStackBucketObject, self).__init__(provider)
        self.cbcontainer = cbcontainer
        self._obj = obj

    @property
    def id(self):
        return self._obj.get("name")

    @property
    def name(self):
        """Get this object's name."""
        return self.id

    @property
    def size(self):
        return self._obj.get("bytes")

    @property
    def last_modified(self):
        return self._obj.get("last_modified")

    def iter_content(self):
        """Returns this object's content as an iterable."""
        _, content = self._provider.swift.get_object(
            self.cbcontainer.name, self.name, resp_chunk_size=65536)
        return content

    def upload(self, data):
        """
        Set the contents of this object to the data read from the source
        string.

        .. warning:: Will fail if the data is larger than 5 Gig.
        """
        self._provider.swift.put_object(self.cbcontainer.name, self.name,
                                        data)

    def upload_from_file(self, path):
        """
        Stores the contents of the file pointed by the ``path`` variable.
        If the file is bigger than 5 Gig, it will be broken into segments.

        :type path: ``str``
        :param path: Absolute path to the file to be uploaded to Swift.
        :rtype: ``bool``
        :return: ``True`` if successful, ``False`` if not.

        .. note::
            * The size of the segments chosen (or any of the other upload
              options) is not under user control.
            * If called this method will remap the
              ``swiftclient.service.get_conn`` factory method to
              ``self._provider._connect_swift``

        .. seealso:: https://github.com/CloudVE/cloudbridge/issues/35#issuecomment-297629661 # noqa
        """
        upload_options = {}
        if 'segment_size' not in upload_options:
            if os.path.getsize(path) >= FIVE_GIG:
                upload_options['segment_size'] = FIVE_GIG

        # remap the swift service's connection factory method
        # pylint:disable=protected-access
        swiftclient.service.get_conn = self._provider._connect_swift

        result = True
        with SwiftService() as swift:
            upload_object = SwiftUploadObject(path, object_name=self.name)
            for up_res in swift.upload(self.cbcontainer.name,
                                       [upload_object, ],
                                       options=upload_options):
                result = result and up_res['success']
        return result

    def delete(self):
        """
        Delete this object.

        :rtype: ``bool``
        :return: True if successful

        .. note:: If called this method will remap the
              ``swiftclient.service.get_conn`` factory method to
              ``self._provider._connect_swift``
        """

        # remap the swift service's connection factory method
        # pylint:disable=protected-access
        swiftclient.service.get_conn = self._provider._connect_swift

        result = True
        with SwiftService() as swift:
            for del_res in swift.delete(self.cbcontainer.name, [self.name, ]):
                result = result and del_res['success']
        return result

    def generate_url(self, expires_in):
        # Set a temp url key on the object (http://bit.ly/2NBiXGD)
        temp_url_key = "cloudbridge-tmp-url-key"
        self._provider.swift.post_account(
            headers={"x-account-meta-temp-url-key": temp_url_key})
        base_url = urlparse(self._provider.swift.get_service_auth()[0])
        access_point = "{0}://{1}".format(base_url.scheme, base_url.netloc)
        url_path = "/".join([base_url.path, self.cbcontainer.name, self.name])
        return urljoin(access_point, generate_temp_url(url_path, expires_in,
                                                       temp_url_key, 'GET'))

    def refresh(self):
        self._obj = self.cbcontainer.objects.get(self.id)._obj


class OpenStackBucket(BaseBucket):

    def __init__(self, provider, bucket):
        super(OpenStackBucket, self).__init__(provider)
        self._bucket = bucket
        self._object_container = OpenStackBucketContainer(provider, self)

    @property
    def id(self):
        return self._bucket.get("name")

    @property
    def name(self):
        return self.id

    @property
    def objects(self):
        return self._object_container

    def delete(self, delete_contents=False):
        self._provider.swift.delete_container(self.name)


class OpenStackBucketContainer(BaseBucketContainer):

    def __init__(self, provider, bucket):
        super(OpenStackBucketContainer, self).__init__(provider, bucket)

    def get(self, name):
        """
        Retrieve a given object from this bucket.
        """
        # Swift always returns a reference for the container first,
        # followed by a list containing references to objects.
        _, object_list = self._provider.swift.get_container(
            self.bucket.name, prefix=name)
        # Loop through list of objects looking for an exact name vs. a prefix
        for obj in object_list:
            if obj.get('name') == name:
                return OpenStackBucketObject(self._provider,
                                             self.bucket,
                                             obj)
        return None

    def list(self, limit=None, marker=None, prefix=None):
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        _, object_list = self._provider.swift.get_container(
            self.bucket.name,
            limit=oshelpers.os_result_limit(self._provider, limit),
            marker=marker, prefix=prefix)
        cb_objects = [OpenStackBucketObject(
            self._provider, self.bucket, obj) for obj in object_list]

        return oshelpers.to_server_paged_list(
            self._provider,
            cb_objects,
            limit)

    def find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def create(self, object_name):
        self._provider.swift.put_object(self.bucket.name, object_name, None)
        return self.get(object_name)
