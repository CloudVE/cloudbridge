"""
DataTypes used by this provider
"""
import hashlib
import inspect
import io
import logging
import math
import re
import uuid
from collections import namedtuple
from datetime import datetime

import googleapiclient

from cloudbridge.base.resources import BaseAttachmentInfo
from cloudbridge.base.resources import BaseBucket
from cloudbridge.base.resources import BaseBucketObject
from cloudbridge.base.resources import BaseDnsRecord
from cloudbridge.base.resources import BaseDnsZone
from cloudbridge.base.resources import BaseFloatingIP
from cloudbridge.base.resources import BaseInstance
from cloudbridge.base.resources import BaseInternetGateway
from cloudbridge.base.resources import BaseKeyPair
from cloudbridge.base.resources import BaseLaunchConfig
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
from cloudbridge.interfaces.resources import GatewayState
from cloudbridge.interfaces.resources import InstanceState
from cloudbridge.interfaces.resources import MachineImageState
from cloudbridge.interfaces.resources import NetworkState
from cloudbridge.interfaces.resources import RouterState
from cloudbridge.interfaces.resources import SnapshotState
from cloudbridge.interfaces.resources import SubnetState
from cloudbridge.interfaces.resources import TrafficDirection
from cloudbridge.interfaces.resources import VolumeState

from . import helpers
from .subservices import GCPBucketObjectSubService
from .subservices import GCPDnsRecordSubService
from .subservices import GCPFloatingIPSubService
from .subservices import GCPGatewaySubService
from .subservices import GCPSubnetSubService
from .subservices import GCPVMFirewallRuleSubService

# Older versions of Python do not have a built-in set data-structure.

try:
    set
except NameError:
    from sets import Set as set

log = logging.getLogger(__name__)


class GCPKeyPair(BaseKeyPair):

    KP_TAG_PREFIX = "cb_key_pair_"
    KP_TAG_REGEX = re.compile("^" + KP_TAG_PREFIX + ".*")
    GCPKeyInfo = namedtuple('GCPKeyInfo', ['name', 'public_key'])

    def __init__(self, provider, kp_info, private_key=None):
        super(GCPKeyPair, self).__init__(provider, None)
        self._key_pair = kp_info
        self._private_key = private_key

    @property
    def id(self):
        return self._key_pair.name

    @property
    def name(self):
        return self._key_pair.name

    def delete(self):
        self._provider.security.key_pairs.delete(self.id)

    @property
    def material(self):
        return self._private_key


class GCPVMType(BaseVMType):
    def __init__(self, provider, instance_dict):
        super(GCPVMType, self).__init__(provider)
        self._inst_dict = instance_dict

    @property
    def resource_url(self):
        return self._inst_dict.get('selfLink')

    @property
    def id(self):
        return self._inst_dict.get('selfLink')

    @property
    def name(self):
        return self._inst_dict.get('name')

    @property
    def family(self):
        return self._inst_dict.get('kind')

    @property
    def vcpus(self):
        return self._inst_dict.get('guestCpus')

    @property
    def ram(self):
        return float("{0:.2f}".format(self._inst_dict.get('memoryMb') / 1024))

    @property
    def size_root_disk(self):
        return 0

    @property
    def size_ephemeral_disks(self):
        return int(self._inst_dict.get('maximumPersistentDisksSizeGb'))

    @property
    def num_ephemeral_disks(self):
        return self._inst_dict.get('maximumPersistentDisks')

    @property
    def extra_data(self):
        return {key: val for key, val in self._inst_dict.items()
                if key not in ['id', 'name', 'kind', 'guestCpus', 'memoryMb',
                               'maximumPersistentDisksSizeGb',
                               'maximumPersistentDisks']}


class GCPPlacementZone(BasePlacementZone):

    def __init__(self, provider, zone):
        super(GCPPlacementZone, self).__init__(provider)
        self._zone = zone

    @property
    def id(self):
        """
        Get the zone id
        :rtype: ``str``
        :return: ID for this zone as returned by the cloud middleware.
        """
        return self._zone['selfLink']

    @property
    def name(self):
        """
        Get the zone name.
        :rtype: ``str``
        :return: Name for this zone as returned by the cloud middleware.
        """
        return self._zone['name']

    @property
    def region_name(self):
        """
        Get the region that this zone belongs to.
        :rtype: ``str``
        :return: Name of this zone's region as returned by the cloud middleware
        """
        parsed_region_url = self._provider.parse_url(self._zone['region'])
        return parsed_region_url.parameters['region']


class GCPRegion(BaseRegion):

    def __init__(self, provider, gcp_region):
        super(GCPRegion, self).__init__(provider)
        self._gcp_region = gcp_region

    @property
    def id(self):
        return self._gcp_region.get('selfLink')

    @property
    def name(self):
        return self._gcp_region.get('name')

    @property
    def zones(self):
        """
        Accesss information about placement zones within this region.
        """
        zones_response = (self._provider
                              .gcp_compute
                              .zones()
                              .list(project=self._provider.project_name)
                              .execute())
        zones = [zone for zone in zones_response['items']
                 if zone['region'] == self._gcp_region['selfLink']]
        return [GCPPlacementZone(self._provider, zone) for zone in zones]


