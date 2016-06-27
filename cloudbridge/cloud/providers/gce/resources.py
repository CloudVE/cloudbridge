"""
DataTypes used by this provider
"""
from cloudbridge.cloud.base.resources import BaseInstanceType
from cloudbridge.cloud.base.resources import BaseKeyPair
from cloudbridge.cloud.base.resources import BasePlacementZone
from cloudbridge.cloud.base.resources import BaseRegion
from cloudbridge.cloud.base.resources import BaseSecurityGroup
from cloudbridge.cloud.base.resources import BaseSecurityGroupRule
from sets import Set

import hashlib
import inspect
import json

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

    _instance = None
   
    def __init__(self, provider):
        if GCEFirewallsDelegate._instance is not None:
            raise Exception('Use GCEFirewalls.instance() to instanciate.')
        self._provider = provider
        self._list_response = None
        GCEFirewallsDelegate._instance = self

    @staticmethod
    def get_instance(provider):
        if GCEFirewallsDelegate._instance is None:
            GCEFirewallsDelegate(provider)
        return GCEFirewallsDelegate._instance
 
    @staticmethod
    def tag_id(tag):
        md5 = hashlib.md5()
        md5.update(tag.encode('ascii'))
        return md5.hexdigest()

    @property
    def tags(self):
        out = Set()
        for firewall in self.iter_firewalls():
            out.add(firewall['targetTags'][0])
        return out
            
    def get_tag_from_id(self, tag_id):
        for tag in self.tags:
            if GCEFirewallsDelegate.tag_id(tag) == tag_id:
                return tag
        return None

    def has_tag(self, tag):
        return tag in self.tags

    def delete_tag_with_id(self, tag_id):
        tag = self.get_tag_from_id(tag_id)
        if tag is None:
            return
        for firewall in self.iter_firewalls(tag):
            self._delete_firewall(firewall)
        self._update_list_response()

    def add_firewall(self, tag, ip_protocol, port, source_range, source_tag,
                     description):
        if self.find_firewall(tag, ip_protocol, port, source_range,
                              source_tag) is not None:
            return True
        firewall_number = 1
        suffixes = []
        for firewall in self.iter_firewalls(tag):
            suffix = firewall['name'].split('-')[-1]
            if suffix.isdigit():
                suffixes.append(int(suffix))
        for suffix in sorted(suffixes):
            if firewall_number == suffix:
                firewall_number += 1
        firewall = {'name': '%s-rule-%d' % (tag, firewall_number),
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

    def find_firewall(self, tag, ip_protocol, port, source_range, source_tag):
        if source_range is None and source_tag is None:
            source_range = '0.0.0.0/0'
        for firewall in self.iter_firewalls(tag):
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
            return info
        return info

    def delete_firewall_id(self, firewall_id):
        for firewall in self.iter_firewalls():
            if firewall['id'] == firewall_id:
                self._delete_firewall(firewall)
        self._update_list_response()

    def iter_firewalls(self, tag=None):
        if self._list_response is None:
            self._update_list_response()
        if 'items' not in self._list_response:
            return
        for firewall in self._list_response['items']:
            if 'targetTags' not in firewall or len(firewall['targetTags']) != 1:
                continue
            if 'allowed' not in firewall or len(firewall['allowed']) != 1:
                continue
            if tag is None or firewall['targetTags'][0] == tag:
                yield firewall

    def _delete_firewall(self, firewall):
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
        self._list_response = (
                self._provider.gce_compute
                              .firewalls()
                              .list(project=self._provider.project_name)
                              .execute())

    def _check_list_in_dict(self, dictionary, field_name, value):
        if field_name not in dictionary:
            return value is None
        if (value is None or
            len(dictionary[field_name]) != 1 or
            dictionary[field_name][0] != value):
            return False
        return True


class GCESecurityGroup(BaseSecurityGroup):

    def __init__(self, provider, tag, description=None):
        super(GCESecurityGroup, self).__init__(provider, tag)
        self._description = description
        self._delegate = GCEFirewallsDelegate.get_instance(provider)

    @property
    def id(self):
        return GCEFirewallsDelegate.tag_id(self._security_group)

    @property
    def name(self):
        return self._security_group

    @property
    def description(self):
        if self._description is not None:
            return self._description
        for firewall in self._delegate.iter_firewalls(self._security_group):
            if 'description' in firewall:
                return firewall['description']
        return None

    @property
    def rules(self):
        out = []
        for firewall in self._delegate.iter_firewalls(self._security_group):
            out.append(GCESecurityGroupRule(self._provider, firewall['id']))
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
                                    cidr_ip, src_tag, self.description)
        return self.get_rule(ip_protocol, from_port, to_port, cidr_ip,
                             src_group)

    def get_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        port = GCESecurityGroup.to_port_range(from_port, to_port)
        src_tag = src_group.name if src_group is not None else None
        firewall_id = self._delegate.find_firewall(
                self._security_group, ip_protocol, port, cidr_ip, src_tag)
        if firewall_id is None:
            return None
        return GCESecurityGroupRule(self._provider, firewall_id)

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

    def __init__(self, provider, firewall_id):
        super(GCESecurityGroupRule, self).__init__(provider, firewall_id, None)
        self._delegate = GCEFirewallsDelegate.get_instance(provider)

    @property
    def parent(self):
        info = self._delegate.get_firewall_info(self._rule)
        if info is None or 'target_tag' not in info:
            return None
        return GCESecurityGroup(self._provider, info['target_tag'])

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
        info = self._delegate.get_firewall_info(self._rule)
        if info is None or 'source_range' not in info:
            return None
        return info['source_range']

    @property
    def group(self):
        info = self._delegate.get_firewall_info(self._rule)
        if info is None or 'source_tag' not in info:
            return None
        return GCESecurityGroup(self._provider, info['source_tag'])

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        js['group'] = self.group.id if self.group else ''
        js['parent'] = self.parent.id if self.parent else ''
        return json.dumps(js, sort_keys=True)

    def delete(self):
        self._delegate.delete_firewall_id(self._rule)
