"""
DataTypes used by this provider
"""
from __future__ import annotations

import inspect
import ipaddress
import logging
import os
import re
from datetime import datetime
from typing import Any
from typing import IO
from typing import Iterable
from typing import TYPE_CHECKING
from typing import cast
from urllib.parse import urljoin
from urllib.parse import urlparse

import keystoneclient.exceptions as keystoneex
from keystoneclient.v3.regions import Region

import swiftclient
from swiftclient.service import SwiftService
from swiftclient.service import SwiftUploadObject
from swiftclient.utils import generate_temp_url

from cloudbridge.base.resources import BaseAttachmentInfo
from cloudbridge.base.resources import BaseBucket
from cloudbridge.base.resources import BaseBucketObject
from cloudbridge.base.resources import BaseDnsRecord
from cloudbridge.base.resources import BaseDnsZone
from cloudbridge.base.resources import BaseFloatingIP
from cloudbridge.base.resources import BaseInstance
from cloudbridge.base.resources import BaseInternetGateway
from cloudbridge.base.resources import BaseKeyPair
from cloudbridge.base.resources import BaseMachineImage
from cloudbridge.base.resources import BaseNetwork
from cloudbridge.base.resources import BasePlacementZone
from cloudbridge.base.resources import BaseRegion
from cloudbridge.base.resources import BaseRouter
from cloudbridge.base.resources import BaseSnapshot
from cloudbridge.base.resources import BaseSubnet
from cloudbridge.base.resources import BaseVMFirewall
from cloudbridge.base.resources import BaseVMFirewallRule
from cloudbridge.base.resources import BaseVMType
from cloudbridge.base.resources import BaseVolume
from cloudbridge.interfaces.exceptions import ProviderInternalException
from cloudbridge.interfaces.resources import AttachmentInfo
from cloudbridge.interfaces.resources import Bucket
from cloudbridge.interfaces.resources import BucketObject
from cloudbridge.interfaces.resources import FloatingIP
from cloudbridge.interfaces.resources import Gateway
from cloudbridge.interfaces.resources import GatewayState
from cloudbridge.interfaces.resources import Instance
from cloudbridge.interfaces.resources import InstanceState
from cloudbridge.interfaces.resources import MachineImage
from cloudbridge.interfaces.resources import MachineImageState
from cloudbridge.interfaces.resources import NetworkState
from cloudbridge.interfaces.resources import RouterState
from cloudbridge.interfaces.resources import Snapshot
from cloudbridge.interfaces.resources import SnapshotState
from cloudbridge.interfaces.resources import Subnet
from cloudbridge.interfaces.resources import SubnetState
from cloudbridge.interfaces.resources import TrafficDirection
from cloudbridge.interfaces.resources import UploadConfig
from cloudbridge.interfaces.resources import VMFirewall
from cloudbridge.interfaces.resources import VMType
from cloudbridge.interfaces.resources import Volume
from cloudbridge.interfaces.resources import VolumeState

from .subservices import OpenStackBucketObjectSubService
from .subservices import OpenStackDnsRecordSubService
from .subservices import OpenStackFloatingIPSubService
from .subservices import OpenStackGatewaySubService
from .subservices import OpenStackSubnetSubService
from .subservices import OpenStackVMFirewallRuleSubService

if TYPE_CHECKING:
    from cloudbridge.providers.openstack.provider import OpenStackCloudProvider

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

    def __init__(self, provider: OpenStackCloudProvider,
                 os_image: Any) -> None:
        super(OpenStackMachineImage, self).__init__(provider)
        if isinstance(os_image, OpenStackMachineImage):
            # pylint:disable=protected-access
            self._os_image = cast(Any, os_image)._os_image
        else:
            self._os_image = os_image

    @property
    def id(self) -> str:
        """
        Get the image identifier.
        """
        return self._os_image.id

    @property
    def name(self) -> str:
        """
        Get the image identifier.
        """
        return self._os_image.id

    @property
    def label(self) -> str | None:
        """
        Get the image label.
        """
        return self._os_image.name

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        """
        Set the image label.
        """
        self.assert_valid_resource_label(value)
        cast("OpenStackCloudProvider", self._provider).os_conn.image \
            .update_image(self._os_image, name=value or "")

    @property
    def description(self) -> str | None:
        """
        Get the image description.
        """
        return None

    @property
    def min_disk(self) -> int | None:
        """
        Returns the minimum size of the disk that's required to
        boot this image (in GB)

        :rtype: ``int``
        :return: The minimum disk size needed by this image
        """
        return self._os_image.min_disk

    def delete(self) -> None:
        """
        Delete this image
        """
        self._os_image.delete(
            cast("OpenStackCloudProvider", self._provider).os_conn.image)

    @property
    def state(self) -> str:
        return OpenStackMachineImage.IMAGE_STATE_MAP.get(
            self._os_image.status, MachineImageState.UNKNOWN)

    def refresh(self) -> None:
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        log.debug("Refreshing OpenStack Machine Image")
        image = self._provider.compute.images.get(self.id)
        if image:
            # pylint:disable=protected-access
            self._os_image = cast(Any, image)._os_image
        else:
            # The image no longer exists and cannot be refreshed.
            # set the status to unknown
            self._os_image.status = 'unknown'