class GCPFirewallsDelegate(object):
    _NETWORK_URL_PREFIX = 'global/networks/'

    def __init__(self, provider):
        self._provider = provider
        self._list_response = None

    @staticmethod
    def tag_network_id(tag, network_name):
        """
        Generate an ID for a (tag, network name) pair.
        """
        md5 = hashlib.md5()
        md5.update("{0}-{1}".format(tag, network_name).encode('ascii'))
        return md5.hexdigest()

    @property
    def provider(self):
        return self._provider

    @property
    def tag_networks(self):
        """
        List all (tag, network name) pairs that are in at least one firewall.
        """
        out = set()
        for firewall in self.iter_firewalls():
            network_name = self.network_name(firewall)
            if network_name is not None:
                out.add((firewall['targetTags'][0], network_name))
        return out

    def network_name(self, firewall):
        """
        Extract the network name of a firewall.
        """
        if 'network' not in firewall:
            return GCPNetwork.CB_DEFAULT_NETWORK_LABEL
        url = self._provider.parse_url(firewall['network'])
        return url.parameters['network']

    def get_tag_network_from_id(self, tag_network_id):
        """
        Map an ID back to the (tag, network name) pair.
        """
        for tag, network_name in self.tag_networks:
            current_id = GCPFirewallsDelegate.tag_network_id(tag, network_name)
            if current_id == tag_network_id:
                return (tag, network_name)
        return (None, None)

    def delete_tag_network_with_id(self, tag_network_id):
        """
        Delete all firewalls in a given network with a specific target tag.
        """
        tag, network_name = self.get_tag_network_from_id(tag_network_id)
        if tag is None:
            return
        for firewall in self.iter_firewalls(tag, network_name):
            self._delete_firewall(firewall)
        self._update_list_response()

    def add_firewall(self, tag, direction, protocol, priority, port,
                     src_dest_range, src_dest_tag, description, network_name):
        """
        Create a new firewall.
        """
        if self.find_firewall(
                tag, direction, protocol, port, src_dest_range, src_dest_tag,
                network_name) is not None:
            return True
        # Do not let the user accidentally open traffic from the world by not
        # explicitly specifying the source.
        if src_dest_tag is None and src_dest_range is None:
            return False
        firewall = {
            'name': 'firewall-{0}'.format(uuid.uuid4()),
            'network': GCPFirewallsDelegate._NETWORK_URL_PREFIX + network_name,
            'allowed': [{'IPProtocol': str(protocol)}],
            'targetTags': [tag]}
        if description is not None:
            firewall['description'] = description
        if port is not None:
            firewall['allowed'][0]['ports'] = [port]
        if direction == TrafficDirection.INBOUND:
            firewall['direction'] = 'INGRESS'
            src_dest_str = 'source'
        else:
            firewall['direction'] = 'EGRESS'
            src_dest_str = 'destination'
        if src_dest_range is not None:
            firewall[src_dest_str + 'Ranges'] = [src_dest_range]
        if src_dest_tag is not None:
            if direction == TrafficDirection.OUTBOUND:
                log.warning('GCP does not support egress rules to network '
                            'tags. Only IP ranges are acceptable.')
            else:
                firewall['sourceTags'] = [src_dest_tag]
        if priority is not None:
            firewall['priority'] = priority
        project_name = self._provider.project_name
        try:
            response = (self._provider
                            .gcp_compute
                            .firewalls()
                            .insert(project=project_name,
                                    body=firewall)
                            .execute())
            self._provider.wait_for_operation(response)
            # TODO: process the response and handle errors.
        finally:
            self._update_list_response()
        return True

    def find_firewall(self, tag, direction, protocol, port, src_dest_range,
                      src_dest_tag, network_name):
        """
        Find a firewall with give parameters.
        """
        if src_dest_range is None and src_dest_tag is None:
            src_dest_range = '0.0.0.0/0'
        if direction == TrafficDirection.INBOUND:
            src_dest_str = 'source'
        else:
            src_dest_str = 'destination'
        for firewall in self.iter_firewalls(tag, network_name):
            if firewall['allowed'][0]['IPProtocol'] != protocol:
                continue
            if not self._check_list_in_dict(firewall['allowed'][0], 'ports',
                                            port):
                continue
            if not self._check_list_in_dict(firewall, src_dest_str + 'Ranges',
                                            src_dest_range):
                continue
            if not self._check_list_in_dict(firewall, src_dest_str + 'Tags',
                                            src_dest_tag):
                continue
            return firewall['id']
        return None

    def get_firewall_info(self, firewall_id):
        """
        Extract firewall properties to into a dictionary for easy of use.
        """
        info = {}
        for firewall in self.iter_firewalls():
            if firewall['id'] != firewall_id:
                continue
            if ('sourceRanges' in firewall and
                    len(firewall['sourceRanges']) == 1):
                info['src_dest_range'] = firewall['sourceRanges'][0]
            elif ('destinationRanges' in firewall and
                    len(firewall['destinationRanges']) == 1):
                info['src_dest_range'] = firewall['destinationRanges'][0]
            if 'sourceTags' in firewall and len(firewall['sourceTags']) == 1:
                info['src_dest_tag'] = firewall['sourceTags'][0]
            if 'targetTags' in firewall and len(firewall['targetTags']) == 1:
                info['target_tag'] = firewall['targetTags'][0]
            if 'IPProtocol' in firewall['allowed'][0]:
                info['protocol'] = firewall['allowed'][0]['IPProtocol']
            if ('ports' in firewall['allowed'][0] and
                    len(firewall['allowed'][0]['ports']) == 1):
                info['port'] = firewall['allowed'][0]['ports'][0]
            info['network_name'] = self.network_name(firewall)
            if 'direction' in firewall:
                info['direction'] = firewall['direction']
            if 'priority' in firewall:
                info['priority'] = firewall['priority']
            return info
        return info

    def delete_firewall_id(self, firewall_id):
        """
        Delete a firewall with a given ID.
        """
        for firewall in self.iter_firewalls():
            if firewall['id'] == firewall_id:
                self._delete_firewall(firewall)
        self._update_list_response()

    def iter_firewalls(self, tag=None, network_name=None):
        """
        Iterate through all firewalls. Can optionally iterate through firewalls
        with a given tag and/or in a network.
        """
        if self._list_response is None:
            self._update_list_response()
        for firewall in self._list_response:
            if ('targetTags' not in firewall or
                    len(firewall['targetTags']) != 1):
                continue
            if 'allowed' not in firewall or len(firewall['allowed']) != 1:
                continue
            if tag is not None and firewall['targetTags'][0] != tag:
                continue
            if network_name is None:
                yield firewall
                continue
            firewall_network_name = self.network_name(firewall)
            if firewall_network_name == network_name:
                yield firewall

    def _delete_firewall(self, firewall):
        """
        Delete a given firewall.
        """
        project_name = self._provider.project_name
        name = firewall['name']
        response = (self._provider
                        .gcp_compute
                        .firewalls()
                        .delete(project=project_name,
                                firewall=name)
                        .execute())
        self._provider.wait_for_operation(response)
        # TODO: process the response and handle errors.
        tag_name = "_".join(["firewall", name, "label"])
        if not helpers.remove_metadata_item(self._provider, tag_name):
            log.warning('No label was found associated with this firewall '
                        '"{}" when deleted.'.format(name))
        return True

    def _update_list_response(self):
        """
        Sync the local cache of all firewalls with the server.
        """
        self._list_response = list(
                helpers.iter_all(self._provider.gcp_compute.firewalls(),
                                 project=self._provider.project_name))

    def _check_list_in_dict(self, dictionary, field_name, value):
        """
        Verify that a given field in a dictionary is a singlton list [value].
        """
        if field_name not in dictionary:
            return value is None
        if (value is None or len(dictionary[field_name]) != 1 or
                dictionary[field_name][0] != value):
            return False
        return True


