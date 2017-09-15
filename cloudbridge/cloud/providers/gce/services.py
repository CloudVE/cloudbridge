import hashlib
import uuid
from collections import namedtuple

import cloudbridge as cb
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.resources import ServerPagedResultList
from cloudbridge.cloud.base.services import BaseBlockStoreService
from cloudbridge.cloud.base.services import BaseComputeService
from cloudbridge.cloud.base.services import BaseImageService
from cloudbridge.cloud.base.services import BaseInstanceService
from cloudbridge.cloud.base.services import BaseInstanceTypesService
from cloudbridge.cloud.base.services import BaseKeyPairService
from cloudbridge.cloud.base.services import BaseNetworkService
from cloudbridge.cloud.base.services import BaseObjectStoreService
from cloudbridge.cloud.base.services import BaseRegionService
from cloudbridge.cloud.base.services import BaseSecurityGroupService
from cloudbridge.cloud.base.services import BaseSecurityService
from cloudbridge.cloud.base.services import BaseSnapshotService
from cloudbridge.cloud.base.services import BaseSubnetService
from cloudbridge.cloud.base.services import BaseVolumeService
from cloudbridge.cloud.interfaces.resources import PlacementZone
from cloudbridge.cloud.interfaces.resources import SecurityGroup
from cloudbridge.cloud.providers.gce import helpers

import googleapiclient

from retrying import retry

from .resources import GCEFirewallsDelegate
from .resources import GCEFloatingIP
from .resources import GCEInstance
from .resources import GCEInstanceType
from .resources import GCEKeyPair
from .resources import GCEMachineImage
from .resources import GCENetwork
from .resources import GCEPlacementZone
from .resources import GCERegion
from .resources import GCERouter
from .resources import GCESecurityGroup
from .resources import GCESnapshot
from .resources import GCESubnet
from .resources import GCEVolume
from .resources import GCSBucket


class GCESecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(GCESecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = GCEKeyPairService(provider)
        self._security_groups = GCESecurityGroupService(provider)

    @property
    def key_pairs(self):
        return self._key_pairs

    @property
    def security_groups(self):
        return self._security_groups


class GCEKeyPairService(BaseKeyPairService):

    GCEKeyInfo = namedtuple('GCEKeyInfo', 'format public_key email')

    def __init__(self, provider):
        super(GCEKeyPairService, self).__init__(provider)
        self._gce_projects = None

    @property
    def gce_projects(self):
        if not self._gce_projects:
            self._gce_projects = self.provider.gce_compute.projects()
        return self._gce_projects

    def get(self, key_pair_id):
        """
        Returns a KeyPair given its ID.
        """
        for kp in self.list():
            if kp.id == key_pair_id:
                return kp
        else:
            return None

    def _iter_gce_key_pairs(self):
        """
        Iterates through the project's metadata, yielding a GCEKeyInfo object
        for each entry in commonInstanceMetaData/items
        """
        metadata = self._get_common_metadata()
        for kpinfo in self._iter_gce_ssh_keys(metadata):
            yield kpinfo

    def _get_common_metadata(self):
        """
        Get a project's commonInstanceMetadata entry
        """
        metadata = self.gce_projects.get(
            project=self.provider.project_name).execute()
        return metadata["commonInstanceMetadata"]

    def _get_or_add_sshkey_entry(self, metadata):
        """
        Get the sshKeys entry from commonInstanceMetadata/items.
        If an entry does not exist, adds a new empty entry
        """
        sshkey_entry = None
        entries = [item for item in metadata["items"]
                   if item["key"] == "sshKeys"]
        if entries:
            sshkey_entry = entries[0]
        else:  # add a new entry
            sshkey_entry = {"key": "sshKeys", "value": ""}
            metadata["items"].append(sshkey_entry)
        return sshkey_entry

    def _iter_gce_ssh_keys(self, metadata):
        """
        Iterates through the ssh keys given a commonInstanceMetadata dict,
        yielding a GCEKeyInfo object for each entry in
        commonInstanceMetaData/items
        """
        sshkeys = self._get_or_add_sshkey_entry(metadata)["value"]
        for key in sshkeys.split("\n"):
            # elems should be "ssh-rsa <public_key> <email>"
            elems = key.split(" ")
            if elems and elems[0]:  # ignore blank lines
                yield GCEKeyPairService.GCEKeyInfo(
                        elems[0], elems[1].encode('ascii'), elems[2])

    def gce_metadata_save_op(self, callback):
        """
        Carries out a metadata save operation. In GCE, a fingerprint based
        locking mechanism is used to prevent lost updates. A new fingerprint
        is returned each time metadata is retrieved. Therefore, this method
        retrieves the metadata, invokes the provided callback with that
        metadata, and saves the metadata using the original fingerprint
        immediately afterwards, ensuring that update conflicts can be detected.
        """
        def _save_common_metadata():
            metadata = self._get_common_metadata()
            # add a new entry if one doesn'te xist
            sshkey_entry = self._get_or_add_sshkey_entry(metadata)
            gce_kp_list = callback(self._iter_gce_ssh_keys(metadata))

            entry = ""
            for gce_kp in gce_kp_list:
                entry = entry + u"{0} {1} {2}\n".format(gce_kp.format,
                                                        gce_kp.public_key,
                                                        gce_kp.email)
            sshkey_entry["value"] = entry.rstrip()
            # common_metadata will have the current fingerprint at this point
            operation = self.gce_projects.setCommonInstanceMetadata(
                project=self.provider.project_name, body=metadata).execute()
            self.provider.wait_for_operation(operation)

        # Retry a few times if the fingerprints conflict
        retry_decorator = retry(stop_max_attempt_number=5)
        retry_decorator(_save_common_metadata)()

    def gce_kp_to_id(self, gce_kp):
        """
        Accept a GCEKeyInfo object and return a unique
        ID for it
        """
        md5 = hashlib.md5()
        md5.update(gce_kp.public_key)
        return md5.hexdigest()

    def list(self, limit=None, marker=None):
        key_pairs = []
        for gce_kp in self._iter_gce_key_pairs():
            kp_id = self.gce_kp_to_id(gce_kp)
            kp_name = gce_kp.email
            key_pairs.append(GCEKeyPair(self.provider, kp_id, kp_name))
        return ClientPagedResultList(self.provider, key_pairs,
                                     limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        """
        Searches for a key pair by a given list of attributes.
        """
        found_kps = []
        for kp in self.list():
            if kp.name == name:
                found_kps.append(kp)
        return ClientPagedResultList(self.provider, found_kps,
                                     limit=limit, marker=marker)

    def create(self, name):
        kp = self.find(name=name)
        if kp:
            return kp

        private_key, public_key = helpers.generate_key_pair()
        kp_info = GCEKeyPairService.GCEKeyInfo(name + u":ssh-rsa",
                                               public_key, name)

        def _add_kp(gce_kp_generator):
            kp_list = []
            # Add the new key pair
            kp_list.append(kp_info)
            for gce_kp in gce_kp_generator:
                kp_list.append(gce_kp)
            return kp_list

        self.gce_metadata_save_op(_add_kp)
        return GCEKeyPair(self.provider, self.gce_kp_to_id(kp_info), name,
                          kp_material=private_key)


class GCESecurityGroupService(BaseSecurityGroupService):

    def __init__(self, provider):
        super(GCESecurityGroupService, self).__init__(provider)
        self._delegate = GCEFirewallsDelegate(provider)

    def get(self, group_id):
        tag, network_name = self._delegate.get_tag_network_from_id(group_id)
        if tag is None:
            return None
        network = self.provider.network.get_by_name(network_name)
        return GCESecurityGroup(self._delegate, tag, network)

    def list(self, limit=None, marker=None):
        security_groups = []
        for tag, network_name in self._delegate.tag_networks:
            network = self.provider.network.get_by_name(network_name)
            security_group = GCESecurityGroup(self._delegate, tag, network)
            security_groups.append(security_group)
        return ClientPagedResultList(self.provider, security_groups,
                                     limit=limit, marker=marker)

    def create(self, name, description, network_id=None):
        network = self.provider.network.get(network_id)
        return GCESecurityGroup(self._delegate, name, network, description)

    def find(self, name, limit=None, marker=None):
        """
        Finds a non-empty security group. If a security group with the given
        name does not exist, or if it does not contain any rules, an empty list
        is returned.
        """
        out = []
        for tag, network_name in self._delegate.tag_networks:
            if tag == name:
                network = self.provider.network.get_by_name(network_name)
                out.append(GCESecurityGroup(self._delegate, name, network))
        return out

    def delete(self, group_id):
        return self._delegate.delete_tag_network_with_id(group_id)

    def find_by_network_and_tags(self, network_name, tags):
        """
        Finds non-empty security groups by network name and security group
        names (tags). If no matching security group is found, an empty list
        is returned.
        """
        security_groups = []
        for tag, net_name in self._delegate.tag_networks:
            if network_name != net_name:
                continue
            if tag not in tags:
                continue
            network = self.provider.network.get_by_name(net_name)
            security_groups.append(
                GCESecurityGroup(self._delegate, tag, network))
        return security_groups


class GCEInstanceTypesService(BaseInstanceTypesService):

    def __init__(self, provider):
        super(GCEInstanceTypesService, self).__init__(provider)

    @property
    def instance_data(self):
        response = (self.provider
                        .gce_compute
                        .machineTypes()
                        .list(project=self.provider.project_name,
                              zone=self.provider.default_zone)
                        .execute())
        return response['items']

    def get(self, instance_type_id):
        for inst_type in self.instance_data:
            if inst_type.get('id') == instance_type_id:
                return GCEInstanceType(self.provider, inst_type)
        return None

    def find(self, **kwargs):
        matched_inst_types = []
        for inst_type in self.instance_data:
            is_match = True
            for key, value in kwargs.iteritems():
                if key not in inst_type:
                    raise TypeError("The attribute key is not valid.")
                if inst_type.get(key) != value:
                    is_match = False
                    break
            if is_match:
                matched_inst_types.append(
                    GCEInstanceType(self.provider, inst_type))
        return matched_inst_types

    def list(self, limit=None, marker=None):
        inst_types = [GCEInstanceType(self.provider, inst_type)
                      for inst_type in self.instance_data]
        return ClientPagedResultList(self.provider, inst_types,
                                     limit=limit, marker=marker)


class GCERegionService(BaseRegionService):

    def __init__(self, provider):
        super(GCERegionService, self).__init__(provider)

    def get(self, region_id):
        try:
            region = (self.provider
                          .gce_compute
                          .regions()
                          .get(project=self.provider.project_name,
                               region=region_id)
                          .execute())
        # Handle the case when region_id is not valid
        except googleapiclient.errors.HttpError:
            return None
        if region:
            return GCERegion(self.provider, region)
        else:
            return None

    def list(self, limit=None, marker=None):
        max_result = limit if limit is not None and limit < 500 else 500
        regions_response = (self.provider
                                .gce_compute
                                .regions()
                                .list(project=self.provider.project_name,
                                      maxResults=max_result,
                                      pageToken=marker)
                                .execute())
        regions = [GCERegion(self.provider, region)
                   for region in regions_response['items']]
        if len(regions) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(regions))
        return ServerPagedResultList('nextPageToken' in regions_response,
                                     regions_response.get('nextPageToken'),
                                     False, data=regions)

    @property
    def current(self):
        return self.get(self.provider.region_name)


class GCEImageService(BaseImageService):

    def __init__(self, provider):
        super(GCEImageService, self).__init__(provider)
        self._public_images = None

    _PUBLIC_IMAGE_PROJECTS = ['centos-cloud', 'coreos-cloud', 'debian-cloud',
                              'opensuse-cloud', 'ubuntu-os-cloud']

    def _retrieve_public_images(self):
        if self._public_images is not None:
            return
        self._public_images = []
        try:
            for project in GCEImageService._PUBLIC_IMAGE_PROJECTS:
                for image in helpers.iter_all(
                        self.provider.gce_compute.images(), project=project):
                    self._public_images.append(
                        GCEMachineImage(self.provider, image))
        except googleapiclient.errors.HttpError as http_error:
                cb.log.warning("googleapiclient.errors.HttpError: {0}".format(
                    http_error))

    def get(self, image_id):
        """
        Returns an Image given its id
        """
        try:
            image = (self.provider
                         .gce_compute
                         .images()
                         .get(project=self.provider.project_name,
                              image=image_id)
                         .execute())
            if image:
                return GCEMachineImage(self.provider, image)
        except TypeError as type_error:
            # The API will throw an TypeError, if parameter `image` does not
            # match the pattern "[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?".
            cb.log.warning("TypeError: {0}".format(type_error))
        except googleapiclient.errors.HttpError as http_error:
            # If the image is not found in project-specific private images,
            # look for this image in public images.
            self._retrieve_public_images()
            for public_image in self._public_images:
                if public_image.id == image_id:
                    return public_image
            cb.log.warning(
                "googleapiclient.errors.HttpError: {0}".format(http_error))
        return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for an image by a given list of attributes
        """
        filters = {'name': name}
        # Retrieve all available images by setting limit to sys.maxsize
        images = [image for image in self if image.name == filters['name']]
        return ClientPagedResultList(self.provider, images,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all images.
        """
        self._retrieve_public_images()
        images = []
        if (self.provider.project_name not in
                GCEImageService._PUBLIC_IMAGE_PROJECTS):
            try:
                for image in helpers.iter_all(
                        self.provider.gce_compute.images(),
                        project=self.provider.project_name):
                    images.append(GCEMachineImage(self.provider, image))
            except googleapiclient.errors.HttpError as http_error:
                cb.log.warning(
                    "googleapiclient.errors.HttpError: {0}".format(http_error))
        images.extend(self._public_images)
        return ClientPagedResultList(self.provider, images,
                                     limit=limit, marker=marker)


class GCEInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(GCEInstanceService, self).__init__(provider)

    def create(self, name, image, instance_type, subnet, zone=None,
               key_pair=None, security_groups=None, user_data=None,
               launch_config=None, **kwargs):
        """
        Creates a new virtual machine instance.
        """
        if not zone:
            zone = self.provider.default_zone
        if not launch_config:
            if subnet:
                network = self.provider.network.get(subnet.network_id)
                network_url = (network.resource_url
                               if isinstance(network, GCENetwork) else network)
            else:
                network_url = 'global/networks/default'
            config = {
                'name': name,
                'machineType': instance_type.resource_url,
                'disks': [{'boot': True,
                           'autoDelete': True,
                           'initializeParams': {
                               'sourceImage': image.resource_url,
                           }
                           }],
                'networkInterfaces': [
                    {
                        # TODO: Should replace network below with subnetwork
                        'network': network_url,
                        'accessConfigs': [{'type': 'ONE_TO_ONE_NAT',
                                           'name': 'External NAT'}]
                    }],
            }
            if security_groups and isinstance(security_groups, list):
                sg_names = []
                if isinstance(security_groups[0], SecurityGroup):
                    sg_names = [sg.name for sg in security_groups]
                elif isinstance(security_groups[0], str):
                    sg_names = security_groups
                if len(sg_names) > 0:
                    config['tags'] = {}
                    config['tags']['items'] = sg_names
        else:
            config = launch_config
        operation = (self.provider
                         .gce_compute.instances()
                         .insert(project=self.provider.project_name,
                                 zone=self.provider.default_zone,
                                 body=config)
                         .execute())
        if 'zone' not in operation:
            return None
        gce_zone = self.provider.get_gce_resource_data(operation['zone'])
        instance_id = operation.get('targetLink')
        self.provider.wait_for_operation(operation, zone=gce_zone.get('name'))
        return self.get(instance_id)

    def get(self, instance_id):
        """
        Returns an instance given its name. Returns None
        if the object does not exist.

        A GCE instance is uniquely identified by its selfLink, which is used
        as its id.
        """
        try:
            response = self.provider.get_gce_resource_data(instance_id)
            if response:
                return GCEInstance(self.provider, response)
        except googleapiclient.errors.HttpError as http_error:
            # If the instance is not found, the API will raise
            # googleapiclient.errors.HttpError.
            cb.log.warning(
                "googleapiclient.errors.HttpError: {0}".format(http_error))
        return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for instances by instance name.
        :return: a list of Instance objects
        """
        instances = [instance for instance in self.list()
                     if instance.name == name]
        if limit and len(instances) > limit:
            instances = instances[:limit]
        return instances

    def list(self, limit=None, marker=None):
        """
        List all instances.
        """
        # For GCE API, Acceptable values are 0 to 500, inclusive.
        # (Default: 500).
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .instances()
                        .list(project=self.provider.project_name,
                              zone=self.provider.default_zone,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        instances = []
        if 'items' in response:
            instances = [GCEInstance(self.provider, inst)
                         for inst in response['items']]
        if len(instances) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(instances))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=instances)


class GCEComputeService(BaseComputeService):
    # TODO: implement GCEComputeService
    def __init__(self, provider):
        super(GCEComputeService, self).__init__(provider)
        self._instance_svc = GCEInstanceService(self.provider)
        self._instance_type_svc = GCEInstanceTypesService(self.provider)
        self._region_svc = GCERegionService(self.provider)
        self._images_svc = GCEImageService(self.provider)

    @property
    def images(self):
        return self._images_svc

    @property
    def instance_types(self):
        return self._instance_type_svc

    @property
    def instances(self):
        return self._instance_svc

    @property
    def regions(self):
        return self._region_svc


class GCENetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(GCENetworkService, self).__init__(provider)
        self._subnet_svc = GCESubnetService(self.provider)

    def get(self, network_id):
        if network_id is None:
            return None
        # Note: networks = self.list(filter='id eq %s' % network_id) does not
        # work due to a GCE API bug that causes an error if the network_id has
        # has more than 19 digits.
        networks = self.list()
        for network in networks:
            if network.id == network_id:
                return network
        return None

    def get_by_name(self, network_name):
        if network_name is None:
            return None
        networks = self.list(filter='name eq %s' % network_name)
        return None if len(networks) == 0 else networks[0]

    def list(self, limit=None, marker=None, filter=None):
        try:
            response = (self.provider
                            .gce_compute
                            .networks()
                            .list(project=self.provider.project_name,
                                  filter=filter)
                            .execute())
            networks = []
            if 'items' in response:
                for network in response['items']:
                    networks.append(GCENetwork(self.provider, network))
            return networks
        except:
            return []

    def _create(self, name, autoCreateSubnetworks):
        """
        Possible values for 'autoCreateSubnetworks' are:

        None: For creating a legacy (non-subnetted) network.
        True: For creating an auto mode VPC network. This also creates a
              subnetwork in every region.
        False: For creating a custom mode VPC network. Subnetworks should be
               created manually.
        """
        networks = self.list(filter='name eq %s' % name)
        if len(networks) > 0:
            return networks[0]
        body = {'name': name,
                'autoCreateSubnetworks': autoCreateSubnetworks}
        try:
            response = (self.provider
                            .gce_compute
                            .networks()
                            .insert(project=self.provider.project_name,
                                    body=body)
                            .execute())
            if 'error' in response:
                return None
            self.provider.wait_for_operation(response)
            networks = self.list(filter='name eq %s' % name)
            return None if len(networks) == 0 else networks[0]
        except:
            return None

    def create(self, name):
        """
        Creates a custom mode VPC network.
        """
        return self._create(name, False)

    def get_or_create_default(self):
        return self._create(GCEFirewallsDelegate.DEFAULT_NETWORK, True)

    @property
    def subnets(self):
        return self._subnet_svc

    def floating_ips(self, network_id=None, region=None):
        if not region:
            region = self.provider.region_name
        try:
            ips = []
            for ip in helpers.iter_all(self.provider.gce_compute.addresses(),
                                       project=self.provider.project_name,
                                       region=region):
                ips.append(GCEFloatingIP(self.provider, ip))
            # TODO: if network_id is given, filter out IPs that are assigned to
            # resources in a different network.
            return ips
        except:
            return []

    def create_floating_ip(self, region=None):
        if not region:
            region = self.provider.region_name
        ip_name = 'ip-{0}'.format(uuid.uuid4())
        try:
            response = (self.provider
                            .gce_compute
                            .addresses()
                            .insert(project=self.provider.project_name,
                                    region=region,
                                    body={'name': ip_name})
                            .execute())
            if 'error' in response:
                return None
            self.provider.wait_for_operation(response, region=region)
            ips = self.floating_ips()
            for ip in ips:
                if ip.id == response['targetId']:
                    return ip
        except:
            return None

    def routers(self, region=None):
        if not region:
            region = self.provider.region_name
        try:
            routers = []
            for router in helpers.iter_all(self.provider.gce_compute.routers(),
                                           project=self.provider.project_name,
                                           region=region):
                routers.append(GCERouter(self.provider, router))
            return routers
        except:
            return []

    def create_router(self, name=None, network=None, region=None):
        network_url = 'global/networks/default'
        if isinstance(network, GCENetwork):
            network_url = network.resource_url
        if not region:
            region = self.provider.region_name
        try:
            response = (self.provider
                            .gce_compute
                            .routers()
                            .insert(project=self.provider.project_name,
                                    region=region,
                                    body={'name': name,
                                          'network': network_url})
                            .execute())
            if 'error' in response:
                return None
            self.provider.wait_for_operation(response, region=region)
            routers = self.routers()
            for router in routers:
                if router.id == response['targetId']:
                    return router
        except:
            return None


class GCESubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(GCESubnetService, self).__init__(provider)

    def get(self, subnet_id):
        for subnet in self.list():
            if subnet.id == subnet_id:
                return subnet
        return None

    def list(self, network=None, zone=None, limit=None, marker=None):
        region = zone.region_name if zone else self.provider.region_name
        filter = None
        if network is not None:
            filter = 'network eq %s' % network.resource_url
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .subnetworks()
                        .list(project=self.provider.project_name,
                              region=region,
                              filter=filter,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        subnets = []
        for subnet in response.get('items', []):
            subnets.append(GCESubnet(self.provider, subnet))
        if len(subnets) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(subnets))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=subnets)

    def create(self, network, cidr_block, name=None, zone=None):
        """
        GCE subnets are regional. The region is inferred from the zone if a
        zone is provided; otherwise, the default region, as set in the
        provider, is used.
        """
        if not name:
            name = 'subnet-{0}'.format(uuid.uuid4())
        if region is not None and zone is not None:
            cb.log.warning('Both parameters "zone" and "region" are provided')
        if region is None:
            region = self.provider.region_name
        if isinstance(zone, GCEPlacementZone):
            region = zone.region_name
        body = {'ipCidrRange': cidr_block,
                'name': name,
                'network': network.resource_url,
                'region': region}
        try:
            response = (self.provider
                            .gce_compute
                            .subnetworks()
                            .insert(project=self.provider.project_name,
                                    region=region,
                                    body=body)
                            .execute())
            self.provider.wait_for_operation(response, region=region)
            if 'error' in response:
                return None
            subnets = self.list(network, region)
            for subnet in subnets:
                if subnet.id == response['targetId']:
                    return subnet
        except:
            return None

    def get_or_create_default(self, zone=None):
        """
        Every GCP project comes with a default auto mode VPC network. An auto
        mode VPC network has exactly one subnetwork per region. This method
        returns the subnetwork of the default network that spans the given
        zone.
        """
        network = self.provider.network.get_or_create_default()
        subnets = self.list(network, zone)
        if len(subnets) > 1:
            cb.log.warning('The default network has more than one subnetwork '
                           'in a region')
        if len(subnets) > 0:
            return subnets[0]
        cb.log.warning('The default network has no subnetwork in a region')
        return None

    def delete(self, subnet):
        response = (self.provider
                        .gce_compute
                        .subnetworks()
                        .delete(project=self.provider.project_name,
                                region=subnet.region,
                                router=subnet.name)
                        .execute())
        self._provider.wait_for_operation(response, region=subnet.region)


class GCEBlockStoreService(BaseBlockStoreService):

    def __init__(self, provider):
        super(GCEBlockStoreService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = GCEVolumeService(self.provider)
        self._snapshot_svc = GCESnapshotService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc


class GCEVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(GCEVolumeService, self).__init__(provider)

    def get(self, volume_id):
        """
        Returns a volume given its id.
        """
        try:
            response = self.provider.get_gce_resource_data(volume_id)
            if response:
                return GCEVolume(self.provider, response)
        except googleapiclient.errors.HttpError as http_error:
            # If the volume is not found, the API will raise
            # googleapiclient.errors.HttpError.
            cb.log.warning(
                "googleapiclient.errors.HttpError: {0}".format(http_error))
        return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a volume by a given list of attributes.
        """
        filtr = 'name eq ' + name
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .disks()
                        .list(project=self.provider.project_name,
                              zone=self.provider.default_zone,
                              filter=filtr,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        if 'items' not in response:
            return []
        gce_vols = [GCEVolume(self.provider, vol)
                    for vol in response['items']]
        if len(gce_vols) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(gce_vols))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=gce_vols)

    def list(self, limit=None, marker=None):
        """
        List all volumes.

        limit: The maximum number of volumes to return. The returned
               ResultList's is_truncated property can be used to determine
               whether more records are available.
        """
        # For GCE API, Acceptable values are 0 to 500, inclusive.
        # (Default: 500).
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .disks()
                        .list(project=self.provider.project_name,
                              zone=self.provider.default_zone,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        if 'items' not in response:
            return []
        gce_vols = [GCEVolume(self.provider, vol)
                    for vol in response['items']]
        if len(gce_vols) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(gce_vols))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=gce_vols)

    def create(self, name, size, zone, snapshot=None, description=None):
        """
        Creates a new volume.

        Argument `name` must be 1-63 characters long, and comply with RFC1035.
        Specifically, the name must be 1-63 characters long and match the
        regular expression [a-z]([-a-z0-9]*[a-z0-9])? which means the first
        character must be a lowercase letter, and all following characters must
        be a dash, lowercase letter, or digit, except the last character, which
        cannot be a dash.
        """
        zone_name = zone.name if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.id if isinstance(
            snapshot, GCESnapshot) and snapshot else snapshot
        disk_body = {
            'name': name,
            'sizeGb': size,
            'type': 'zones/{0}/diskTypes/{1}'.format(zone_name, 'pd-standard'),
            'sourceSnapshot': snapshot_id,
            'description': description,
        }
        operation = (self.provider
                         .gce_compute
                         .disks()
                         .insert(
                             project=self._provider.project_name,
                             zone=zone_name,
                             body=disk_body)
                         .execute())
        return self.get(operation.get('targetLink'))


class GCESnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(GCESnapshotService, self).__init__(provider)

    def get(self, snapshot_id):
        """
        Returns a snapshot given its id.
        """
        try:
            response = self.provider.get_gce_resource_data(snapshot_id)
            if response:
                return GCESnapshot(self.provider, response)
        except googleapiclient.errors.HttpError as http_error:
            # If the volume is not found, the API will raise
            # googleapiclient.errors.HttpError.
            cb.log.warning(
                "googleapiclient.errors.HttpError: {0}".format(http_error))
        return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a snapshot by a given list of attributes.
        """
        filtr = 'name eq ' + name
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .snapshots()
                        .list(project=self.provider.project_name,
                              filter=filtr,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        if 'items' not in response:
            return []
        snapshots = [GCESnapshot(self.provider, snapshot)
                     for snapshot in response['items']]
        if len(snapshots) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(snapshots))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=snapshots)

    def list(self, limit=None, marker=None):
        """
        List all snapshots.
        """
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .snapshots()
                        .list(project=self.provider.project_name,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        if 'items' not in response:
            return []
        snapshots = [GCESnapshot(self.provider, snapshot)
                     for snapshot in response['items']]
        if len(snapshots) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(snapshots))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=snapshots)

    def create(self, name, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        volume_name = volume.name if isinstance(volume, GCEVolume) else volume
        snapshot_body = {
            "name": name,
            "description": description
        }
        operation = (self.provider
                         .gce_compute
                         .disks()
                         .createSnapshot(
                             project=self.provider.project_name,
                             zone=self.provider.default_zone,
                             disk=volume_name, body=snapshot_body)
                         .execute())
        if 'zone' not in operation:
            return None
        gce_zone = self.provider.get_gce_resource_data(operation['zone'])
        self.provider.wait_for_operation(operation, zone=gce_zone.get('name'))
        snapshots = self.provider.block_store.snapshots.find(name=name)
        if snapshots:
            return snapshots[0]
        else:
            return None


class GCSObjectStoreService(BaseObjectStoreService):

    def __init__(self, provider):
        super(GCSObjectStoreService, self).__init__(provider)

    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist or if the user does not have permission to access the
        bucket.
        """
        try:
            response = (self.provider
                            .gcp_storage
                            .buckets()
                            .get(bucket=bucket_id)
                            .execute())
            if 'error' in response:
                # response['error']['code'] is 404 if the bucket does not exist
                # and 403 if the user does not have permission to access it.
                if response['error']['code'] not in (403, 404):
                    cb.log.warning('Unexpected error code (%d) when accessing '
                                   'bucket %s', response['error']['code'],
                                   bucket_id)
                return None
            return GCSBucket(self.provider, response)
        except:
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches in bucket names for a substring.
        """
        buckets = [bucket for bucket in self if name in bucket.name]
        return ClientPagedResultList(self.provider, buckets, limit=limit,
                                     marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all containers.
        """
        max_result = limit if limit is not None and limit < 500 else 500
        try:
            response = (self.provider
                            .gcp_storage
                            .buckets()
                            .list(project=self.provider.project_name,
                                  maxResults=max_result,
                                  pageToken=marker)
                            .execute())
            if 'error' in response:
                return ServerPagedResultList(False, None, False, data=[])
            buckets = []
            for bucket in response.get('items', []):
                buckets.append(GCSBucket(self.provider, bucket))
            if len(buckets) > max_result:
                cb.log.warning('Expected at most %d results; got %d',
                               max_result, len(buckets))
            return ServerPagedResultList('nextPageToken' in response,
                                         response.get('nextPageToken'),
                                         False, data=buckets)
        except:
            return ServerPagedResultList(False, None, False, data=[])

    def create(self, name, location=None):
        """
        Create a new bucket and returns it. Returns None if creation fails.
        """
        body = {'name': name}
        if location:
            body['location'] = location
        try:
            response = (self.provider
                            .gcp_storage
                            .buckets()
                            .insert(project=self.provider.project_name,
                                    body=body)
                            .execute())
            if 'error' in response:
                return None
            return GCSBucket(self.provider, response)
        except:
            return None