class OpenStackPlacementZone(BasePlacementZone):

    def __init__(self, provider: OpenStackCloudProvider, zone: Any,
                 region: Any) -> None:
        super(OpenStackPlacementZone, self).__init__(provider)
        if isinstance(zone, OpenStackPlacementZone):
            # pylint:disable=protected-access
            self._os_zone = cast(Any, zone)._os_zone
            # pylint:disable=protected-access
            self._os_region = cast(Any, zone)._os_region
        else:
            self._os_zone = zone
            self._os_region = region

    @property
    def id(self) -> str:
        """
        Get the zone id

        :rtype: ``str``
        :return: ID for this zone as returned by the cloud middleware.
        """
        return self._os_zone

    @property
    def name(self) -> str:
        """
        Get the zone name.

        :rtype: ``str``
        :return: Name for this zone as returned by the cloud middleware.
        """
        # return self._os_zone.zoneName
        return self._os_zone

    @property
    def region_name(self) -> str:
        """
        Get the region that this zone belongs to.

        :rtype: ``str``
        :return: Name of this zone's region as returned by the cloud middleware
        """
        return self._os_region


class OpenStackVMType(BaseVMType):

    def __init__(self, provider: OpenStackCloudProvider,
                 os_flavor: Any) -> None:
        super(OpenStackVMType, self).__init__(provider)
        self._os_flavor = os_flavor
        self._extra_data: dict[str, Any] | None = None

    @property
    def id(self) -> str:
        return self._os_flavor.id

    @property
    def name(self) -> str:
        return self._os_flavor.name

    @property
    def family(self) -> str | None:
        # TODO: This may not be standardised across OpenStack
        # but NeCTAR is using it this way
        return self.extra_data.get('flavor_class:name')

    @property
    def vcpus(self) -> int:
        return self._os_flavor.vcpus

    @property
    def ram(self) -> float:
        return int(self._os_flavor.ram) / 1024

    @property
    def size_root_disk(self) -> int:
        return self._os_flavor.disk

    @property
    def size_ephemeral_disks(self) -> int:
        return 0 if self._os_flavor.ephemeral == 'N/A' else \
            self._os_flavor.ephemeral

    @property
    def num_ephemeral_disks(self) -> int:
        return 0 if self._os_flavor.ephemeral == 'N/A' else \
            self._os_flavor.ephemeral

    @property
    def extra_data(self) -> dict[str, Any]:
        # get_keys() hits Nova's /flavors/<id>/os-extra_specs endpoint.
        # Cache the result so repeat property accesses (and family, which
        # delegates here) don't fan out to N concurrent API calls under
        # pytest-xdist load.
        if self._extra_data is None:
            extras = self._os_flavor.get_keys()
            extras['rxtx_factor'] = self._os_flavor.rxtx_factor
            extras['swap'] = self._os_flavor.swap
            extras['is_public'] = self._os_flavor.is_public
            self._extra_data = extras
        return self._extra_data


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

    def __init__(self, provider: OpenStackCloudProvider,
                 os_instance: Any) -> None:
        super(OpenStackInstance, self).__init__(provider)
        self._os_instance = os_instance

    @property
    def id(self) -> str:
        """
        Get the instance identifier.
        """
        return self._os_instance.id

    @property
    def name(self) -> str:
        """
        Get the instance identifier.
        """
        return self.id

    @property
    # pylint:disable=arguments-differ
    def label(self) -> str | None:
        """
        Get the instance label.
        """
        return self._os_instance.name

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        """
        Set the instance label.
        """
        self.assert_valid_resource_label(value)

        self._os_instance.name = value
        self._os_instance.update(name=value or "cb-inst")

    def _all_addresses(self) -> set[str]:
        """All IP addresses associated with this instance.

        Nova's info_cache (which backs ``server.addresses``) is refreshed
        by a periodic task on a ~60s cadence and is not re-queried on a
        plain server-show. That makes it lag both ways: a FIP just
        attached via Neutron won't appear, and a FIP just detached via
        Neutron will still appear. So we deliberately read only fixed
        IPs from Nova and ask Neutron live for the current floating IPs.
        """
        addrs: set[str] = set()
        for _, addr_list in self._os_instance.addresses.items():
            for entry in addr_list:
                if entry.get('OS-EXT-IPS:type') == 'floating':
                    continue
                ip = entry.get('addr') or entry.get('OS-EXT-IPS-MAC:addr')
                if ip:
                    addrs.add(ip)
        try:
            os_conn = cast("OpenStackCloudProvider", self._provider).os_conn
            for port in os_conn.network.ports(device_id=self.id):
                for fip in os_conn.network.ips(port_id=port.id):
                    if fip.floating_ip_address:
                        addrs.add(fip.floating_ip_address)
        except Exception as e:
            log.debug(
                "Could not enumerate floating IPs for instance %s: %s",
                self.id, e)
        return addrs

    @property
    def public_ips(self) -> list[str]:
        """
        Get all the public IP addresses for this instance.
        """
        # OpenStack doesn't provide an easy way to figure our whether an IP is
        # public or private, since the returned IPs are grouped by an arbitrary
        # network label. Therefore, it's necessary to parse the address and
        # determine whether it's public or private
        return [a for a in self._all_addresses()
                if not ipaddress.ip_address(a).is_private]

    @property
    def private_ips(self) -> list[str]:
        """
        Get all the private IP addresses for this instance.
        """
        return [a for a in self._all_addresses()
                if ipaddress.ip_address(a).is_private]

    @property
    def vm_type_id(self) -> str:
        """
        Get the VM type name.
        """
        return self._os_instance.flavor.get('id')

    @property
    def vm_type(self) -> VMType:
        """
        Get the VM type object.
        """
        flavor = cast("OpenStackCloudProvider", self._provider).nova \
            .flavors.get(self._os_instance.flavor.get('id'))
        return OpenStackVMType(
            cast("OpenStackCloudProvider", self._provider), flavor)

    @property
    def create_time(self) -> str | datetime:
        """
        Get the instance creation time
        """
        return datetime.strptime(
            self._os_instance.created, '%Y-%m-%dT%H:%M:%SZ')

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def reboot(self) -> None:
        """
        Reboot this instance (using the cloud middleware API).
        """
        self._os_instance.reboot()

    @property
    def image_id(self) -> str:
        """
        Get the image ID for this instance.
        """
        # In OpenStack, the Machine Image of a running instance may
        # be deleted, so make sure the image exists before attempting to
        # retrieve its id
        return (self._os_instance.image.get("id")
                if self._os_instance.image else "")

    @property
    def zone_id(self) -> str:
        """
        Get the placement zone where this instance is running.
        """
        zone = getattr(
            self._os_instance, 'OS-EXT-AZ:availability_zone', None)
        if zone is None:
            raise ProviderInternalException(
                "Instance {0} has no availability zone".format(self.id))
        return zone

    @property
    def subnet_id(self) -> str:
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
        port = None
        addr = None
        for net in self._os_instance.to_dict().get('addresses').keys():
            for iface in self._os_instance.to_dict().get('addresses')[net]:
                if iface.get('OS-EXT-IPS:type') == 'fixed':
                    port = iface.get('OS-EXT-IPS-MAC:mac_addr')
                    addr = iface.get('addr')
                    break
        # Now get a handle to a port with the given MAC address and get the
        # subnet to which the private IP is connected as the desired id.
        neutron = cast("OpenStackCloudProvider", self._provider).neutron
        for prt in neutron.list_ports().get('ports'):
            if prt.get('mac_address') == port:
                for ip in prt.get('fixed_ips'):
                    if ip.get('ip_address') == addr:
                        return ip.get('subnet_id')
        raise ProviderInternalException(
            "Could not determine a subnet for instance {0}".format(self.id))

    @property
    def vm_firewalls(self) -> list[VMFirewall]:
        return cast("list[VMFirewall]", [
            self._provider.security.vm_firewalls.get(group.id)
            for group in self._os_instance.list_security_group()
        ])

    @property
    def vm_firewall_ids(self) -> list[str]:
        """
        Get the VM firewall IDs associated with this instance.
        """
        return [fw.id for fw in self.vm_firewalls]

    @property
    def key_pair_id(self) -> str:
        """
        Get the id of the key pair associated with this instance.
        """
        return self._os_instance.key_name

    def create_image(self, label: str) -> MachineImage:
        """
        Create a new image based on this instance.
        """
        log.debug("Creating OpenStack Image with the label %s", label)
        self.assert_valid_resource_label(label)

        image_id = self._os_instance.create_image(label)
        img = OpenStackMachineImage(
            cast("OpenStackCloudProvider", self._provider),
            self._provider.compute.images.get(image_id))
        return img

    def _get_fip(self, floating_ip: FloatingIP | str) -> Any:
        """Get a floating IP object based on the supplied ID."""
        # The OpenStack FloatingIP service looks up by id alone and ignores
        # the gateway argument, so None is passed deliberately.
        # pylint:disable=protected-access
        return self._provider.networking._floating_ips.get(
            cast(Gateway, None), cast(str, floating_ip))

    def _primary_port(self) -> Any:
        """Return the first Neutron port on this instance, or None."""
        # pylint:disable=protected-access
        os_conn = cast("OpenStackCloudProvider", self._provider).os_conn
        return next(
            iter(os_conn.network.ports(device_id=self.id)),
            None)

    def add_floating_ip(self, floating_ip: FloatingIP | str) -> None:
        """
        Add a floating IP address to this instance.

        Nova's add_floating_ip server action was removed in microversion
        2.44 (Pike). The supported path is to set the FIP's port_id to
        one of the server's Neutron ports.
        """
        log.debug("Adding floating IP adress: %s", floating_ip)
        fip = (floating_ip if isinstance(floating_ip, OpenStackFloatingIP)
               else self._get_fip(floating_ip))
        port = self._primary_port()
        if not port:
            raise Exception(
                "Cannot add floating IP: instance {0} has no network port"
                .format(self.id))
        # pylint:disable=protected-access
        cast("OpenStackCloudProvider", self._provider).os_conn.network \
            .update_ip(fip._ip, port_id=port.id)

    def remove_floating_ip(self, floating_ip: FloatingIP | str) -> None:
        """
        Remove a floating IP address from this instance.

        Same rationale as add_floating_ip; the Nova action endpoint is
        gone, so detach by clearing port_id on the Neutron FIP. We go
        through neutronclient directly rather than openstacksdk
        Connection.network.update_ip(...) because some openstacksdk
        versions drop ``None`` kwargs from the PUT body, which leaves
        port_id unchanged on the server side.
        """
        log.debug("Removing floating IP adress: %s", floating_ip)
        fip = (floating_ip if isinstance(floating_ip, OpenStackFloatingIP)
               else self._get_fip(floating_ip))
        if fip is None:
            return
        cast("OpenStackCloudProvider", self._provider).neutron \
            .update_floatingip(fip.id, {'floatingip': {'port_id': None}})

    def add_vm_firewall(self, firewall: VMFirewall) -> None:
        """
        Add a VM firewall to this instance
        """
        log.debug("Adding firewall: %s", firewall)
        self._os_instance.add_security_group(firewall.id)

    def remove_vm_firewall(self, firewall: VMFirewall) -> None:
        """
        Remove a VM firewall from this instance
        """
        log.debug("Removing firewall: %s", firewall)
        self._os_instance.remove_security_group(firewall.id)

    @property
    def state(self) -> str:
        return OpenStackInstance.INSTANCE_STATE_MAP.get(
            self._os_instance.status, InstanceState.UNKNOWN)

    def refresh(self) -> None:
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        instance = self._provider.compute.instances.get(
            self.id)
        if instance:
            # pylint:disable=protected-access
            self._os_instance = cast(Any, instance)._os_instance
        else:
            # The instance no longer exists and cannot be refreshed.
            # set the status to unknown
            self._os_instance.status = 'unknown'