class GCPVMFirewall(BaseVMFirewall):

    def __init__(self, delegate, tag, network=None, description=None):
        super(GCPVMFirewall, self).__init__(delegate.provider, tag)
        self._delegate = delegate
        self._description = description
        if network is None:
            self._network = (delegate.provider.networking.networks
                             .get_or_create_default())
        else:
            self._network = network
        self._rule_container = GCPVMFirewallRuleSubService(self._provider,
                                                           self)

    @property
    def id(self):
        """
        Return the ID of this VM firewall which is determined based on the
        network and the target tag corresponding to this VM firewall.
        """
        return GCPFirewallsDelegate.tag_network_id(self._vm_firewall,
                                                   self._network.name)

    @property
    def name(self):
        """
        Return the name of the VM firewall which is the same as the
        corresponding tag name.
        """
        return self._vm_firewall

    @property
    def label(self):
        tag_name = "_".join(["firewall", self.name, "label"])
        return helpers.get_metadata_item_value(self._provider, tag_name)

    @label.setter
    def label(self, value):
        self.assert_valid_resource_label(value)
        tag_name = "_".join(["firewall", self.name, "label"])
        helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

    @property
    def description(self):
        """
        The description of the VM firewall is even explicitly given when the
        VM firewall is created or is determined from a VM firewall rule, i.e. a
        GCP firewall, in the VM firewall.

        If the GCP firewalls are created using this API, they all have the same
        description.
        """
        if self._description is None:
            for firewall in self._delegate.iter_firewalls(self._vm_firewall,
                                                          self._network.name):
                if 'description' in firewall:
                    self._description = firewall['description']
        if self._description is None:
            self._description = ''
        return self._description

    @description.setter
    def description(self, value):
        # Change the description on all rules
        for fw in self._delegate.iter_firewalls(self._vm_firewall,
                                                self._network.name):
            fw['description'] = value or ''
            response = (self._provider
                        .gcp_compute
                        .firewalls()
                        .update(project=self._provider.project_name,
                                firewall=fw['name'],
                                body=fw)
                        .execute())
            self._provider.wait_for_operation(response)
        # Set back to None so that the next time the user gets it, it updates
        # but don't force update here to avoid more overhead
        self._description = None

    @property
    def network_id(self):
        return self._network.id

    @property
    def rules(self):
        return self._rule_container

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = json_rules
        return js

    def refresh(self):
        fw = self._provider.security.vm_firewalls.get(self.id)
        # restore all internal state
        if fw:
            # pylint:disable=protected-access
            self._delegate = fw._delegate
            # pylint:disable=protected-access
            self._description = fw._description
            # pylint:disable=protected-access
            self._network = fw._network
            # pylint:disable=protected-access
            self._rule_container = fw._rule_container

    @property
    def network(self):
        return self._network

    @property
    def delegate(self):
        return self._delegate


class GCPVMFirewallRule(BaseVMFirewallRule):

    def __init__(self, parent_fw, rule):
        super(GCPVMFirewallRule, self).__init__(parent_fw, rule)

    @property
    def id(self):
        return self._rule

    @property
    def direction(self):
        info = self.firewall.delegate.get_firewall_info(self._rule)
        if info is None:
            return None
        if 'direction' in info and info['direction'] == 'EGRESS':
            return TrafficDirection.OUTBOUND
        return TrafficDirection.INBOUND

    @property
    def protocol(self):
        info = self.firewall.delegate.get_firewall_info(self._rule)
        if info is None or 'protocol' not in info:
            return None
        return info['protocol']

    @property
    def from_port(self):
        info = self.firewall.delegate.get_firewall_info(self._rule)
        if info is None or 'port' not in info:
            return 0
        port = info['port']
        if port.isdigit():
            return int(port)
        parts = port.split('-')
        if len(parts) > 2 or len(parts) < 1:
            return 0
        if parts[0].isdigit():
            return int(parts[0])
        return 0

    @property
    def to_port(self):
        info = self.firewall.delegate.get_firewall_info(self._rule)
        if info is None or 'port' not in info:
            return 0
        port = info['port']
        if port.isdigit():
            return int(port)
        parts = port.split('-')
        if len(parts) > 2 or len(parts) < 1:
            return 0
        if parts[-1].isdigit():
            return int(parts[-1])
        return 0

    @property
    def cidr(self):
        info = self.firewall.delegate.get_firewall_info(self._rule)
        if info is None or 'src_dest_range' not in info:
            return None
        return info['src_dest_range']

    @property
    def src_dest_fw_id(self):
        """
        Return the VM firewall given access by this rule.
        """
        info = self.firewall.delegate.get_firewall_info(self._rule)
        if info is None or 'src_dest_tag' not in info:
            return None
        return GCPFirewallsDelegate.tag_network_id(info['src_dest_tag'],
                                                   self.firewall.network.name)

    @property
    def src_dest_fw(self):
        """
        Return the VM firewall given access by this rule.
        """
        info = self.firewall.delegate.get_firewall_info(self._rule)
        if info is None or 'src_dest_tag' not in info:
            return None
        return GCPVMFirewall(
                self.firewall.delegate, info['src_dest_tag'],
                self.firewall.network)

    @property
    def priority(self):
        info = self.firewall.delegate.get_firewall_info(self._rule)
        # The default firewall rule priority, when not specified, is 1000.
        if info is None or 'priority' not in info:
            return 1000
        return info['priority']

    def is_dummy_rule(self):
        if self.priority != 65534:
            return False
        if self.direction != TrafficDirection.OUTBOUND:
            return False
        if self.protocol != 'tcp':
            return False
        if self.cidr != '0.0.0.0/0':
            return False
        return True


