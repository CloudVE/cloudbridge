"""
DataTypes used by this provider
"""
import hashlib
import inspect
import io
import json
import math
import re
import uuid

import cloudbridge as cb
from cloudbridge.cloud.base.resources import BaseAttachmentInfo
from cloudbridge.cloud.base.resources import BaseBucket
from cloudbridge.cloud.base.resources import BaseBucketObject
from cloudbridge.cloud.base.resources import BaseFloatingIP
from cloudbridge.cloud.base.resources import BaseInstance
from cloudbridge.cloud.base.resources import BaseInstanceType
from cloudbridge.cloud.base.resources import BaseKeyPair
from cloudbridge.cloud.base.resources import BaseMachineImage
from cloudbridge.cloud.base.resources import BaseNetwork
from cloudbridge.cloud.base.resources import BasePlacementZone
from cloudbridge.cloud.base.resources import BaseRegion
from cloudbridge.cloud.base.resources import BaseRouter
from cloudbridge.cloud.base.resources import BaseSecurityGroup
from cloudbridge.cloud.base.resources import BaseSecurityGroupRule
from cloudbridge.cloud.base.resources import BaseSnapshot
from cloudbridge.cloud.base.resources import BaseSubnet
from cloudbridge.cloud.base.resources import BaseVolume
from cloudbridge.cloud.base.resources import ServerPagedResultList
from cloudbridge.cloud.interfaces.resources import InstanceState
from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.interfaces.resources import NetworkState
from cloudbridge.cloud.interfaces.resources import RouterState
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import VolumeState
from cloudbridge.cloud.providers.gce import helpers

import googleapiclient

# Older versions of Python do not have a built-in set data-structure.
try:
    set
except NameError:
    from sets import Set as set


class GCEKeyPair(BaseKeyPair):

    def __init__(self, provider, kp_id, kp_name, kp_material=None):
        super(GCEKeyPair, self).__init__(provider, None)
        self._kp_id = kp_id
        self._kp_name = kp_name
        self._kp_material = kp_material

    @property
    def id(self):
        return self._kp_id

    @property
    def name(self):
        # use e-mail as keyname if possible, or ID if not
        return self._kp_name or self.id

    def delete(self):
        svc = self._provider.security.key_pairs

        def _delete_key(gce_kp_generator):
            kp_list = []
            for gce_kp in gce_kp_generator:
                if svc.gce_kp_to_id(gce_kp) == self.id:
                    continue
                else:
                    kp_list.append(gce_kp)
            return kp_list

        svc.gce_metadata_save_op(_delete_key)

    @property
    def material(self):
        return self._kp_material

    @material.setter
    def material(self, value):
        self._kp_material = value


class GCEInstanceType(BaseInstanceType):
    def __init__(self, provider, instance_dict):
        super(GCEInstanceType, self).__init__(provider)
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
        return self._inst_dict.get('memoryMb')

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


class GCEPlacementZone(BasePlacementZone):

    def __init__(self, provider, zone, region):
        super(GCEPlacementZone, self).__init__(provider)
        if isinstance(zone, GCEPlacementZone):
            # pylint:disable=protected-access
            self._gce_zone = zone._gce_zone
            self._gce_region = zone._gce_region
        else:
            self._gce_zone = zone
            self._gce_region = region

    @property
    def id(self):
        """
        Get the zone id
        :rtype: ``str``
        :return: ID for this zone as returned by the cloud middleware.
        """
        return self._gce_zone

    @property
    def name(self):
        """
        Get the zone name.
        :rtype: ``str``
        :return: Name for this zone as returned by the cloud middleware.
        """
        return self._gce_zone

    @property
    def region_name(self):
        """
        Get the region that this zone belongs to.
        :rtype: ``str``
        :return: Name of this zone's region as returned by the cloud middleware
        """
        return self._gce_region


class GCERegion(BaseRegion):

    def __init__(self, provider, gce_region):
        super(GCERegion, self).__init__(provider)
        self._gce_region = gce_region

    @property
    def id(self):
        # In GCE API, region has an 'id' property, whose values are '1220',
        # '1100', '1000', '1230', etc. Here we use 'name' property (such
        # as 'asia-east1', 'europe-west1', 'us-central1', 'us-east1') as
        # 'id' to represent the region for the consistency with AWS
        # implementation and ease of use.
        return self._gce_region['name']

    @property
    def name(self):
        return self._gce_region['name']

    @property
    def zones(self):
        """
        Accesss information about placement zones within this region.
        """
        zones_response = (self._provider
                              .gce_compute
                              .zones()
                              .list(project=self._provider.project_name)
                              .execute())
        zones = [zone for zone in zones_response['items']
                 if zone['region'] == self._gce_region['selfLink']]
        return [GCEPlacementZone(self._provider, zone['name'], self.name)
                for zone in zones]


