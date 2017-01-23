from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.services import BaseComputeService
from cloudbridge.cloud.base.services import BaseImageService
from cloudbridge.cloud.base.services import BaseInstanceTypesService
from cloudbridge.cloud.base.services import BaseKeyPairService
from cloudbridge.cloud.base.services import BaseNetworkService
from cloudbridge.cloud.base.services import BaseRegionService
from cloudbridge.cloud.base.services import BaseSecurityGroupService
from cloudbridge.cloud.base.services import BaseSecurityService
from cloudbridge.cloud.providers.gce import helpers
import cloudbridge as cb

from collections import namedtuple
import hashlib
import googleapiclient

from retrying import retry
import sys

from .resources import GCEFirewallsDelegate
from .resources import GCEMachineImage
from .resources import GCENetwork
from .resources import GCEInstanceType
from .resources import GCEKeyPair
from .resources import GCERegion
from .resources import GCESecurityGroup
from .resources import GCESecurityGroupRule

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
                yield GCEKeyPairService.GCEKeyInfo(elems[0], elems[1],
                                                   elems[2])

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
            self.provider.wait_for_global_operation(operation)

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


class GCEInstanceTypesService(BaseInstanceTypesService):

    def __init__(self, provider):
        super(GCEInstanceTypesService, self).__init__(provider)

    @property
    def instance_data(self):
        response = self.provider.gce_compute \
                                .machineTypes() \
                                .list(project=self.provider.project_name,
                                      zone=self.provider.default_zone) \
                                .execute()
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
            region = self.provider.gce_compute \
                                  .regions() \
                                  .get(project=self.provider.project_name,
                                       region=region_id) \
                                  .execute()
        # Handle the case when region_id is not valid
        except googleapiclient.errors.HttpError:
            return None
        if region:
            return GCERegion(self.provider, region)
        else:
            return None

    def list(self, limit=None, marker=None):
        regions_response = self.provider.gce_compute.regions().list(
            project=self.provider.project_name).execute()
        regions = [GCERegion(self.provider, region)
                   for region in regions_response['items']]
        return ClientPagedResultList(self.provider, regions,
                                     limit=limit, marker=marker)

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
        for project in GCEImageService._PUBLIC_IMAGE_PROJECTS:
            try:
                response = self.provider.gce_compute \
                                        .images() \
                                        .list(project=project) \
                                        .execute()
            except googleapiclient.errors.HttpError as http_error:
                cb.log.warning("googleapiclient.errors.HttpError: {0}".format(
                    http_error))
            if 'items' in response:
                self._public_images.extend(
                    [GCEMachineImage(self.provider, image) for image
                     in response['items']])

    def get(self, image_id):
        """
        Returns an Image given its id
        """
        try:
            image = self.provider.gce_compute \
                                  .images() \
                                  .get(project=self.provider.project_name,
                                       image=image_id) \
                                  .execute()
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
                response = self.provider \
                               .gce_compute \
                               .images() \
                               .list(project=self.provider.project_name) \
                               .execute()
                if 'items' in response:
                    images = [GCEMachineImage(self.provider, image) for image
                              in response['items']]
            except googleapiclient.errors.HttpError as http_error:
                cb.log.warning(
                    "googleapiclient.errors.HttpError: {0}".format(http_error))
        images.extend(self._public_images)
        return ClientPagedResultList(self.provider, images,
                                     limit=limit, marker=marker)


class GCEComputeService(BaseComputeService):
    # TODO: implement GCEComputeService
    def __init__(self, provider):
        super(GCEComputeService, self).__init__(provider)
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
        raise NotImplementedError("To be implemented")

    @property
    def regions(self):
        return self._region_svc


class GCENetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(GCENetworkService, self).__init__(provider)

    def get(self, network_id):
        if network_id is None:
            return None
        # networks = self.list(filter='id eq %s' % network_id) would be better.
        # But, there is a GCE API bug that causes an error if the network_id
        # has more than 19 digits. So, we list all networks and filter
        # ourselves.
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
            response = (self.provider.gce_compute
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

    def create(self, name):
        try:
            networks = self.list(filter='name eq %s' % name)
            if len(networks) > 0:
                return networks[0]

            response = (self.provider.gce_compute
                                     .networks()
                                     .insert(project=self.provider.project_name,
                                             body={'name': name})
                                     .execute())
            if 'error' in response:
                return None
            self.provider.wait_for_global_operation(response)
            networks = self.list(filter='name eq %s' % name)
            return None if len(networks) == 0 else networks[0]
        except:
            return None

    @property
    def subnets(self):
        raise NotImplementedError('To be implemented')

    def floating_ips(self, network_id=None):
        raise NotImplementedError('To be implemented')

    def create_floating_ip(self):
        raise NotImplementedError('To be implemented')

    def routers(self):
        raise NotImplementedError('To be implemented')

    def create_router(self, name=None):
        raise NotImplementedError('To be implemented')