class GCPMachineImage(BaseMachineImage):

    IMAGE_STATE_MAP = {
        'PENDING': MachineImageState.PENDING,
        'READY': MachineImageState.AVAILABLE,
        'FAILED': MachineImageState.ERROR
    }

    def __init__(self, provider, image):
        super(GCPMachineImage, self).__init__(provider)
        if isinstance(image, GCPMachineImage):
            # pylint:disable=protected-access
            self._gcp_image = image._gcp_image
        else:
            self._gcp_image = image

    @property
    def resource_url(self):
        return self._gcp_image.get('selfLink')

    @property
    def id(self):
        """
        Get the image identifier.
        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        return self._gcp_image.get('selfLink')

    @property
    def name(self):
        """
        Get the image name.
        :rtype: ``str``
        :return: Name for this image as returned by the cloud middleware.
        """
        return self._gcp_image['name']

    @property
    def label(self):
        labels = self._gcp_image.get('labels')
        return labels.get('cblabel', '') if labels else ''

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        req = (self._provider
                   .gcp_compute
                   .images()
                   .setLabels(project=self._provider.project_name,
                              resource=self.name,
                              body={}))

        helpers.change_label(self, 'cblabel', value, '_gcp_image', req)

    @property
    def description(self):
        """
        Get the image description.
        :rtype: ``str``
        :return: Description for this image as returned by the cloud middleware
        """
        return self._gcp_image.get('description', '')

    @property
    def min_disk(self):
        """
        Returns the minimum size of the disk that's required to
        boot this image (in GB)
        :rtype: ``int``
        :return: The minimum disk size needed by this image
        """
        return int(math.ceil(float(self._gcp_image.get('diskSizeGb'))))

    def delete(self):
        """
        Delete this image
        """
        (self._provider
             .gcp_compute
             .images()
             .delete(project=self._provider.project_name,
                     image=self.name)
             .execute())

    @property
    def state(self):
        return GCPMachineImage.IMAGE_STATE_MAP.get(
            self._gcp_image['status'], MachineImageState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        image = self._provider.compute.images.get(self.id)
        if image:
            # pylint:disable=protected-access
            self._gcp_image = image._gcp_image
        else:
            # image no longer exists
            self._gcp_image['status'] = MachineImageState.UNKNOWN


class GCPInstance(BaseInstance):
    # https://cloud.google.com/compute/docs/reference/latest/instances
    # The status of the instance. One of the following values:
    # PROVISIONING, STAGING, RUNNING, STOPPING, SUSPENDING, SUSPENDED,
    # and TERMINATED.
    INSTANCE_STATE_MAP = {
        'PROVISIONING': InstanceState.PENDING,
        'STAGING': InstanceState.PENDING,
        'RUNNING': InstanceState.RUNNING,
        'STOPPING': InstanceState.CONFIGURING,
        'TERMINATED': InstanceState.STOPPED,
        'SUSPENDING': InstanceState.CONFIGURING,
        'SUSPENDED': InstanceState.STOPPED
    }

    def __init__(self, provider, gcp_instance):
        super(GCPInstance, self).__init__(provider)
        self._gcp_instance = gcp_instance
        self._inet_gateway = None

    @property
    def resource_url(self):
        return self._gcp_instance.get('selfLink')

    @property
    def id(self):
        """
        Get the instance identifier.

        A GCP instance is uniquely identified by its selfLink, which is used
        as its id.
        """
        return self._gcp_instance.get('selfLink')

    @property
    def name(self):
        """
        Get the instance name.
        """
        return self._gcp_instance['name']

    @property
    def label(self):
        labels = self._gcp_instance.get('labels')
        return labels.get('cblabel', '') if labels else ''

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        req = (self._provider
                   .gcp_compute
                   .instances()
                   .setLabels(project=self._provider.project_name,
                              zone=self.zone_name,
                              instance=self.name,
                              body={}))

        helpers.change_label(self, 'cblabel', value, '_gcp_instance', req)

    @property
    def public_ips(self):
        """
        Get all the public IP addresses for this instance.
        """
        ips = []
        network_interfaces = self._gcp_instance.get('networkInterfaces')
        if network_interfaces is not None and len(network_interfaces) > 0:
            access_configs = network_interfaces[0].get('accessConfigs')
            if access_configs is not None and len(access_configs) > 0:
                # https://cloud.google.com/compute/docs/reference/beta/instances
                # An array of configurations for this interface. Currently,
                # only one access config, ONE_TO_ONE_NAT, is supported. If
                # there are no accessConfigs specified, then this instance will
                # have no external internet access.
                access_config = access_configs[0]
                if 'natIP' in access_config:
                    ips.append(access_config['natIP'])
        for ip in self.inet_gateway.floating_ips:
            if ip.in_use:
                if ip.private_ip in self.private_ips:
                    ips.append(ip.public_ip)
        return ips

    @property
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        network_interfaces = self._gcp_instance.get('networkInterfaces')
        if network_interfaces is None or len(network_interfaces) == 0:
            return []
        if 'networkIP' in network_interfaces[0]:
            return [network_interfaces[0]['networkIP']]
        else:
            return []

    @property
    def vm_type_id(self):
        """
        Get the instance type name.
        """
        return self._gcp_instance.get('machineType')

    @property
    def vm_type(self):
        """
        Get the instance type.
        """
        machine_type_uri = self._gcp_instance.get('machineType')
        if machine_type_uri is None:
            return None
        parsed_uri = self._provider.parse_url(machine_type_uri)
        return GCPVMType(self._provider, parsed_uri.get_resource())

    @property
    def create_time(self):
        """
        Get the instance creation time
        """
        return datetime.fromisoformat(self._gcp_instance.get("creationTimestamp"))

    @property
    def subnet_id(self):
        """
        Get the zone for this instance.
        """
        return (self._gcp_instance.get('networkInterfaces', [{}])[0]
                .get('subnetwork'))

    def reboot(self):
        """
        Reboot this instance.
        """
        if self.state == InstanceState.STOPPED:
            (self._provider
             .gcp_compute
             .instances()
             .start(project=self._provider.project_name,
                    zone=self.zone_name,
                    instance=self.name)
             .execute())
        else:
            (self._provider
             .gcp_compute
             .instances()
             .reset(project=self._provider.project_name,
                    zone=self.zone_name,
                    instance=self.name)
             .execute())

    def stop(self):
        """
        Stop this instance.
        """
        (self._provider
         .gcp_compute
         .instances()
         .stop(project=self._provider.project_name,
               zone=self.zone_name,
               instance=self.name)
         .execute())

    @property
    def image_id(self):
        """
        Get the image ID for this insance.
        """
        if 'disks' not in self._gcp_instance:
            return None
        for disk in self._gcp_instance['disks']:
            if 'boot' in disk and disk['boot']:
                disk_url = self._provider.parse_url(disk['source'])
                return disk_url.get_resource().get('sourceImage')
        return None

    @property
    def zone_id(self):
        """
        Get the placement zone id where this instance is running.
        """
        return self._gcp_instance.get('zone')

    @property
    def zone_name(self):
        return self._provider.parse_url(self.zone_id).parameters['zone']

    @property
    def vm_firewalls(self):
        """
        Get the VM firewalls associated with this instance.
        """
        network_url = self._gcp_instance.get('networkInterfaces')[0].get(
            'network')
        url = self._provider.parse_url(network_url)
        network_name = url.parameters['network']
        if 'items' not in self._gcp_instance['tags']:
            return []
        tags = self._gcp_instance['tags']['items']
        # Tags are mapped to non-empty VM firewalls under the instance network.
        # Unmatched tags are ignored.
        sgs = (self._provider.security
               .vm_firewalls.find_by_network_and_tags(
                   network_name, tags))
        return sgs

    @property
    def vm_firewall_ids(self):
        """
        Get the VM firewall IDs associated with this instance.
        """
        sg_ids = []
        for sg in self.vm_firewalls:
            sg_ids.append(sg.id)
        return sg_ids

    @property
    def key_pair_id(self):
        """
        Get the id of the key pair associated with this instance.
        Assume there is only 1 key pair
        """
        # Get instance again to avoid stale metadata
        ins = self._provider.compute.instances.get(self.id)
        # pylint:disable=protected-access
        meta = ins._gcp_instance.get('metadata', {})
        if meta:
            items = meta.get("items", [])
            for item in items:
                if item.get("key") == "ssh-keys":
                    # The key pair name/id is stored last, after the public key
                    return item.get("value").split(" ")[-1]
        return None

    @property
    def inet_gateway(self):
        if self._inet_gateway:
            return self._inet_gateway
        network_url = self._gcp_instance.get('networkInterfaces')[0].get(
            'network')
        network = self._provider.networking.networks.get(network_url)
        self._inet_gateway = network.gateways.get_or_create()
        return self._inet_gateway

    def create_image(self, label):
        """
        Create a new image based on this instance.
        """
        self.assert_valid_resource_label(label)
        name = self._generate_name_from_label(label, 'cb-img')
        if 'disks' not in self._gcp_instance:
            log.error('Failed to create image: no disks found.')
            return
        for disk in self._gcp_instance['disks']:
            if 'boot' in disk and disk['boot']:
                image_body = {
                    'name': name,
                    'sourceDisk': disk['source'],
                    'labels': {'cblabel': label.replace(' ', '_').lower()},
                }
                operation = (self._provider
                             .gcp_compute
                             .images()
                             .insert(project=self._provider.project_name,
                                     body=image_body,
                                     forceCreate=True)
                             .execute())
                self._provider.wait_for_operation(operation)
                img = self._provider.get_resource('images', name)
                return GCPMachineImage(self._provider, img) if img else None
        log.error('Failed to create image: no boot disk found.')

    def _get_existing_target_instance(self):
        """
        Return the target instance corresponding to this instance.

        If there is no target instance for this instance, return None.
        """
        try:
            for target_instance in helpers.iter_all(
                    self._provider.gcp_compute.targetInstances(),
                    project=self._provider.project_name,
                    zone=self.zone_name):
                url = self._provider.parse_url(target_instance['instance'])
                if url.parameters['instance'] == self.name:
                    return target_instance
        except Exception as e:
            log.warning('Exception while listing target instances: %s', e)
        return None

    def _get_target_instance(self):
        """
        Return the target instance corresponding to this instance.

        If there is no target instance for this instance, create one.
        """
        existing_target_instance = self._get_existing_target_instance()
        if existing_target_instance:
            return existing_target_instance

        # No targetInstance exists for this instance. Create one.
        body = {'name': 'target-instance-{0}'.format(uuid.uuid4()),
                'instance': self._gcp_instance['selfLink']}
        try:
            response = (self._provider
                            .gcp_compute
                            .targetInstances()
                            .insert(project=self._provider.project_name,
                                    zone=self.zone_name,
                                    body=body)
                            .execute())
            self._provider.wait_for_operation(response, zone=self.zone_name)
        except Exception as e:
            log.warning('Exception while inserting a target instance: %s', e)
            return None

        # The following method should find the target instance that we
        # successfully created above.
        return self._get_existing_target_instance()

    def _redirect_existing_rule(self, ip, target_instance):
        """
        Redirect the forwarding rule of the given IP to the given Instance.
        """
        new_zone = (self._provider.parse_url(target_instance['zone'])
                                  .parameters['zone'])
        new_name = target_instance['name']
        new_url = target_instance['selfLink']
        try:
            for rule in helpers.iter_all(
                    self._provider.gcp_compute.forwardingRules(),
                    project=self._provider.project_name,
                    region=ip.region_name):
                if rule['IPAddress'] != ip.public_ip:
                    continue
                parsed_target_url = self._provider.parse_url(rule['target'])
                old_zone = parsed_target_url.parameters['zone']
                old_name = parsed_target_url.parameters['targetInstance']
                if old_zone == new_zone and old_name == new_name:
                    return True
                response = (self._provider
                                .gcp_compute
                                .forwardingRules()
                                .setTarget(
                                    project=self._provider.project_name,
                                    region=ip.region_name,
                                    forwardingRule=rule['name'],
                                    body={'target': new_url})
                                .execute())
                self._provider.wait_for_operation(response,
                                                  region=ip.region_name)
                return True
        except Exception as e:
            log.warning(
                'Exception while listing/changing forwarding rules: %s', e)
        return False

    def _forward(self, ip, target_instance):
        """
        Forward the traffic to a given IP to a given instance.

        If there is already a forwarding rule for the IP, it is redirected;
        otherwise, a new forwarding rule is created.
        """
        if self._redirect_existing_rule(ip, target_instance):
            return True
        body = {'name': 'forwarding-rule-{0}'.format(uuid.uuid4()),
                'IPAddress': ip.public_ip,
                'target': target_instance['selfLink']}
        try:
            response = (self._provider
                            .gcp_compute
                            .forwardingRules()
                            .insert(project=self._provider.project_name,
                                    region=ip.region_name,
                                    body=body)
                            .execute())
            self._provider.wait_for_operation(response, region=ip.region_name)
        except Exception as e:
            log.warning('Exception while inserting a forwarding rule: %s', e)
            return False
        return True

    def _delete_existing_rule(self, ip, target_instance):
        """
        Stop forwarding traffic to an instance by deleting the forwarding rule.
        """
        zone = (self._provider.parse_url(target_instance['zone'])
                              .parameters['zone'])
        name = target_instance['name']
        try:
            for rule in helpers.iter_all(
                    self._provider.gcp_compute.forwardingRules(),
                    project=self._provider.project_name,
                    region=ip.region_name):
                if rule['IPAddress'] != ip.public_ip:
                    continue
                parsed_target_url = self._provider.parse_url(rule['target'])
                temp_zone = parsed_target_url.parameters['zone']
                temp_name = parsed_target_url.parameters['targetInstance']
                if temp_zone != zone or temp_name != name:
                    log.warning(
                            '"%s" is forwarded to "%s" in zone "%s"',
                            ip.public_ip, temp_name, temp_zone)
                    return False
                response = (self._provider
                                .gcp_compute
                                .forwardingRules()
                                .delete(
                                    project=self._provider.project_name,
                                    region=ip.region_name,
                                    forwardingRule=rule['name'])
                                .execute())
                self._provider.wait_for_operation(response,
                                                  region=ip.region_name)
                return True
        except Exception as e:
            log.warning(
                'Exception while listing/deleting forwarding rules: %s', e)
            return False
        return True

    def add_floating_ip(self, floating_ip):
        """
        Add an elastic IP address to this instance.
        """
        fip = (floating_ip if isinstance(floating_ip, GCPFloatingIP)
               else self.inet_gateway.floating_ips.get(floating_ip))
        if fip.in_use:
            if fip.private_ip not in self.private_ips:
                log.warning('Floating IP "%s" is not associated to "%s"',
                            fip.public_ip, self.name)
            return
        target_instance = self._get_target_instance()
        if not target_instance:
            log.warning('Could not create a targetInstance for "%s"',
                        self.name)
            return
        if not self._forward(fip, target_instance):
            log.warning('Could not forward "%s" to "%s"',
                        fip.public_ip, target_instance['selfLink'])

    def remove_floating_ip(self, floating_ip):
        """
        Remove a elastic IP address from this instance.
        """
        fip = (floating_ip if isinstance(floating_ip, GCPFloatingIP)
               else self.inet_gateway.floating_ips.get(floating_ip))
        if not fip.in_use or fip.private_ip not in self.private_ips:
            log.warning('Floating IP "%s" is not associated to "%s"',
                        fip.public_ip, self.name)
            return
        target_instance = self._get_target_instance()
        if not target_instance:
            # We should not be here.
            log.warning('Something went wrong! "%s" is associated to "%s" '
                        'with no target instance', fip.public_ip, self.name)
            return
        if not self._delete_existing_rule(fip, target_instance):
            log.warning(
                'Could not remove floating IP "%s" from instance "%s"',
                fip.public_ip, self.name)

    @property
    def state(self):
        return GCPInstance.INSTANCE_STATE_MAP.get(
            self._gcp_instance['status'], InstanceState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        inst = self._provider.compute.instances.get(self.id)
        if inst:
            # pylint:disable=protected-access
            self._gcp_instance = inst._gcp_instance
        else:
            # instance no longer exists
            self._gcp_instance['status'] = InstanceState.UNKNOWN

    def add_vm_firewall(self, sg):
        tag = sg.name if isinstance(sg, GCPVMFirewall) else sg
        tags = self._gcp_instance.get('tags', {}).get('items', [])
        tags.append(tag)
        self._set_tags(tags)

    def remove_vm_firewall(self, sg):
        tag = sg.name if isinstance(sg, GCPVMFirewall) else sg
        tags = self._gcp_instance.get('tags', {}).get('items', [])
        if tag in tags:
            tags.remove(tag)
            self._set_tags(tags)

    def _set_tags(self, tags):
        # Refresh to make sure we are using the most recent tags fingerprint.
        self.refresh()
        fingerprint = self._gcp_instance.get('tags', {}).get('fingerprint', '')
        response = (self._provider
                        .gcp_compute
                        .instances()
                        .setTags(project=self._provider.project_name,
                                 zone=self.zone_name,
                                 instance=self.name,
                                 body={'items': tags,
                                       'fingerprint': fingerprint})
                        .execute())
        self._provider.wait_for_operation(response, zone=self.zone_name)


class GCPNetwork(BaseNetwork):

    def __init__(self, provider, network):
        super(GCPNetwork, self).__init__(provider)
        self._network = network
        self._gateway_container = GCPGatewaySubService(provider, self)
        self._subnet_svc = GCPSubnetSubService(provider, self)

    @property
    def resource_url(self):
        return self._network['selfLink']

    @property
    def id(self):
        return self._network['selfLink']

    @property
    def name(self):
        return self._network['name']

    @property
    def label(self):
        tag_name = "_".join(["network", self.name, "label"])
        return helpers.get_metadata_item_value(self._provider, tag_name)

    @label.setter
    def label(self, value):
        self.assert_valid_resource_label(value)
        tag_name = "_".join(["network", self.name, "label"])
        helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

    @property
    def external(self):
        """
        All GCP networks can be connected to the Internet.
        """
        return True

    @property
    def state(self):
        """
        When a GCP network created by the CloudBridge API, we wait until the
        network is ready.
        """
        if self._network.get('status') == NetworkState.UNKNOWN:
            return NetworkState.UNKNOWN
        return NetworkState.AVAILABLE

    @property
    def cidr_block(self):
        if 'IPv4Range' in self._network:
            # This is a legacy network.
            return self._network['IPv4Range']
        return GCPNetwork.CB_DEFAULT_IPV4RANGE

    @property
    def subnets(self):
        return self._subnet_svc

    def refresh(self):
        net = self._provider.networking.networks.get(self.id)
        if net:
            # pylint:disable=protected-access
            self._network = net._network
        else:
            # network no longer exists
            self._network['status'] = NetworkState.UNKNOWN

    @property
    def gateways(self):
        return self._gateway_container


class GCPFloatingIP(BaseFloatingIP):
    _DEAD_INSTANCE = 'dead instance'

    def __init__(self, provider, floating_ip):
        super(GCPFloatingIP, self).__init__(provider)
        self._ip = floating_ip
        self._process_ip_users()

    @property
    def id(self):
        return self._ip['selfLink']

    @property
    def region_name(self):
        # We use regional IPs to simulate floating IPs not global IPs because
        # global IPs can be forwarded only to load balancing resources, not to
        # a specific instance. Find out the region to which the IP belongs.
        url = self._provider.parse_url(self._ip['region'])
        return url.parameters['region']

    @property
    def public_ip(self):
        return self._ip.get('address')

    @property
    def private_ip(self):
        if (not self._target_instance or
                self._target_instance == GCPFloatingIP._DEAD_INSTANCE):
            return None
        return self._target_instance['networkInterfaces'][0]['networkIP']

    @property
    def in_use(self):
        return True if self._target_instance else False

    def refresh(self):
        # pylint:disable=protected-access
        fip = self._provider.networking._floating_ips.get(None, self.id)
        # pylint:disable=protected-access
        self._ip = fip._ip
        self._process_ip_users()

    def _process_ip_users(self):
        self._rule = None
        self._target_instance = None

        if 'users' in self._ip and len(self._ip['users']) > 0:
            provider = self._provider
            if len(self._ip['users']) > 1:
                log.warning('Address "%s" in use by more than one resource',
                            self._ip.get('address'))
            resource_parsed_url = provider.parse_url(self._ip['users'][0])
            resource = resource_parsed_url.get_resource()
            if resource['kind'] == 'compute#forwardingRule':
                self._rule = resource
                target = provider.parse_url(resource['target']).get_resource()
                if target['kind'] == 'compute#targetInstance':
                    url = provider.parse_url(target['instance'])
                    try:
                        self._target_instance = url.get_resource()
                    except googleapiclient.errors.HttpError:
                        self._target_instance = GCPFloatingIP._DEAD_INSTANCE
                else:
                    log.warning('Address "%s" is forwarded to a %s',
                                self._ip.get('address'), target['kind'])
            else:
                log.warning('Address "%s" in use by a %s',
                            self._ip.get('address'), resource['kind'])


class GCPRouter(BaseRouter):

    def __init__(self, provider, router):
        super(GCPRouter, self).__init__(provider)
        self._router = router

    @property
    def id(self):
        return self._router['selfLink']

    @property
    def name(self):
        return self._router['name']

    @property
    def label(self):
        tag_name = "_".join(["router", self.name, "label"])
        return helpers.get_metadata_item_value(self._provider, tag_name)

    @label.setter
    def label(self, value):
        self.assert_valid_resource_label(value)
        tag_name = "_".join(["router", self.name, "label"])
        helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

    @property
    def region_name(self):
        parsed_url = self._provider.parse_url(self.id)
        return parsed_url.parameters['region']

    def refresh(self):
        router = self._provider.networking.routers.get(self.id)
        if router:
            # pylint:disable=protected-access
            self._router = router._router
        else:
            # router no longer exists
            self._router['status'] = RouterState.UNKNOWN

    @property
    def state(self):
        # If the router info is refreshed after it is deleted, its status will
        # be UNKNOWN.
        if self._router.get('status') == RouterState.UNKNOWN:
            return RouterState.UNKNOWN
        # GCP routers are always attached to a network.
        return RouterState.ATTACHED

    @property
    def network_id(self):
        parsed_url = self._provider.parse_url(self._router['network'])
        network = parsed_url.get_resource()
        return network['selfLink']

    @property
    def subnets(self):
        network = self._provider.networking.networks.get(self.network_id)
        return network.subnets

    def attach_subnet(self, subnet):
        if not isinstance(subnet, GCPSubnet):
            subnet = self._provider.networking.subnets.get(subnet)
        if subnet.network_id == self.network_id:
            return
        log.warning('Google Cloud Routers automatically learn new subnets '
                    'in your VPC network and announces them to your '
                    'on-premises network')

    def detach_subnet(self, network_id):
        log.warning('Cannot detach from subnet. Google Cloud Routers '
                    'automatically learn new subnets in your VPC network '
                    'and announces them to your on-premises network')

    def attach_gateway(self, gateway):
        pass

    def detach_gateway(self, gateway):
        pass


class GCPInternetGateway(BaseInternetGateway):

    def __init__(self, provider, gateway):
        super(GCPInternetGateway, self).__init__(provider)
        self._gateway = gateway
        self._fip_container = GCPFloatingIPSubService(provider, self)

    @property
    def id(self):
        return self._gateway['id']

    @property
    def name(self):
        return self._gateway['name']

    def refresh(self):
        pass

    @property
    def state(self):
        return GatewayState.AVAILABLE

    @property
    def network_id(self):
        """
        GCP internet gateways are not attached to a network.
        """
        return None

    def delete(self):
        pass

    @property
    def floating_ips(self):
        return self._fip_container


class GCPSubnet(BaseSubnet):

    def __init__(self, provider, subnet):
        super(GCPSubnet, self).__init__(provider)
        self._subnet = subnet

    @property
    def id(self):
        return self._subnet['selfLink']

    @property
    def name(self):
        return self._subnet['name']

    @property
    def label(self):
        tag_name = "_".join(["subnet", self.name, "label"])
        return helpers.get_metadata_item_value(self._provider, tag_name)

    @label.setter
    def label(self, value):
        self.assert_valid_resource_label(value)
        tag_name = "_".join(["subnet", self.name, "label"])
        helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

    @property
    def cidr_block(self):
        return self._subnet['ipCidrRange']

    @property
    def network_url(self):
        return self._subnet['network']

    @property
    def network_id(self):
        return self.network_url

    @property
    def region(self):
        return self._subnet['region']

    @property
    def region_name(self):
        parsed_url = self._provider.parse_url(self.id)
        return parsed_url.parameters['region']

    @property
    def zone(self):
        return None

    @property
    def state(self):
        if self._subnet.get('status') == SubnetState.UNKNOWN:
            return SubnetState.UNKNOWN
        return SubnetState.AVAILABLE

    def refresh(self):
        subnet = self._provider.networking.subnets.get(self.id)
        if subnet:
            # pylint:disable=protected-access
            self._subnet = subnet._subnet
        else:
            # subnet no longer exists
            self._subnet['status'] = SubnetState.UNKNOWN


class GCPVolume(BaseVolume):

    VOLUME_STATE_MAP = {
        'CREATING': VolumeState.CONFIGURING,
        'FAILED': VolumeState.ERROR,
        'READY': VolumeState.AVAILABLE,
        'RESTORING': VolumeState.CONFIGURING,
    }

    def __init__(self, provider, volume):
        super(GCPVolume, self).__init__(provider)
        self._volume = volume

    @property
    def id(self):
        return self._volume.get('selfLink')

    @property
    def name(self):
        """
        Get the volume name.
        """
        return self._volume.get('name')

    @property
    def label(self):
        labels = self._volume.get('labels')
        return labels.get('cblabel', '') if labels else ''

    @label.setter
    def label(self, value):
        req = (self._provider
                   .gcp_compute
                   .disks()
                   .setLabels(project=self._provider.project_name,
                              zone=self.zone_name,
                              resource=self.name,
                              body={}))

        helpers.change_label(self, 'cblabel', value, '_volume', req)

    @property
    def description(self):
        labels = self._volume.get('labels')
        if labels and 'description' in labels:
            return labels.get('description', '')
        return self._volume.get('description', '')

    @description.setter
    def description(self, value):
        req = (self._provider
               .gcp_compute
               .disks()
               .setLabels(project=self._provider.project_name,
                          zone=self.zone_name,
                          resource=self.name,
                          body={}))

        helpers.change_label(self, 'description', value, '_volume', req)

    @property
    def size(self):
        return int(self._volume.get('sizeGb'))

    @property
    def create_time(self):
        return self._volume.get('creationTimestamp')

    @property
    def zone_id(self):
        return self._volume.get('zone')

    @property
    def zone_name(self):
        return self._provider.parse_url(self.zone_id).parameters['zone']

    @property
    def source(self):
        if 'sourceSnapshot' in self._volume:
            snapshot_uri = self._volume.get('sourceSnapshot')
            return GCPSnapshot(
                    self._provider,
                    self._provider.parse_url(snapshot_uri).get_resource())
        if 'sourceImage' in self._volume:
            image_uri = self._volume.get('sourceImage')
            return GCPMachineImage(
                    self._provider,
                    self._provider.parse_url(image_uri).get_resource())
        return None

    @property
    def attachments(self):
        # GCP Persistent Disk supports multiple instances attaching a READ-ONLY
        # disk. In cloudbridge, volume usage pattern is that a disk is attached
        # to a single instance in a read-write mode. Therefore, we only check
        # the first user of a disk.
        if 'users' in self._volume and len(self._volume) > 0:
            if len(self._volume) > 1:
                log.warning("This volume is attached to multiple instances")
            return BaseAttachmentInfo(self,
                                      self._volume.get('users')[0],
                                      None)
        else:
            return None

    def attach(self, instance, device):
        """
        Attach this volume to an instance.

        instance: The ID of an instance or an ``Instance`` object to
                  which this volume will be attached.

        To use the disk, the user needs to mount the disk so that the operating
        system can use the available storage space.
        https://cloud.google.com/compute/docs/disks/add-persistent-disk
        """
        attach_disk_body = {
            "source": self.id,
            "deviceName": device.split('/')[-1],
        }
        if not isinstance(instance, GCPInstance):
            instance = self._provider.get_resource('instances', instance)
        (self._provider
             .gcp_compute
             .instances()
             .attachDisk(project=self._provider.project_name,
                         zone=instance.zone_name,
                         instance=instance.name,
                         body=attach_disk_body)
             .execute())

    def detach(self, force=False):
        """
        Detach this volume from an instance.
        """
        # Check whether this volume is attached to an instance.
        if not self.attachments:
            return
        parsed_uri = self._provider.parse_url(self.attachments.instance_id)
        instance_data = parsed_uri.get_resource()
        # Check whether the instance has this volume attached.
        if 'disks' not in instance_data:
            return
        device_name = None
        for disk in instance_data['disks']:
            if ('source' in disk and 'deviceName' in disk and
                    disk['source'] == self.id):
                device_name = disk['deviceName']
        if not device_name:
            return
        (self._provider
             .gcp_compute
             .instances()
             .detachDisk(project=self._provider.project_name,
                         zone=self.zone_name,
                         instance=instance_data.get('name'),
                         deviceName=device_name)
             .execute())

    def create_snapshot(self, label, description=None):
        """
        Create a snapshot of this Volume.
        """
        return self._provider.storage.snapshots.create(
            label, self, description)

    @property
    def state(self):
        if len(self._volume.get('users', [])) > 0:
            return VolumeState.IN_USE
        return GCPVolume.VOLUME_STATE_MAP.get(
            self._volume.get('status'), VolumeState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        vol = self._provider.storage.volumes.get(self.id)
        if vol:
            # pylint:disable=protected-access
            self._volume = vol._volume
        else:
            # volume no longer exists
            self._volume['status'] = VolumeState.UNKNOWN


class GCPSnapshot(BaseSnapshot):

    SNAPSHOT_STATE_MAP = {
        'PENDING': SnapshotState.PENDING,
        'READY': SnapshotState.AVAILABLE,
    }

    def __init__(self, provider, snapshot):
        super(GCPSnapshot, self).__init__(provider)
        self._snapshot = snapshot

    @property
    def id(self):
        return self._snapshot.get('selfLink')

    @property
    def name(self):
        """
        Get the snapshot name.
        """
        return self._snapshot.get('name')

    @property
    def label(self):
        labels = self._snapshot.get('labels')
        return labels.get('cblabel', '') if labels else ''

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        req = (self._provider
                   .gcp_compute
                   .snapshots()
                   .setLabels(project=self._provider.project_name,
                              resource=self.name,
                              body={}))

        helpers.change_label(self, 'cblabel', value, '_snapshot', req)

    @property
    def description(self):
        labels = self._snapshot.get('labels')
        if labels and 'description' in labels:
            return labels.get('description', '')
        return self._snapshot.get('description', '')

    @description.setter
    def description(self, value):
        req = (self._provider
               .gcp_compute
               .snapshots()
               .setLabels(project=self._provider.project_name,
                          resource=self.name,
                          body={}))

        helpers.change_label(self, 'description', value, '_snapshot', req)

    @property
    def size(self):
        return int(self._snapshot.get('diskSizeGb'))

    @property
    def volume_id(self):
        return self._snapshot.get('sourceDisk')

    @property
    def create_time(self):
        return self._snapshot.get('creationTimestamp')

    @property
    def state(self):
        return GCPSnapshot.SNAPSHOT_STATE_MAP.get(
            self._snapshot.get('status'), SnapshotState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        snap = self._provider.storage.snapshots.get(self.id)
        if snap:
            # pylint:disable=protected-access
            self._snapshot = snap._snapshot
        else:
            # snapshot no longer exists
            self._snapshot['status'] = SnapshotState.UNKNOWN

    def create_volume(self, size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.

        Args:
            placement: GCP zone name, e.g. 'us-central1-f'.
            size: The size of the new volume, in GiB (optional). Defaults to
                the size of the snapshot.
            volume_type: Type of persistent disk. Either 'pd-standard' or
                'pd-ssd'.
            iops: Not supported by GCP.
        """
        zone_name = self._provider.zone_name
        vol_type = 'zones/{0}/diskTypes/{1}'.format(
            zone_name,
            'pd-standard' if (volume_type != 'pd-standard' or
                              volume_type != 'pd-ssd') else volume_type)
        disk_body = {
            'name': ('created-from-{0}'.format(self.name))[:63],
            'sizeGb': size if size is not None else self.size,
            'type': vol_type,
            'sourceSnapshot': self.id
        }
        operation = (self._provider
                         .gcp_compute
                         .disks()
                         .insert(project=self._provider.project_name,
                                 zone=zone_name,
                                 body=disk_body)
                         .execute())
        return self._provider.storage.volumes.get(
            operation.get('targetLink'))