class GCEFirewallsDelegate(object):
    DEFAULT_NETWORK = 'default'
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
            return GCEFirewallsDelegate.DEFAULT_NETWORK
        url = self._provider.parse_url(firewall['network'])
        return url.parameters['network']

    def get_tag_network_from_id(self, tag_network_id):
        """
        Map an ID back to the (tag, network name) pair.
        """
        for tag, network_name in self.tag_networks:
            current_id = GCEFirewallsDelegate.tag_network_id(tag, network_name)
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

    def add_firewall(self, tag, ip_protocol, port, source_range, source_tag,
                     description, network_name):
        """
        Create a new firewall.
        """
        if self.find_firewall(tag, ip_protocol, port, source_range,
                              source_tag, network_name) is not None:
            return True
        # Do not let the user accidentally open traffic from the world by not
        # explicitly specifying the source.
        if source_tag is None and source_range is None:
            return False
        firewall = {
            'name': 'firewall-{0}'.format(uuid.uuid4()),
            'network': GCEFirewallsDelegate._NETWORK_URL_PREFIX + network_name,
            'allowed': [{'IPProtocol': str(ip_protocol)}],
            'targetTags': [tag]}
        if description is not None:
            firewall['description'] = description
        if port is not None:
            firewall['allowed'][0]['ports'] = [port]
        if source_range is not None:
            firewall['sourceRanges'] = [source_range]
        if source_tag is not None:
            firewall['sourceTags'] = [source_tag]
        project_name = self._provider.project_name
        try:
            response = (self._provider
                            .gce_compute
                            .firewalls()
                            .insert(project=project_name,
                                    body=firewall)
                            .execute())
            self._provider.wait_for_operation(response)
            # TODO: process the response and handle errors.
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return False
        finally:
            self._update_list_response()
        return True

    def find_firewall(self, tag, ip_protocol, port, source_range, source_tag,
                      network_name):
        """
        Find a firewall with give parameters.
        """
        if source_range is None and source_tag is None:
            source_range = '0.0.0.0/0'
        for firewall in self.iter_firewalls(tag, network_name):
            if firewall['allowed'][0]['IPProtocol'] != ip_protocol:
                continue
            if not self._check_list_in_dict(firewall['allowed'][0], 'ports',
                                            port):
                continue
            if not self._check_list_in_dict(firewall, 'sourceRanges',
                                            source_range):
                continue
            if not self._check_list_in_dict(firewall, 'sourceTags',
                                            source_tag):
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
                info['source_range'] = firewall['sourceRanges'][0]
            if 'sourceTags' in firewall and len(firewall['sourceTags']) == 1:
                info['source_tag'] = firewall['sourceTags'][0]
            if 'targetTags' in firewall and len(firewall['targetTags']) == 1:
                info['target_tag'] = firewall['targetTags'][0]
            if 'IPProtocol' in firewall['allowed'][0]:
                info['ip_protocol'] = firewall['allowed'][0]['IPProtocol']
            if ('ports' in firewall['allowed'][0] and
                    len(firewall['allowed'][0]['ports']) == 1):
                info['port'] = firewall['allowed'][0]['ports'][0]
            info['network_name'] = self.network_name(firewall)
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
        if 'items' not in self._list_response:
            return
        for firewall in self._list_response['items']:
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
        try:
            response = (self._provider
                            .gce_compute
                            .firewalls()
                            .delete(project=project_name,
                                    firewall=firewall['name'])
                            .execute())
            self._provider.wait_for_operation(response)
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return False
        # TODO: process the response and handle errors.
        return True

    def _update_list_response(self):
        """
        Sync the local cache of all firewalls with the server.
        """
        self._list_response = list(
                helpers.iter_all(self._provider.gce_compute.firewalls(),
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


class GCESecurityGroup(BaseSecurityGroup):

    def __init__(self, delegate, tag, network=None, description=None):
        super(GCESecurityGroup, self).__init__(delegate.provider, tag)
        self._description = description
        self._delegate = delegate
        if network is None:
            self._network = delegate.provider.network.get_by_name(
                    GCEFirewallsDelegate.DEFAULT_NETWORK)
        else:
            self._network = network

    @property
    def id(self):
        """
        Return the ID of this security group which is determined based on the
        network and the target tag corresponding to this security group.
        """
        return GCEFirewallsDelegate.tag_network_id(self._security_group,
                                                   self._network.name)

    @property
    def name(self):
        """
        Return the name of the security group which is the same as the
        corresponding tag name.
        """
        return self._security_group

    @property
    def description(self):
        """
        The description of the security group is even explicitly given when the
        group is created or is determined from a firewall in the group.

        If the firewalls are created using this API, they all have the same
        description.
        """
        if self._description is not None:
            return self._description
        for firewall in self._delegate.iter_firewalls(self._security_group,
                                                      self._network.name):
            if 'description' in firewall:
                return firewall['description']
        return None

    @property
    def network_id(self):
        return self._network.id

    @property
    def rules(self):
        out = []
        for firewall in self._delegate.iter_firewalls(self._security_group,
                                                      self._network.name):
            out.append(GCESecurityGroupRule(self._delegate, firewall['id']))
        return out

    @staticmethod
    def to_port_range(from_port, to_port):
        if from_port is not None and to_port is not None:
            return '%d-%d' % (from_port, to_port)
        elif from_port is not None:
            return from_port
        else:
            return to_port

    def add_rule(self, ip_protocol, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        port = GCESecurityGroup.to_port_range(from_port, to_port)
        src_tag = src_group.name if src_group is not None else None
        self._delegate.add_firewall(self._security_group, ip_protocol, port,
                                    cidr_ip, src_tag, self.description,
                                    self._network.name)
        return self.get_rule(ip_protocol, from_port, to_port, cidr_ip,
                             src_group)

    def get_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        port = GCESecurityGroup.to_port_range(from_port, to_port)
        src_tag = src_group.name if src_group is not None else None
        firewall_id = self._delegate.find_firewall(
                self._security_group, ip_protocol, port, cidr_ip, src_tag,
                self._network.name)
        if firewall_id is None:
            return None
        return GCESecurityGroupRule(self._delegate, firewall_id)

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = [json.loads(r) for r in json_rules]
        return json.dumps(js, sort_keys=True)

    def delete(self):
        for rule in self.rules:
            rule.delete()


class GCESecurityGroupRule(BaseSecurityGroupRule):

    def __init__(self, delegate, firewall_id):
        super(GCESecurityGroupRule, self).__init__(
                delegate.provider, firewall_id, None)
        self._delegate = delegate

    @property
    def parent(self):
        """
        Return the security group to which this rule belongs.
        """
        info = self._delegate.get_firewall_info(self._rule)
        if info is None:
            return None
        if 'target_tag' not in info or info['network_name'] is None:
            return None
        network = self._delegate.network.get_by_name(info['network_name'])
        if network is None:
            return None
        return GCESecurityGroup(self._delegate, info['target_tag'], network)

    @property
    def id(self):
        return self._rule

    @property
    def ip_protocol(self):
        info = self._delegate.get_firewall_info(self._rule)
        if info is None or 'ip_protocol' not in info:
            return None
        return info['ip_protocol']

    @property
    def from_port(self):
        info = self._delegate.get_firewall_info(self._rule)
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
        info = self._delegate.get_firewall_info(self._rule)
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
    def cidr_ip(self):
        """
        Return the IP of machines from which this rule allows traffic.
        """
        info = self._delegate.get_firewall_info(self._rule)
        if info is None or 'source_range' not in info:
            return None
        return info['source_range']

    @property
    def group(self):
        """
        Return the security group from which this rule allows traffic.
        """
        info = self._delegate.get_firewall_info(self._rule)
        if info is None:
            return None
        if 'source_tag' not in info or info['network_name'] is None:
            return None
        network = self._delegate.provider.network.get_by_name(
                info['network_name'])
        if network is None:
            return None
        return GCESecurityGroup(self._delegate, info['source_tag'], network)

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        js['group'] = self.group.id if self.group else ''
        js['parent'] = self.parent.id if self.parent else ''
        return json.dumps(js, sort_keys=True)

    def delete(self):
        self._delegate.delete_firewall_id(self._rule)


class GCEMachineImage(BaseMachineImage):

    IMAGE_STATE_MAP = {
        'PENDING': MachineImageState.PENDING,
        'READY': MachineImageState.AVAILABLE,
        'FAILED': MachineImageState.ERROR
    }

    def __init__(self, provider, image):
        super(GCEMachineImage, self).__init__(provider)
        if isinstance(image, GCEMachineImage):
            # pylint:disable=protected-access
            self._gce_image = image._gce_image
        else:
            self._gce_image = image

    @property
    def resource_url(self):
        return self._gce_image.get('selfLink')

    @property
    def id(self):
        """
        Get the image identifier.
        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        return self._gce_image.get('selfLink')

    @property
    def name(self):
        """
        Get the image name.
        :rtype: ``str``
        :return: Name for this image as returned by the cloud middleware.
        """
        return self._gce_image['name']

    @property
    def description(self):
        """
        Get the image description.
        :rtype: ``str``
        :return: Description for this image as returned by the cloud middleware
        """
        return self._gce_image.get('description', '')

    @property
    def min_disk(self):
        """
        Returns the minimum size of the disk that's required to
        boot this image (in GB)
        :rtype: ``int``
        :return: The minimum disk size needed by this image
        """
        return int(math.ceil(float(self._gce_image.get('diskSizeGb'))))

    def delete(self):
        """
        Delete this image
        """
        (self._provider
             .gce_compute
             .images()
             .delete(project=self._provider.project_name,
                     image=self.name)
             .execute())

    @property
    def state(self):
        return GCEMachineImage.IMAGE_STATE_MAP.get(
            self._gce_image['status'], MachineImageState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        resource_link = self._gce_image['selfLink']
        project_pattern = 'projects/(.*?)/'
        match = re.search(project_pattern, resource_link)
        if match:
            project = match.group(1)
        else:
            cb.log.warning("Project name is not found.")
            return
        try:
            response = (self._provider
                            .gce_compute
                            .images()
                            .get(project=project, image=self.name)
                            .execute())
            if response:
                # pylint:disable=protected-access
                self._gce_image = response
        except googleapiclient.errors.HttpError as http_error:
            # image no longer exists
            cb.log.warning(
                "googleapiclient.errors.HttpError: {0}".format(http_error))
            self._gce_image['status'] = "unknown"


class GCEInstance(BaseInstance):
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

    def __init__(self, provider, gce_instance):
        super(GCEInstance, self).__init__(provider)
        self._gce_instance = gce_instance

    @property
    def resource_url(self):
        return self._gce_instance.get('selfLink')

    @property
    def id(self):
        """
        Get the instance identifier.

        A GCE instance is uniquely identified by its selfLink, which is used
        as its id.
        """
        return self._gce_instance.get('selfLink')

    @property
    def name(self):
        """
        Get the instance name.
        """
        return self._gce_instance['name']

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the instance name.
        """
        # In GCE, the name of the instance is provided by the client when
        # initially creating the resource. The name cannot be changed after
        # the instance is created.
        cb.log.warning("Setting instance name after it is created is not "
                       "supported by this provider.")

    @property
    def public_ips(self):
        """
        Get all the public IP addresses for this instance.
        """
        ips = []
        network_interfaces = self._gce_instance.get('networkInterfaces')
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
        for ip in self._provider.network.floating_ips():
            if ip.in_use():
                if ip.private_ip in self.private_ips:
                    ips.append(ip.public_ip)
        return ips

    @property
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        network_interfaces = self._gce_instance.get('networkInterfaces')
        if network_interfaces is None or len(network_interfaces) == 0:
            return []
        if 'networkIP' in network_interfaces[0]:
            return [network_interfaces[0]['networkIP']]
        else:
            return []

    @property
    def instance_type_id(self):
        """
        Get the instance type name.
        """
        machine_type_uri = self._gce_instance.get('machineType')
        if machine_type_uri is None:
            return None
        parsed_uri = self._provider.parse_url(machine_type_uri)
        return parsed_uri.parameters['machineType']

    @property
    def instance_type(self):
        """
        Get the instance type.
        """
        machine_type_uri = self._gce_instance.get('machineType')
        if machine_type_uri is None:
            return None
        parsed_uri = self._provider.parse_url(machine_type_uri)
        return GCEInstanceType(self._provider, parsed_uri.get_resource())

    def reboot(self):
        """
        Reboot this instance.
        """
        if self.state == InstanceState.STOPPED:
            (self._provider
                 .gce_compute
                 .instances()
                 .start(project=self._provider.project_name,
                        zone=self._provider.default_zone,
                        instance=self.name)
                 .execute())
        else:
            (self._provider
                 .gce_compute
                 .instances()
                 .reset(project=self._provider.project_name,
                        zone=self._provider.default_zone,
                        instance=self.name)
                 .execute())

    def terminate(self):
        """
        Permanently terminate this instance.
        """
        (self._provider
             .gce_compute
             .instances()
             .delete(project=self._provider.project_name,
                     zone=self._provider.default_zone,
                     instance=self.name)
             .execute())

    def stop(self):
        """
        Stop this instance.
        """
        (self._provider
             .gce_compute
             .instances()
             .stop(project=self._provider.project_name,
                   zone=self._provider.default_zone,
                   instance=self.name)
             .execute())

    @property
    def image_id(self):
        """
        Get the image ID for this insance.
        """
        if 'disks' not in self._gce_instance:
            return None
        for disk in self._gce_instance['disks']:
            if 'boot' in disk and disk['boot']:
                disk_url = self._provider.parse_url(disk['source'])
                return disk_url.get_resource().get('sourceImage')
        return None

    @property
    def zone_id(self):
        """
        Get the placement zone id where this instance is running.
        """
        zone_uri = self._gce_instance.get('zone')
        if zone_uri is None:
            return None
        return self._provider.parse_url(zone_uri).parameters['zone']

    @property
    def security_groups(self):
        """
        Get the security groups associated with this instance.
        """
        network_url = self._gce_instance.get('networkInterfaces')[0].get(
            'network')
        url = self._provider.parse_url(network_url)
        network_name = url.parameters['network']
        if 'items' not in self._gce_instance['tags']:
            return []
        tags = self._gce_instance['tags']['items']
        # Tags are mapped to non-empty security groups under the instance
        # network. Unmatched tags are ignored.
        sgs = (self._provider.security
               .security_groups.find_by_network_and_tags(
                   network_name, tags))
        return sgs

    @property
    def security_group_ids(self):
        """
        Get the security groups IDs associated with this instance.
        """
        sg_ids = []
        for sg in self.security_groups:
            sg_ids.append(sg.id)
        return sg_ids

    @property
    def key_pair_name(self):
        """
        Get the name of the key pair associated with this instance.
        """
        return self._provider.security.key_pairs.name

    def create_image(self, name):
        """
        Create a new image based on this instance.
        """
        if 'disks' not in self._gce_instance:
            cb.log.error('Failed to create image: no disks found.')
            return
        for disk in self._gce_instance['disks']:
            if 'boot' in disk and disk['boot']:
                image_body = {
                    'name': name,
                    'sourceDisk': disk['source']
                }
                operation = (self._provider
                             .gce_compute
                             .images()
                             .insert(project=self._provider.project_name,
                                     body=image_body)
                             .execute())
                self._provider.wait_for_operation(operation)
                return
        cb.log.error('Failed to create image: no boot disk found.')

    def _get_existing_target_instance(self):
        """
        Return the target instance corrsponding to this instance.

        If there is no target instance for this instance, return None.
        """
        self_url = self._provider.parse_url(self._gce_instance['selfLink'])
        try:
            for target_instance in helpers.iter_all(
                    self._provider.gce_compute.targetInstances(),
                    project=self_url.parameters['project'],
                    zone=self_url.parameters['zone']):
                url = self._provider.parse_url(target_instance['instance'])
                if url.parameters['instance'] == self.name:
                    return target_instance
        except Exception as e:
            cb.log.warning('Exception while listing target instances: %s', e)
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
        self_url = self._provider.parse_url(self._gce_instance['selfLink'])
        body = {'name': 'target-instance-{0}'.format(uuid.uuid4()),
                'instance': self._gce_instance['selfLink']}
        try:
            response = (self._provider
                            .gce_compute
                            .targetInstances()
                            .insert(project=self_url.parameters['project'],
                                    zone=self_url.parameters['zone'],
                                    body=body)
                            .execute())
            self._provider.wait_for_operation(
                response, zone=self_url.parameters['zone'])
        except Exception as e:
            cb.log.warning('Exception while inserting a target instance: %s',
                           e)
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
                    self._provider.gce_compute.forwardingRules(),
                    project=self._provider.project_name,
                    region=ip.region):
                if rule['IPAddress'] != ip.public_ip:
                    continue
                parsed_target_url = self._provider.parse_url(rule['target'])
                old_zone = parsed_target_url.parameters['zone']
                old_name = parsed_target_url.parameters['targetInstance']
                if old_zone == new_zone and old_name == new_name:
                    return True
                response = (self._provider
                                .gce_compute
                                .forwardingRules()
                                .setTarget(
                                    project=self._provider.project_name,
                                    region=ip.region,
                                    forwardingRule=rule['name'],
                                    body={'target': new_url})
                                .execute())
                self._provider.wait_for_operation(response, region=ip.region)
                return True
        except Exception as e:
            cb.log.warning(
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
                            .gce_compute
                            .forwardingRules()
                            .insert(project=self._provider.project_name,
                                    region=ip.region,
                                    body=body)
                            .execute())
            self._provider.wait_for_operation(response, region=ip.region)
        except Exception as e:
            cb.log.warning('Exception while inserting a forwarding rule: %s',
                           e)
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
                    self._provider.gce_compute.forwardingRules(),
                    project=self._provider.project_name,
                    region=ip.region):
                if rule['IPAddress'] != ip.public_ip:
                    continue
                parsed_target_url = self._provider.parse_url(rule['target'])
                temp_zone = parsed_target_url.parameters['zone']
                temp_name = parsed_target_url.parameters['targetInstance']
                if temp_zone != zone or temp_name != name:
                    cb.log.warning(
                            '"%s" is forwarded to "%s" in zone "%s"',
                            ip.public_ip, temp_name, temp_zone)
                    return False
                response = (self._provider
                                .gce_compute
                                .forwardingRules()
                                .delete(
                                    project=self._provider.project_name,
                                    region=ip.region,
                                    forwardingRule=rule['name'])
                                .execute())
                self._provider.wait_for_operation(response, region=ip.region)
                return True
        except Exception as e:
            cb.log.warning(
                'Exception while listing/deleting forwarding rules: %s', e)
            return False
        return True

    def add_floating_ip(self, ip_address):
        """
        Add an elastic IP address to this instance.
        """
        for ip in self._provider.network.floating_ips():
            if ip.public_ip == ip_address:
                if ip.in_use():
                    if ip.private_ip not in self.private_ips:
                        cb.log.warning(
                            'Floating IP "%s" is already associated to "%s".',
                            ip_address, self.name)
                    return
                target_instance = self._get_target_instance()
                if not target_instance:
                    cb.log.warning(
                            'Could not create a targetInstance for "%s"',
                            self.name)
                    return
                if not self._forward(ip, target_instance):
                    cb.log.warning('Could not forward "%s" to "%s"',
                                   ip.public_ip, target_instance['selfLink'])
                return
        cb.log.warning('Floating IP "%s" does not exist.', ip_address)

    def remove_floating_ip(self, ip_address):
        """
        Remove a elastic IP address from this instance.
        """
        for ip in self._provider.network.floating_ips():
            if ip.public_ip == ip_address:
                if not ip.in_use() or ip.private_ip not in self.private_ips:
                    cb.log.warning(
                        'Floating IP "%s" is not associated to "%s".',
                        ip_address, self.name)
                    return
                target_instance = self._get_target_instance()
                if not target_instance:
                    # We should not be here.
                    cb.log.warning('Something went wrong! "%s" is associated '
                                   'to "%s" with no target instance',
                                   ip_address, self.name)
                    return
                if not self._delete_existing_rule(ip, target_instance):
                    cb.log.warning(
                        'Could not remove floating IP "%s" from instance "%s"',
                        ip.public_ip, self.name)
                return
        cb.log.warning('Floating IP "%s" does not exist.', ip_address)

    @property
    def state(self):
        return GCEInstance.INSTANCE_STATE_MAP.get(
            self._gce_instance['status'], InstanceState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        self_link = self._gce_instance.get('selfLink')
        self._gce_instance = self._provider.parse_url(self_link).get_resource()

    def add_security_group(self, sg):
        raise NotImplementedError('To be implemented.')

    def remove_security_group(self, sg):
        raise NotImplementedError('To be implemented.')


class GCENetwork(BaseNetwork):

    def __init__(self, provider, network):
        super(GCENetwork, self).__init__(provider)
        self._network = network

    @property
    def resource_url(self):
        return self._network['selfLink']

    @property
    def id(self):
        return self._network['id']

    @property
    def name(self):
        return self._network['name']

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
        return NetworkState.AVAILABLE

    @property
    def cidr_block(self):
        return self._network['IPv4Range']

    def delete(self):
        try:
            response = (self._provider
                            .gce_compute
                            .networks()
                            .delete(project=self._provider.project_name,
                                    network=self.name)
                            .execute())
            if 'error' in response:
                return False
            self._provider.wait_for_operation(response)
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return False
        return True

    def subnets(self):
        return self._provider.network.subnets.list()

    def create_subnet(self, cidr_block, name=None):
        return self._provider.network.subnets.create(self, cidr_block, name)

    def refresh(self):
        return self.state


class GCEFloatingIP(BaseFloatingIP):
    _DEAD_INSTANCE = 'dead instance'

    def __init__(self, provider, floating_ip):
        super(GCEFloatingIP, self).__init__(provider)
        self._ip = floating_ip

        # We use regional IPs to simulate floating IPs not global IPs because
        # global IPs can be forwarded only to load balancing resources, not to
        # a specific instance. Find out the region to which the IP belongs.
        url = provider.parse_url(self._ip['region'])
        self._region = url.parameters['region']

        # Check if the address is used by a resource.
        self._rule = None
        self._target_instance = None
        if 'users' in floating_ip and len(floating_ip['users']) > 0:
            if len(floating_ip['users']) > 1:
                cb.log.warning('Address "%s" in use by more than one resource',
                               floating_ip['address'])
            resource_parsed_url = provider.parse_url(floating_ip['users'][0])
            resource = resource_parsed_url.get_resource()
            if resource['kind'] == 'compute#forwardingRule':
                self._rule = resource
                target = provider.parse_url(resource['target']).get_resource()
                if target['kind'] == 'compute#targetInstance':
                    url = provider.parse_url(target['instance'])
                    try:
                        self._target_instance = url.get_resource()
                    except googleapiclient.errors.HttpError:
                        self._target_instance = GCEFloatingIP._DEAD_INSTANCE
                else:
                    cb.log.warning('Address "%s" is forwarded to a %s',
                                   floating_ip['address'], target['kind'])
            else:
                cb.log.warning('Address "%s" in use by a %s',
                               floating_ip['address'], resource['kind'])

    @property
    def id(self):
        return self._ip['id']

    @property
    def region(self):
        return self._region

    @property
    def public_ip(self):
        return self._ip['address']

    @property
    def private_ip(self):
        if (not self._target_instance or
                self._target_instance == GCEFloatingIP._DEAD_INSTANCE):
            return None
        return self._target_instance['networkInterfaces'][0]['networkIP']

    def in_use(self):
        return True if self._target_instance else False

    def delete(self):
        project_name = self._provider.project_name
        # First, delete the forwarding rule, if there is any.
        if self._rule:
            response = (self._provider
                            .gce_compute
                            .forwardingRules()
                            .delete(project=project_name,
                                    region=self._region,
                                    forwardingRule=self._rule['name'])
                            .execute())
            self._provider.wait_for_operation(response, region=self._region)

        # Release the address.
        response = (self._provider
                        .gce_compute
                        .addresses()
                        .delete(project=project_name,
                                region=self._region,
                                address=self._ip['name'])
                        .execute())
        self._provider.wait_for_operation(response, region=self._region)


class GCERouter(BaseRouter):

    def __init__(self, provider, router):
        super(GCERouter, self).__init__(provider)
        self._router = router

    @property
    def id(self):
        return self._router['id']

    @property
    def name(self):
        return self._router['name']

    def refresh(self):
        parsed_url = self._provider.parse_url(self._router['selfLink'])
        self._router = parsed_url.get_resource()

    @property
    def state(self):
        # GCE routers are always attached to a network.
        return RouterState.ATTACHED

    @property
    def network_id(self):
        parsed_url = self._provider.parse_url(self._router['network'])
        network = parsed_url.get_resource()
        return network['id']

    def delete(self):
        response = (self._provider
                        .gce_compute
                        .routers()
                        .delete(project=self._provider.project_name,
                                region=self._router['region'],
                                router=self._router['name'])
                        .execute())
        self._provider.wait_for_operation(response,
                                          region=self._router['region'])

    def attach_network(self, network_id):
        if network_id == self.network_id:
            return
        cb.log.warning('GCE routers should be attached at creation time')

    def detach_network(self, network_id):
        cb.log.warning('GCE routers are always attached')

    def add_route(self, subnet_id):
        cb.log.warning('Not implemented')

    def remove_route(self, subnet_id):
        cb.log.warning('Not implemented')


class GCESubnet(BaseSubnet):

    def __init__(self, provider, subnet):
        super(GCESubnet, self).__init__(provider)
        self._subnet = subnet

    @property
    def id(self):
        return self._subnet['id']

    @property
    def name(self):
        return self._subnet['name']

    @name.setter
    def name(self, value):
        if value == self.name:
            return
        cb.log.warning('Cannot change the name of a GCE subnetwork')

    @property
    def cidr_block(self):
        return self._subnet['ipCidrRange']

    @property
    def network_url(self):
        return self._subnet['network']

    @property
    def network_id(self):
        return self._provider.parse_url(self.network_url).get_resource()['id']

    @property
    def region(self):
        return self._subnet['region']

    @property
    def zone(self):
        return None

    @property
    def delete(self):
        return self._provider.network.subnets.delete(self)


class GCEVolume(BaseVolume):

    VOLUME_STATE_MAP = {
        'RESTORING': VolumeState.CONFIGURING,
        'PENDING': VolumeState.CONFIGURING,
        'READY': VolumeState.AVAILABLE,
        'DONE': VolumeState.AVAILABLE,
        'RUNNING': VolumeState.IN_USE,
    }

    def __init__(self, provider, volume):
        super(GCEVolume, self).__init__(provider)
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

    @name.setter
    def name(self, value):
        """
        Set the volume name.
        """
        raise NotImplementedError('Not supported by this provider.')

    @property
    def description(self):
        labels = self._volume.get('labels')
        if not labels or 'description' not in labels:
            return ''
        return labels.get('description', '')

    @description.setter
    def description(self, value):
        request_body = {
            'labels': {'description': value.replace(' ', '_').lower()},
            'labelFingerprint': self._volume.get('labelFingerprint'),
        }
        try:
            (self._provider
                 .gce_compute
                 .disks()
                 .setLabels(project=self._provider.project_name,
                            zone=self._provider.default_zone,
                            resource=self.name,
                            body=request_body)
                 .execute())
        except Exception as e:
            cb.log.warning('Exception while setting volume description: %s. '
                           'Check for invalid characters in description. '
                           'Should confirm to RFC1035.', e)
            raise e
        self.refresh()

    @property
    def size(self):
        return self._volume.get('sizeGb')

    @property
    def create_time(self):
        return self._volume.get('creationTimestamp')

    @property
    def zone_id(self):
        return self._volume.get('zone')

    @property
    def source(self):
        if 'sourceSnapshot' in self._volume:
            snapshot_uri = self._volume.get('sourceSnapshot')
            return GCESnapshot(
                    self._provider,
                    self._provider.parse_url(snapshot_uri).get_resource())
        if 'sourceImage' in self._volume:
            image_uri = self._volume.get('sourceImage')
            return GCEMachineImage(
                    self._provider,
                    self._provider.parse_url(image_uri).get_resource())
        return None

    @property
    def attachments(self):
        # GCE Persistent Disk supports multiple instances attaching a READ-ONLY
        # disk. In cloudbridge, volume usage pattern is that a disk is attached
        # to a single instance in a read-write mode. Therefore, we only check
        # the first user of a disk.
        if 'users' in self._volume and len(self._volume) > 0:
            if len(self._volume) > 1:
                cb.log.warning("This volume is attached to multiple instances")
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
            "deviceName": device,
        }
        instance_name = instance.name if isinstance(
            instance,
            GCEInstance) else instance
        (self._provider
             .gce_compute
             .instances()
             .attachDisk(project=self._provider.project_name,
                         zone=self._provider.default_zone,
                         instance=instance_name,
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
             .gce_compute
             .instances()
             .detachDisk(project=self._provider.project_name,
                         zone=self._provider.default_zone,
                         instance=instance_data.get('name'),
                         deviceName=device_name)
             .execute())

    def create_snapshot(self, name, description=None):
        """
        Create a snapshot of this Volume.
        """
        return self._provider.block_store.snapshots.create(
            name, self, description)

    def delete(self):
        """
        Delete this volume.
        """
        (self._provider
             .gce_compute
             .disks()
             .delete(project=self._provider.project_name,
                     zone=self._provider.default_zone,
                     disk=self.name)
             .execute())

    @property
    def state(self):
        return GCEVolume.VOLUME_STATE_MAP.get(
            self._volume.get('status'), VolumeState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        self_link = self._volume.get('selfLink')
        self._volume = self._provider.parse_url(self_link).get_resource()


class GCESnapshot(BaseSnapshot):

    SNAPSHOT_STATE_MAP = {
        'PENDING': SnapshotState.PENDING,
        'READY': SnapshotState.AVAILABLE,
    }

    def __init__(self, provider, snapshot):
        super(GCESnapshot, self).__init__(provider)
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

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the snapshot name.
        """
        raise NotImplementedError('Not supported by this provider.')

    @property
    def description(self):
        return self._snapshot.get('description')

    @description.setter
    def description(self, value):
        raise NotImplementedError('Not supported by this provider.')

    @property
    def size(self):
        return self._snapshot.get('diskSizeGb')

    @property
    def volume_id(self):
        return self._snapshot.get('sourceDisk')

    @property
    def create_time(self):
        return self._snapshot.get('creationTimestamp')

    @property
    def state(self):
        return GCESnapshot.SNAPSHOT_STATE_MAP.get(
            self._snapshot.get('status'), SnapshotState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        self_link = self._snapshot.get('selfLink')
        self._snapshot = self._provider.parse_url(self_link).get_resource()

    def delete(self):
        """
        Delete this snapshot.
        """
        (self._provider
             .gce_compute
             .snapshots()
             .delete(project=self._provider.project_name,
                     snapshot=self.name)
             .execute())

    def create_volume(self, placement, size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.

        Args:
            placement: GCE zone name, e.g. 'us-central1-f'.
            size: The size of the new volume, in GiB (optional). Defaults to
                the size of the snapshot.
            volume_type: Type of persistent disk. Either 'pd-standard' or
                'pd-ssd'.
            iops: Not supported by GCE.
        """
        vol_type = 'zones/{0}/diskTypes/{1}'.format(
            placement,
            'pd-standard' if (volume_type != 'pd-standard' or
                              volume_type != 'pd-ssd') else volume_type)
        disk_body = {
            'name': 'created-from-{0}'.format(self.name),
            'sizeGb': size if size is not None else self.size,
            'type': vol_type,
            'sourceSnapshot': self.id
        }
        operation = (self._provider
                         .gce_compute
                         .disks()
                         .insert(project=self._provider.project_name,
                                 zone=placement,
                                 body=disk_body)
                         .execute())
        return self._provider.block_store.volumes.get(
            operation.get('targetLink'))


class GCSObject(BaseBucketObject):

    def __init__(self, provider, bucket, obj):
        super(GCSObject, self).__init__(provider)
        self._bucket = bucket
        self._obj = obj

    @property
    def id(self):
        return self._obj['id']

    @property
    def name(self):
        return self._obj['name']

    @property
    def size(self):
        return self._obj['size']

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
        media_body = googleapiclient.http.MediaIoBaseUpload(
                io.BytesIO(data), mimetype='plain/text')
        response = self._bucket.create_object_with_media_body(self.name,
                                                              media_body)
        if response:
            self._obj = response

    def upload_from_file(self, path):
        """
        Upload a binary file.
        """
        with open(path, 'rb') as f:
            media_body = googleapiclient.http.MediaIoBaseUpload(
                    f, 'application/octet-stream')
            response = self._bucket.create_object_with_media_body(self.name,
                                                                  media_body)
            if response:
                self._obj = response

    def delete(self):
        (self._provider
             .gcp_storage
             .objects()
             .delete(bucket=self._obj['bucket'], object=self.name)
             .execute())

    def generate_url(self, expires_in=0):
        return self._obj['mediaLink']


class GCSBucket(BaseBucket):

    def __init__(self, provider, bucket):
        super(GCSBucket, self).__init__(provider)
        self._bucket = bucket

    @property
    def id(self):
        return self._bucket['id']

    @property
    def name(self):
        """
        Get this bucket's name.
        """
        return self._bucket['name']

    def get(self, name):
        """
        Retrieve a given object from this bucket.
        """
        try:
            response = (self._provider
                            .gcp_storage
                            .objects()
                            .get(bucket=self.name, object=name)
                            .execute())
            if 'error' in response:
                return None
            return GCSObject(self._provider, self, response)
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return None

    def list(self, limit=None, marker=None, prefix=None):
        """
        List all objects within this bucket.
        """
        max_result = limit if limit is not None and limit < 500 else 500
        try:
            response = (self._provider
                            .gcp_storage
                            .objects()
                            .list(bucket=self.name,
                                  prefix=prefix if prefix else '',
                                  maxResults=max_result,
                                  pageToken=marker)
                            .execute())
            if 'error' in response:
                return ServerPagedResultList(False, None, False, data=[])
            objects = []
            for obj in response.get('items', []):
                objects.append(GCSObject(self._provider, self, obj))
            if len(objects) > max_result:
                cb.log.warning('Expected at most %d results; got %d',
                               max_result, len(objects))
            return ServerPagedResultList('nextPageToken' in response,
                                         response.get('nextPageToken'),
                                         False, data=objects)
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return ServerPagedResultList(False, None, False, data=[])

    def delete(self, delete_contents=False):
        """
        Delete this bucket.
        """
        (self._provider
             .gcp_storage
             .buckets()
             .delete(bucket=self.name)
             .execute())

    def create_object(self, name):
        """
        Create an empty plain text object.
        """
        response = self.create_object_with_media_body(
            name,
            googleapiclient.http.MediaIoBaseUpload(
                    io.BytesIO(''), mimetype='plain/text'))
        return GCSObject(self._provider, self, response) if response else None

    def create_object_with_media_body(self, name, media_body):
        try:
            response = (self._provider
                            .gcp_storage
                            .objects()
                            .insert(bucket=self.name,
                                    body={'name': name},
                                    media_body=media_body)
                            .execute())
            if 'error' in response:
                return None
            return response
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return None