class OpenStackRegion(BaseRegion):

    def __init__(self, provider: OpenStackCloudProvider,
                 os_region: Any) -> None:
        super(OpenStackRegion, self).__init__(provider)
        self._os_region = os_region

    @property
    def id(self) -> str:
        return (self._os_region.id if type(self._os_region) is Region else
                self._os_region)

    @property
    def name(self) -> str:
        return self.id

    @property
    def zones(self) -> Iterable[OpenStackPlacementZone]:
        # ``detailed`` param must be set to ``False`` because the (default)
        # ``True`` value requires Admin privileges
        provider = cast("OpenStackCloudProvider", self._provider)
        if self.name == self._provider.region_name:  # optimisation
            zones = provider.nova.availability_zones.list(detailed=False)
        else:
            try:
                # pylint:disable=protected-access
                region_nova = provider._connect_nova_region(self.name)
                zones = region_nova.availability_zones.list(detailed=False)
            except keystoneex.EndpointNotFound:
                # This region may not have a compute endpoint. If so just
                # return an empty list
                zones = []

        return [OpenStackPlacementZone(provider, z.zoneName, self.name)
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

    def __init__(self, provider: OpenStackCloudProvider,
                 volume: Any) -> None:
        super(OpenStackVolume, self).__init__(provider)
        self._volume = volume

    @property
    def id(self) -> str:
        return self._volume.id

    @property
    def name(self) -> str:
        return self.id

    @property
    # pylint:disable=arguments-differ
    def label(self) -> str | None:
        """
        Get the volume label.
        """
        return self._volume.name

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        """
        Set the volume label.
        """
        self.assert_valid_resource_label(value)
        self._volume.name = value
        self._volume.commit(
            cast("OpenStackCloudProvider", self._provider).os_conn
            .block_storage)

    @property
    def description(self) -> str:
        return self._volume.description

    @description.setter
    def description(self, value: str) -> None:
        self._volume.description = value
        self._volume.commit(
            cast("OpenStackCloudProvider", self._provider).os_conn
            .block_storage)

    @property
    def size(self) -> int:
        return self._volume.size

    @property
    def create_time(self) -> str | datetime:
        return self._volume.created_at

    @property
    def zone_id(self) -> str:
        return self._volume.availability_zone

    @property
    def source(self) -> Snapshot | MachineImage | None:
        if self._volume.snapshot_id:
            return self._provider.storage.snapshots.get(
                self._volume.snapshot_id)
        return None

    @property
    def attachments(self) -> AttachmentInfo | None:
        if self._volume.attachments:
            return BaseAttachmentInfo(
                self,
                self._volume.attachments[0].get('server_id'),
                self._volume.attachments[0].get('device'))
        else:
            return None

    def attach(self, instance: str | Instance, device: str) -> None:
        """
        Attach this volume to an instance.
        """
        log.debug("Attaching %s to %s instance", device, instance)
        instance_id = instance.id if isinstance(
            instance,
            OpenStackInstance) else instance
        cast("OpenStackCloudProvider", self._provider).os_conn.compute \
            .create_volume_attachment(
                server=instance_id, volume_id=self.id, device=device)

    def detach(self, force: bool = False) -> None:
        """
        Detach this volume from an instance.
        """
        for attachment in self._volume.attachments:
            cast("OpenStackCloudProvider", self._provider).os_conn.compute \
                .delete_volume_attachment(
                    attachment['id'], attachment['server_id'])

    def create_snapshot(self, label: str,
                        description: str | None = None) -> Snapshot:
        """
        Create a snapshot of this Volume.
        """
        log.debug("Creating snapchat of volume: %s with the "
                  "description: %s", label, description)
        return self._provider.storage.snapshots.create(
            label, self, description=description)

    @property
    def state(self) -> str:
        return OpenStackVolume.VOLUME_STATE_MAP.get(
            self._volume.status, VolumeState.UNKNOWN)

    def refresh(self) -> None:
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        vol = self._provider.storage.volumes.get(
            self.id)
        if vol:
            # pylint:disable=protected-access
            self._volume = cast(Any, vol)._volume
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

    def __init__(self, provider: OpenStackCloudProvider,
                 snapshot: Any) -> None:
        super(OpenStackSnapshot, self).__init__(provider)
        self._snapshot = snapshot

    @property
    def id(self) -> str:
        return self._snapshot.id

    @property
    def name(self) -> str:
        return self.id

    @property
    # pylint:disable=arguments-differ
    def label(self) -> str | None:
        """
        Get the snapshot label.
        """
        return self._snapshot.name

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        """
        Set the snapshot label.
        """
        self.assert_valid_resource_label(value)
        self._snapshot.name = value
        self._snapshot.commit(
            cast("OpenStackCloudProvider", self._provider).os_conn
            .block_storage)

    @property
    def description(self) -> str:
        return self._snapshot.description

    @description.setter
    def description(self, value: str) -> None:
        self._snapshot.description = value
        self._snapshot.commit(
            cast("OpenStackCloudProvider", self._provider).os_conn
            .block_storage)

    @property
    def size(self) -> int:
        return self._snapshot.size

    @property
    def volume_id(self) -> str | None:
        return self._snapshot.volume_id

    @property
    def create_time(self) -> str | datetime:
        return self._snapshot.created_at

    @property
    def state(self) -> str:
        return OpenStackSnapshot.SNAPSHOT_STATE_MAP.get(
            self._snapshot.status, SnapshotState.UNKNOWN)

    def refresh(self) -> None:
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        snap = self._provider.storage.snapshots.get(
            self.id)
        if snap:
            # pylint:disable=protected-access
            self._snapshot = cast(Any, snap)._snapshot
        else:
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            self._snapshot.status = 'unknown'

    def create_volume(self, size: int | None = None,
                      volume_type: str | None = None,
                      iops: int | None = None) -> Volume:
        """
        Create a new Volume from this Snapshot.
        """
        vol_label = "from-snap-{0}".format(self.label or self.id)
        self.assert_valid_resource_label(vol_label)
        size = size if size else self._snapshot.size
        provider = cast("OpenStackCloudProvider", self._provider)
        os_vol = provider.os_conn.block_storage.create_volume(
            size=size, name=vol_label, snapshot_id=self._snapshot.id,
            availability_zone=provider.zone_name)
        cb_vol = OpenStackVolume(provider, os_vol)
        return cb_vol


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

    def __init__(self, provider: OpenStackCloudProvider,
                 network: Any) -> None:
        super(OpenStackNetwork, self).__init__(provider)
        self._network = network
        self._gateway_service = OpenStackGatewaySubService(provider, self)
        self._subnet_svc = OpenStackSubnetSubService(provider, self)

    @property
    def id(self) -> str:
        return self._network.get('id', None)

    @property
    def name(self) -> str:
        return self.id

    @property
    def label(self) -> str | None:
        return self._network.get('name', None)

    @label.setter
    def label(self, value: str) -> None:
        """
        Set the network label.
        """
        self.assert_valid_resource_label(value)
        cast("OpenStackCloudProvider", self._provider).neutron.update_network(
            self.id, {'network': {'name': value or ""}})
        self.refresh()

    @property
    def external(self) -> bool:
        return self._network.get('router:external', False)

    @property
    def shared(self) -> bool:
        return self._network.get('shared', False)

    @property
    def state(self) -> str:
        self.refresh()
        return OpenStackNetwork._NETWORK_STATE_MAP.get(
            self._network.get('status', None),
            NetworkState.UNKNOWN)

    @property
    def cidr_block(self) -> str:
        # OpenStack does not define a CIDR block for networks
        return ''

    @property
    def subnets(self) -> OpenStackSubnetSubService:
        return self._subnet_svc

    def refresh(self) -> None:
        """Refresh the state of this network by re-querying the provider."""
        network = self._provider.networking.networks.get(self.id)
        if network:
            # pylint:disable=protected-access
            self._network = cast(Any, network)._network
        else:
            # Network no longer exists
            self._network = {}

    @property
    def gateways(self) -> OpenStackGatewaySubService:
        return self._gateway_service


class OpenStackSubnet(BaseSubnet):

    def __init__(self, provider: OpenStackCloudProvider,
                 subnet: Any) -> None:
        super(OpenStackSubnet, self).__init__(provider)
        self._subnet = subnet
        self._state: str | None = None

    @property
    def id(self) -> str:
        return self._subnet.get('id', None)

    @property
    def name(self) -> str:
        return self.id

    @property
    def label(self) -> str | None:
        return self._subnet.get('name', None)

    @label.setter
    def label(self, value: str) -> None:  # pylint:disable=arguments-differ
        """
        Set the subnet label.
        """
        self.assert_valid_resource_label(value)
        cast("OpenStackCloudProvider", self._provider).neutron.update_subnet(
            self.id, {'subnet': {'name': value or ""}})
        self._subnet['name'] = value

    @property
    def cidr_block(self) -> str:
        return self._subnet.get('cidr', None)

    @property
    def network_id(self) -> str:
        return self._subnet.get('network_id', None)

    @property
    def zone(self) -> None:
        """
        OpenStack does not have a notion of placement zone for subnets.

        Default to None.
        """
        return None

    @property
    def state(self) -> str:
        return SubnetState.UNKNOWN if self._state == SubnetState.UNKNOWN \
             else SubnetState.AVAILABLE

    def refresh(self) -> None:
        subnet = self._provider.networking.subnets.get(self.id)
        if subnet:
            # pylint:disable=protected-access
            self._subnet = cast(Any, subnet)._subnet
            self._state = SubnetState.AVAILABLE
        else:
            # subnet no longer exists
            self._state = SubnetState.UNKNOWN


class OpenStackFloatingIP(BaseFloatingIP):

    def __init__(self, provider: OpenStackCloudProvider,
                 floating_ip: Any) -> None:
        super(OpenStackFloatingIP, self).__init__(provider)
        self._ip = floating_ip

    @property
    def id(self) -> str:
        return self._ip.id

    @property
    def public_ip(self) -> str:
        return self._ip.floating_ip_address

    @property
    def private_ip(self) -> str | None:
        return self._ip.fixed_ip_address

    @property
    def in_use(self) -> bool:
        return bool(self._ip.port_id)

    def refresh(self) -> None:
        net = cast("OpenStackNetwork", self._provider.networking.networks.get(
            self._ip.floating_network_id))
        gw = net.gateways.get_or_create()
        fip = gw.floating_ips.get(self.id)
        # pylint:disable=protected-access
        self._ip = cast(Any, fip)._ip

    @property
    def _gateway_id(self) -> str:
        return self._ip.floating_network_id


class OpenStackRouter(BaseRouter):

    def __init__(self, provider: OpenStackCloudProvider,
                 router: Any) -> None:
        super(OpenStackRouter, self).__init__(provider)
        self._router = router

    @property
    def id(self) -> str:
        router_id = getattr(self._router, 'id', None)
        if router_id is None:
            raise ProviderInternalException("Router has no id")
        return router_id

    @property
    def name(self) -> str:
        return self.id

    @property
    def label(self) -> str | None:
        return self._router.name

    @label.setter
    def label(self, value: str) -> None:  # pylint:disable=arguments-differ
        """
        Set the router label.
        """
        self.assert_valid_resource_label(value)
        self._router = cast("OpenStackCloudProvider", self._provider) \
            .os_conn.update_router(self.id, value)

    def refresh(self) -> None:
        self._router = cast("OpenStackCloudProvider", self._provider) \
            .os_conn.get_router(self.id)

    @property
    def state(self) -> str:
        if self._router.external_gateway_info:
            return RouterState.ATTACHED
        return RouterState.DETACHED

    @property
    def network_id(self) -> str | None:
        ports = cast("OpenStackCloudProvider", self._provider).os_conn \
            .list_ports(filters={'device_id': self.id})
        if ports:
            return ports[0].network_id
        return None

    def attach_subnet(self, subnet: Subnet | str) -> None:
        subnet_id = subnet.id if isinstance(subnet, OpenStackSubnet) else subnet
        cast("OpenStackCloudProvider", self._provider).os_conn \
            .add_router_interface(self._router.toDict(), subnet_id)

    def detach_subnet(self, subnet: Subnet | str) -> None:
        subnet_id = subnet.id if isinstance(subnet, OpenStackSubnet) else subnet
        cast("OpenStackCloudProvider", self._provider).os_conn \
            .remove_router_interface(self._router.toDict(), subnet_id)

    @property
    def subnets(self) -> list[Subnet]:
        # A router and a subnet are linked via a port, so traverse ports
        # associated with the current router to find a list of subnets
        # associated with it.
        subnets: list[Subnet | None] = []
        os_conn = cast("OpenStackCloudProvider", self._provider).os_conn
        for port in os_conn.list_ports(filters={'device_id': self.id}):
            for fixed_ip in port.fixed_ips:
                subnets.append(self._provider.networking.subnets.get(
                    fixed_ip.get('subnet_id')))
        return cast("list[Subnet]", subnets)

    def attach_gateway(self, gateway: Gateway) -> None:
        cast("OpenStackCloudProvider", self._provider).os_conn.update_router(
            self.id, ext_gateway_net_id=gateway.id)

    def detach_gateway(self, gateway: Gateway) -> None:
        # TODO: OpenStack SDK Connection object doesn't appear to have a method
        # for detaching/clearing the external gateway.
        cast("OpenStackCloudProvider", self._provider).neutron \
            .remove_gateway_router(self.id)


class OpenStackInternetGateway(BaseInternetGateway):

    GATEWAY_STATE_MAP = {
        NetworkState.AVAILABLE: GatewayState.AVAILABLE,
        NetworkState.DOWN: GatewayState.ERROR,
        NetworkState.ERROR: GatewayState.ERROR,
        NetworkState.PENDING: GatewayState.CONFIGURING,
        NetworkState.UNKNOWN: GatewayState.UNKNOWN
    }

    def __init__(self, provider: OpenStackCloudProvider,
                 gateway_net: Any) -> None:
        super(OpenStackInternetGateway, self).__init__(provider)
        if isinstance(gateway_net, OpenStackNetwork):
            # pylint:disable=protected-access
            gateway_net = gateway_net._network
        self._gateway_net = gateway_net
        self._fips_container = OpenStackFloatingIPSubService(provider, self)

    @property
    def id(self) -> str:
        return self._gateway_net.get('id', None)

    @property
    def name(self) -> str:
        return self._gateway_net.get('name', None)

    @property
    def network_id(self) -> str:
        return self._gateway_net.get('id')

    def refresh(self) -> None:
        """Refresh the state of this network by re-querying the provider."""
        network = self._provider.networking.networks.get(self.id)
        if network:
            # pylint:disable=protected-access
            self._gateway_net = cast(Any, network)._network
        else:
            # subnet no longer exists
            self._gateway_net.state = NetworkState.UNKNOWN

    @property
    def state(self) -> str:
        return self.GATEWAY_STATE_MAP.get(
            self._gateway_net.state, GatewayState.UNKNOWN)

    @property
    def floating_ips(self) -> OpenStackFloatingIPSubService:
        return self._fips_container


class OpenStackKeyPair(BaseKeyPair):

    def __init__(self, provider: OpenStackCloudProvider,
                 key_pair: Any) -> None:
        super(OpenStackKeyPair, self).__init__(provider, key_pair)


class OpenStackVMFirewall(BaseVMFirewall):
    _network_id_tag = "CB-auto-associated-network-id: "

    def __init__(self, provider: OpenStackCloudProvider,
                 vm_firewall: Any) -> None:
        super(OpenStackVMFirewall, self).__init__(provider, vm_firewall)
        self._rule_svc = OpenStackVMFirewallRuleSubService(provider, self)

    @property
    def network_id(self) -> str | None:
        """
        OpenStack does not associate a fw with a network so extract from desc.

        :return: The network ID supplied when this firewall was created or
                 `None` if ID cannot be identified.
        """
        # Extracting networking ID from description
        exp = ".*\\[" + self._network_id_tag + "([^\\]]*)\\].*"
        matches = re.match(exp, self._description)
        if matches:
            return matches.group(1)
        # We generally simulate a network being associated with a firewall;
        # however, because of some networking specificity in Nectar, we must
        # allow `None` return value as well in case an ID was not discovered.
        else:
            return None

    @property
    def _description(self) -> str:
        return self._vm_firewall.description or ""

    @property
    def description(self) -> str | None:
        desc_fragment = " [{}{}]".format(self._network_id_tag,
                                         self.network_id)
        desc = self._description
        if desc:
            return desc.replace(desc_fragment, "")
        else:
            return None

    @description.setter
    def description(self, value: str) -> None:
        if not value:
            value = ""
        value += " [{}{}]".format(self._network_id_tag,
                                  self.network_id)
        cast("OpenStackCloudProvider", self._provider).os_conn.network \
            .update_security_group(self.id, description=value)
        self.refresh()

    @property
    def name(self) -> str:
        """
        Return the name of this VM firewall.
        """
        return self.id

    @property
    def label(self) -> str | None:
        return self._vm_firewall.name

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        self.assert_valid_resource_label(value)
        cast("OpenStackCloudProvider", self._provider).os_conn.network \
            .update_security_group(self.id, name=value or "")
        self.refresh()

    @property
    def rules(self) -> OpenStackVMFirewallRuleSubService:
        return self._rule_svc

    def refresh(self) -> None:
        self._vm_firewall = cast(
            "OpenStackCloudProvider", self._provider).os_conn.network \
            .get_security_group(self.id)

    def to_json(self) -> dict[str, Any]:
        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = json_rules
        return js


class OpenStackVMFirewallRule(BaseVMFirewallRule):

    def __init__(self, parent_fw: VMFirewall, rule: Any) -> None:
        super(OpenStackVMFirewallRule, self).__init__(parent_fw, rule)

    @property
    def id(self) -> str:
        return self._rule.get('id')

    @property
    def direction(self) -> TrafficDirection:
        direction = self._rule.get('direction')
        if direction == 'ingress':
            return TrafficDirection.INBOUND
        elif direction == 'egress':
            return TrafficDirection.OUTBOUND
        raise ProviderInternalException(
            "Unknown firewall rule direction: {0}".format(direction))

    @property
    def protocol(self) -> str:
        return self._rule.get('protocol')

    @property
    def from_port(self) -> int:
        return self._rule.get('port_range_min')

    @property
    def to_port(self) -> int:
        return self._rule.get('port_range_max')

    @property
    def cidr(self) -> str | None:
        return self._rule.get('remote_ip_prefix')

    @property
    def src_dest_fw_id(self) -> str | None:
        fw = self.src_dest_fw
        if fw:
            return fw.id
        return None

    @property
    def src_dest_fw(self) -> VMFirewall | None:
        fw_id = self._rule.get('remote_group_id')
        if fw_id:
            return self._provider.security.vm_firewalls.get(fw_id)
        return None


class OpenStackBucketObject(BaseBucketObject):

    def __init__(self, provider: OpenStackCloudProvider,
                 cbcontainer: Any, obj: Any) -> None:
        super(OpenStackBucketObject, self).__init__(provider)
        self.cbcontainer = cbcontainer
        self._obj = obj

    @property
    def id(self) -> str:
        return self._obj.get("name")

    @property
    def name(self) -> str:
        """Get this object's name."""
        return self.id

    @property
    def size(self) -> int:
        return self._obj.get("bytes")

    @property
    def last_modified(self) -> str:
        return self._obj.get("last_modified")

    def iter_content(self) -> Iterable[bytes]:
        """Returns this object's content as an iterable."""
        _, content = cast("OpenStackCloudProvider", self._provider).swift \
            .get_object(self.cbcontainer.name, self.name, resp_chunk_size=65536)
        return content

    @property
    def bucket(self) -> Bucket:
        return self.cbcontainer

    def _upload_single_shot(
            self, data: str | bytes | IO[bytes]) -> BucketObject:
        """
        Set the contents of this object in a single request.

        Inputs larger than the multipart threshold are handled transparently
        by the base class via the Static Large Object (SLO) multipart path, so
        this single-request path only runs for smaller payloads.
        """
        cast("OpenStackCloudProvider", self._provider).swift.put_object(
            self.cbcontainer.name, self.name, data)
        return self

    def upload_from_file(self, path: str,
                         config: UploadConfig | None = None) -> BucketObject:
        """
        Stores the contents of the file pointed by the ``path`` variable.
        If the file is bigger than 5 Gig, it will be broken into segments.

        Swift uses ``SwiftService`` here, which manages its own segmenting and
        concurrency; the ``config`` argument is accepted for interface
        consistency but does not affect this path.

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
        upload_options: dict[str, Any] = {}
        if 'segment_size' not in upload_options:
            if os.path.getsize(path) >= FIVE_GIG:
                upload_options['segment_size'] = FIVE_GIG

        # remap the swift service's connection factory method
        # pylint:disable=protected-access
        swiftclient.service.get_conn = cast(
            "OpenStackCloudProvider", self._provider)._connect_swift

        with SwiftService() as swift:
            upload_object = SwiftUploadObject(path, object_name=self.name)
            for up_res in swift.upload(self.cbcontainer.name,
                                       [upload_object, ],
                                       options=upload_options):
                up_res['success']
        return self

    def delete(self) -> None:
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
        swiftclient.service.get_conn = cast(
            "OpenStackCloudProvider", self._provider)._connect_swift

        with SwiftService() as swift:
            for del_res in swift.delete(self.cbcontainer.name, [self.name, ]):
                del_res['success']

    def generate_url(self, expires_in: int, writable: bool = False) -> str:
        http_method = "PUT" if writable else "GET"
        # Set a temp url key on the object (http://bit.ly/2NBiXGD)
        temp_url_key = "cloudbridge-tmp-url-key"
        swift = cast("OpenStackCloudProvider", self._provider).swift
        swift.post_account(
            headers={"x-account-meta-temp-url-key": temp_url_key})
        base_url = urlparse(swift.get_service_auth()[0])
        access_point = "{0}://{1}".format(base_url.scheme, base_url.netloc)
        url_path = "/".join([base_url.path, self.cbcontainer.name, self.name])
        return urljoin(access_point, generate_temp_url(url_path, expires_in,
                                                       temp_url_key, http_method))

    def refresh(self) -> None:
        self._obj = self.cbcontainer.objects.get(self.id)._obj


class OpenStackBucket(BaseBucket):

    def __init__(self, provider: OpenStackCloudProvider,
                 bucket: Any) -> None:
        super(OpenStackBucket, self).__init__(provider)
        self._bucket = bucket
        self._object_container = OpenStackBucketObjectSubService(provider,
                                                                 self)

    @property
    def id(self) -> str:
        return self._bucket.get("name")

    @property
    def name(self) -> str:
        return self.id

    @property
    def objects(self) -> OpenStackBucketObjectSubService:
        return self._object_container


class OpenStackDnsZone(BaseDnsZone):

    def __init__(self, provider: OpenStackCloudProvider,
                 dns_zone: Any) -> None:
        super(OpenStackDnsZone, self).__init__(provider)
        self._dns_zone = dns_zone
        self._dns_record_container = OpenStackDnsRecordSubService(
            provider, self)

    @property
    def id(self) -> str:
        return self._dns_zone.id

    @property
    def name(self) -> str:
        return self._dns_zone.name

    @property
    def admin_email(self) -> str | None:
        return self._dns_zone.email

    @property
    def records(self) -> OpenStackDnsRecordSubService:
        return self._dns_record_container


class OpenStackDnsRecord(BaseDnsRecord):

    def __init__(self, provider: OpenStackCloudProvider, dns_zone: Any,
                 dns_record: Any) -> None:
        super(OpenStackDnsRecord, self).__init__(provider)
        self._dns_zone = dns_zone
        self._dns_rec = dns_record

    @property
    def id(self) -> str:
        return self._dns_rec.id

    @property
    def name(self) -> str:
        return self._dns_rec.name

    @property
    def zone_id(self) -> str:
        return self._dns_zone.id

    @property
    def type(self) -> str:
        return self._dns_rec.type

    @property
    def data(self) -> list[str]:
        return self._dns_rec.records

    @property
    def ttl(self) -> int:
        return self._dns_rec.ttl

    def delete(self) -> None:
        # pylint:disable=protected-access
        records: Any = self._provider.dns._records
        records.delete(self._dns_zone, self)