class GCPBucketObject(BaseBucketObject):

    def __init__(self, provider, bucket, obj):
        super(GCPBucketObject, self).__init__(provider)
        self._bucket = bucket
        self._obj = obj

    @property
    def id(self):
        return self._obj['selfLink']

    @property
    def name(self):
        return self._obj['name']

    @property
    def size(self):
        return int(self._obj['size'])

    @property
    def last_modified(self):
        return self._obj['updated']

    def iter_content(self):
        return io.BytesIO(self._provider
                              .gcp_storage
                              .objects()
                              .get_media(bucket=self._obj['bucket'],
                                         object=self.name)
                              .execute())

    def upload(self, data):
        """
        Set the contents of this object to the given text.
        """
        if type(data) is str:
            data = data.encode()
        media_body = googleapiclient.http.MediaIoBaseUpload(
                io.BytesIO(data), mimetype='plain/text')
        # pylint:disable=protected-access
        response = (self._provider
                        .storage._bucket_objects
                        ._create_object_with_media_body(self._bucket,
                                                        self.name,
                                                        media_body))
        if response:
            self._obj = response

    def upload_from_file(self, path):
        """
        Upload a binary file.
        """
        with open(path, 'rb') as f:
            media_body = googleapiclient.http.MediaIoBaseUpload(
                    f, 'application/octet-stream')
            # pylint:disable=protected-access
            response = (self._provider
                        .storage._bucket_objects
                        ._create_object_with_media_body(self._bucket,
                                                        self.name,
                                                        media_body))
            if response:
                self._obj = response

    def delete(self):
        (self._provider
             .gcp_storage
             .objects()
             .delete(bucket=self._obj['bucket'], object=self.name)
             .execute())

    def generate_url(self, expires_in, writable=False):
        """
        Generates a signed URL accessible to everyone.

        Note that if the user asks for write permissions, we need
        to set the `http_method` as PUT so the user can keep updating
        the files with the same URL.

        """
        http_method = "PUT" if writable else "GET"

        # pylint:disable=protected-access
        return helpers.generate_signed_url(
            self._provider._credentials, self._obj['bucket'], self.name,
            expiration=expires_in, http_method=http_method)

    def refresh(self):
        # pylint:disable=protected-access
        self._obj = self.bucket.objects.get(self.id)._obj


