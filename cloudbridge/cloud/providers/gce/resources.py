"""
DataTypes used by this provider
"""
from cloudbridge.cloud.base.resources import BaseInstanceType
from cloudbridge.cloud.base.resources import BaseKeyPair
from cloudbridge.cloud.base.resources import BaseMachineImage
from cloudbridge.cloud.base.resources import BaseNetwork
from cloudbridge.cloud.base.resources import BasePlacementZone
from cloudbridge.cloud.base.resources import BaseRegion
from cloudbridge.cloud.base.resources import BaseSecurityGroup
from cloudbridge.cloud.base.resources import BaseSecurityGroupRule
from cloudbridge.cloud.interfaces.resources import MachineImageState

# Older versions of Python do not have a built-in set data-structure.
try:
    set
except NameError:
    from sets import Set as set

import hashlib
import inspect
import json
import re

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
    def id(self):
        return str(self._inst_dict.get('id'))

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
        zones_response = self._provider.gce_compute.zones().list(
            project=self._provider.project_name).execute()
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
    def tag_network_id(tag, network):
        """
        Generate an ID for a (tag, network) pair.
        """
        md5 = hashlib.md5()
        md5.update("{0}-{1}".format(tag, network).encode('ascii'))
        return md5.hexdigest()

    @staticmethod
    def network(firewall):
        """
        Extract the network name of a firewall.
        """
        if 'network' not in firewall:
            return GCEFirewallsDelegate.DEFAULT_NETWORK
        match = re.search(
                GCEFirewallsDelegate._NETWORK_URL_PREFIX + '([^/]*)$',
                firewall['network'])
        if match and len(match.groups()) == 1:
            return match.group(1)
        return None

    @property
    def provider(self):
        return self._provider

    @property
    def tag_networks(self):
        """
        List all (tag, network) pairs that are used in at least one firewall.
        """
        out = set()
        for firewall in self.iter_firewalls():
            network = GCEFirewallsDelegate.network(firewall)
            if network is not None:
                out.add((firewall['targetTags'][0], network))
        return out
            
    def get_tag_network_from_id(self, tag_network_id):
        """
        Map an ID back to the (tag, network) pair.
        """
        for tag, network in self.tag_networks:
            current_id = GCEFirewallsDelegate.tag_network_id(tag, network)
            if current_id == tag_network_id:
                return (tag, network)
        return (None, None)

    def delete_tag_network_with_id(self, tag_network_id):
        """
        Delete all firewalls in a given network with a specific target tag.
        """
        tag, network = self.get_tag_network_from_id(tag_network_id)
        if tag is None:
            return
        for firewall in self.iter_firewalls(tag, network):
            self._delete_firewall(firewall)
        self._update_list_response()

    def add_firewall(self, tag, ip_protocol, port, source_range, source_tag,
                     description, network):
        """
        Create a new firewall.
        """
        if self.find_firewall(tag, ip_protocol, port, source_range,
                              source_tag, network) is not None:
            return True
        # Do not let the user accidentally open traffic from the world by not
        # explicitly specifying the source.
        if source_tag is None and source_range is None:
            return False
        firewall_number = 1
        suffixes = []
        for firewall in self.iter_firewalls(tag, network):
            suffix = firewall['name'].split('-')[-1]
            if suffix.isdigit():
                suffixes.append(int(suffix))
        for suffix in sorted(suffixes):
            if firewall_number == suffix:
                firewall_number += 1
        firewall = {
            'name': '%s-%s-rule-%d' % (network, tag, firewall_number),
            'network': GCEFirewallsDelegate._NETWORK_URL_PREFIX + network,
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
            response = (self._provider.gce_compute
                                      .firewalls()
                                      .insert(project=project_name,
                                              body=firewall)
                                      .execute())
            self._provider.wait_for_global_operation(response)
            # TODO: process the response and handle errors.
            return True
        except:
            return False
        finally:
            self._update_list_response()

    def find_firewall(self, tag, ip_protocol, port, source_range, source_tag,
                      network):
        """
        Find a firewall with give parameters.
        """
        if source_range is None and source_tag is None:
            source_range = '0.0.0.0/0'
        for firewall in self.iter_firewalls(tag, network):
            if firewall['allowed'][0]['IPProtocol'] != ip_protocol:
                continue
            if not self._check_list_in_dict(firewall['allowed'][0], 'ports',
                                            port):
                continue
            if not self._check_list_in_dict(firewall, 'sourceRanges',
                                            source_range):
                continue
            if not self._check_list_in_dict(firewall, 'sourceTags', source_tag):
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
            info['network'] = GCEFirewallsDelegate.network(firewall)
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

    def iter_firewalls(self, tag=None, network=None):
        """
        Iterate through all firewalls. Can optionally iterate through firewalls
        with a given tag and/or in a network.
        """
        if self._list_response is None:
            self._update_list_response()
        if 'items' not in self._list_response:
            return
        for firewall in self._list_response['items']:
            if 'targetTags' not in firewall or len(firewall['targetTags']) != 1:
                continue
            if 'allowed' not in firewall or len(firewall['allowed']) != 1:
                continue
            if tag is not None and firewall['targetTags'][0] != tag:
                continue
            if network is None:
                yield firewall
                continue
            firewall_network = GCEFirewallsDelegate.network(firewall)
            if firewall_network == network:
                yield firewall

    def _delete_firewall(self, firewall):
        """
        Delete a given firewall.
        """
        project_name = self._provider.project_name
        try:
            response = (self._provider.gce_compute
                                      .firewalls()
                                      .delete(project=project_name,
                                              firewall=firewall['name'])
                                      .execute())
            self._provider.wait_for_global_operation(response)
            # TODO: process the response and handle errors.
            return True
        except:
            return False

    def _update_list_response(self):
        """
        Sync the local cache of all firewalls with the server.
        """
        self._list_response = (
                self._provider.gce_compute
                              .firewalls()
                              .list(project=self._provider.project_name)
                              .execute())

    def _check_list_in_dict(self, dictionary, field_name, value):
        """
        Verify that a given field in a dictionary is a singlton list [value].
        """
        if field_name not in dictionary:
            return value is None
        if (value is None or
            len(dictionary[field_name]) != 1 or
            dictionary[field_name][0] != value):
            return False
        return True


class GCESecurityGroup(BaseSecurityGroup):

    def __init__(self, delegate, tag,
                 network=GCEFirewallsDelegate.DEFAULT_NETWORK,
                 description=None):
        super(GCESecurityGroup, self).__init__(delegate.provider, tag)
        self._description = description
        self._delegate = delegate
        self._network = network
        if self._network is None:
            self._network = GCEFirewallsDelegate.DEFAULT_NETWORK 

    @property
    def id(self):
        """
        Return the ID of this security group which is determined based on the
        network and the target tag corresponding to this security group.
        """
        return GCEFirewallsDelegate.tag_network_id(self._security_group,
                                                   self._network)

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
                                                      self._network):
            if 'description' in firewall:
                return firewall['description']
        return None

    @property
    def rules(self):
        out = []
        for firewall in self._delegate.iter_firewalls(self._security_group,
                                                      self._network):
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
                                    self._network)
        return self.get_rule(ip_protocol, from_port, to_port, cidr_ip,
                             src_group)

    def get_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        port = GCESecurityGroup.to_port_range(from_port, to_port)
        src_tag = src_group.name if src_group is not None else None
        firewall_id = self._delegate.find_firewall(
                self._security_group, ip_protocol, port, cidr_ip, src_tag,
                self._network)
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
        if info is None or 'target_tag' not in info or info['network'] is None:
            return None
        return GCESecurityGroup(self._delegate, info['target_tag'],
                                info['network'])

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
        if info is None or 'source_tag' not in info or info['network'] is None:
            return None
        return GCESecurityGroup(self._delegate, info['source_tag'],
                                info['network'])

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
    def id(self):
        """
        Get the image identifier.
        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        return self._gce_image['name']

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

    def delete(self):
        """
        Delete this image
        """
        request = self._provider.gce_compute.images().delete(
            project=self._provider.project_name, image=self.name)
        request.execute()

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
            response = self._provider.gce_compute \
                                  .images() \
                                  .get(project=project,
                                       image=self.name) \
                                  .execute()
            if response:
                # pylint:disable=protected-access
                self._gce_image = response
        except googleapiclient.errors.HttpError as http_error:
            # image no longer exists
            cb.log.warning(
                "googleapiclient.errors.HttpError: {0}".format(http_error))
            self._gce_image['status'] = "unknown"


class GCENetwork(BaseNetwork):

    def __init__(self, provider, network):
        super(GCENetwork, self).__init__(provider)
        self._network = network

    @property
    def id(self):
        return self._network['id']

    @property
    def name(self):
        return self._network['name']

    @property
    def external(self):
        raise NotImplementedError("To be implemented")

    @property
    def state(self):
        raise NotImplementedError("To be implemented")

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
            self._provider.wait_for_global_operation(response)
            return True
        except:
            return False

    def subnets(self):
        raise NotImplementedError("To be implemented")

    def create_subnet(self, cidr_block, name=None):
        raise NotImplementedError("To be implemented")

    def refresh(self):
        return self.state
