"""
DataTypes used by this provider
"""
from cloudbridge.cloud.base.resources import BaseInstanceType
from cloudbridge.cloud.base.resources import BaseKeyPair
from cloudbridge.cloud.base.resources import BasePlacementZone
from cloudbridge.cloud.base.resources import BaseRegion


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