class GCPBucket(BaseBucket):

    def __init__(self, provider, bucket):
        super(GCPBucket, self).__init__(provider)
        self._bucket = bucket
        self._object_container = GCPBucketObjectSubService(provider, self)

    @property
    def id(self):
        return self._bucket['selfLink']

    @property
    def name(self):
        """
        Get this bucket's name.
        """
        return self._bucket['name']

    @property
    def objects(self):
        return self._object_container


class GCPLaunchConfig(BaseLaunchConfig):

    def __init__(self, provider):
        super(GCPLaunchConfig, self).__init__(provider)


class GCPDnsZone(BaseDnsZone):

    def __init__(self, provider, dns_zone):
        super(GCPDnsZone, self).__init__(provider)
        self._dns_zone = dns_zone
        self._dns_record_container = GCPDnsRecordSubService(provider, self)

    @property
    def id(self):
        return self._dns_zone.get('name')

    @property
    def name(self):
        return self._dns_zone.get('dnsName')

    @property
    def admin_email(self):
        comment = self._dns_zone.get('description')
        if comment:
            email_field = comment.split(",")[0].split("=")
            if email_field[0] == "admin_email":
                return email_field[1]
            else:
                return None
        else:
            return None

    @property
    def records(self):
        return self._dns_record_container


class GCPDnsRecord(BaseDnsRecord):

    def __init__(self, provider, dns_zone, dns_record):
        super(GCPDnsRecord, self).__init__(provider)
        self._dns_zone = dns_zone
        self._dns_rec = dns_record

    @property
    def id(self):
        return self._dns_rec.get('name') + ":" + self._dns_rec.get('type')

    @property
    def name(self):
        return self._dns_rec.get('name')

    @property
    def zone_id(self):
        return self._dns_zone.id

    @property
    def type(self):
        return self._dns_rec.get('type')

    @property
    def data(self):
        return self._dns_rec.get('rrdatas')

    @property
    def ttl(self):
        return self._dns_rec.get('ttl')

    def delete(self):
        # pylint:disable=protected-access
        return self._provider.dns._records.delete(self._dns_zone, self)
