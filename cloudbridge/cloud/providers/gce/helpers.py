from collections import namedtuple
import hashlib

# based on http://stackoverflow.com/a/39126754
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization as crypt_serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from retrying import retry


GCEKeyInfo = namedtuple('GCEKeyInfo', 'format public_key email')


def gce_projects(provider):
    return provider.gce_compute.projects()


def generate_key_pair():
    key_pair = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048)
    private_key = key_pair.private_bytes(
        crypt_serialization.Encoding.PEM,
        crypt_serialization.PrivateFormat.PKCS8,
        crypt_serialization.NoEncryption())
    public_key = key_pair.public_key().public_bytes(
        crypt_serialization.Encoding.OpenSSH,
        crypt_serialization.PublicFormat.OpenSSH)
    return private_key, public_key


def iter_all(resource, **kwargs):
    token = None
    while True:
        response = resource.list(pageToken=token, **kwargs).execute()
        for item in response.get('items', []):
            yield item
        if 'nextPageToken' not in response:
            return
        token = response['nextPageToken']


def _iter_gce_key_pairs(provider):
    """
    Iterates through the project's metadata, yielding a GCEKeyInfo object
    for each entry in commonInstanceMetaData/items
    """
    metadata = _get_common_metadata(provider)
    for kpinfo in _iter_gce_ssh_keys(metadata):
        yield kpinfo


def _get_common_metadata(provider):
    """
    Get a project's commonInstanceMetadata entry
    """
    metadata = gce_projects(provider).get(
        project=provider.project_name).execute()
    return metadata["commonInstanceMetadata"]


def _get_or_add_sshkey_entry(metadata):
    """
    Get the ssh-keys entry from commonInstanceMetadata/items.
    If an entry does not exist, adds a new empty entry
    """
    sshkey_entry = None
    entries = [item for item in metadata.get('items', [])
               if item['key'] == 'ssh-keys']
    if entries:
        sshkey_entry = entries[0]
    else:  # add a new entry
        sshkey_entry = {'key': 'ssh-keys', 'value': ''}
        if 'items' not in metadata:
            metadata['items'] = [sshkey_entry]
        else:
            metadata['items'].append(sshkey_entry)
    return sshkey_entry


def _iter_gce_ssh_keys(metadata):
    """
    Iterates through the ssh keys given a commonInstanceMetadata dict,
    yielding a GCEKeyInfo object for each entry in
    commonInstanceMetaData/items
    """
    sshkeys = _get_or_add_sshkey_entry(metadata)["value"]
    for key in sshkeys.split("\n"):
        # elems should be "ssh-rsa <public_key> <email>"
        elems = key.split(" ")
        if elems and elems[0]:  # ignore blank lines
            yield GCEKeyInfo(
                    elems[0], elems[1].encode('ascii'), elems[2])


def gce_metadata_save_op(provider, callback):
    """
    Carries out a metadata save operation. In GCE, a fingerprint based
    locking mechanism is used to prevent lost updates. A new fingerprint
    is returned each time metadata is retrieved. Therefore, this method
    retrieves the metadata, invokes the provided callback with that
    metadata, and saves the metadata using the original fingerprint
    immediately afterwards, ensuring that update conflicts can be detected.
    """
    def _save_common_metadata(provider):
        metadata = _get_common_metadata(provider)
        # add a new entry if one doesn't exist
        sshkey_entry = _get_or_add_sshkey_entry(metadata)
        gce_kp_list = callback(_iter_gce_ssh_keys(metadata))

        entry = ""
        for gce_kp in gce_kp_list:
            entry = entry + u"{0} {1} {2}\n".format(gce_kp.format,
                                                    gce_kp.public_key,
                                                    gce_kp.email)
        sshkey_entry["value"] = entry.rstrip()
        # common_metadata will have the current fingerprint at this point
        operation = gce_projects(provider).setCommonInstanceMetadata(
            project=provider.project_name, body=metadata).execute()
        provider.wait_for_operation(operation)

    # Retry a few times if the fingerprints conflict
    retry_decorator = retry(stop_max_attempt_number=5)
    retry_decorator(_save_common_metadata)(provider)


def gce_kp_to_id(gce_kp):
    """
    Accept a GCEKeyInfo object and return a unique
    ID for it
    """
    md5 = hashlib.md5()
    md5.update(gce_kp.public_key)
    return md5.hexdigest()


def modify_or_add_metadata_item(provider, key, value):
    metadata = _get_common_metadata(provider)
    entries = [item for item in metadata.get('items', [])
               if item['key'] == key]
    if entries:
        entries[-1]['value'] = value
    else:
        entry = {'key': key, 'value': value}
        if 'items' not in metadata:
            metadata['items'] = [entry]
        else:
            metadata['items'].append(entry)
    operation = gce_projects(provider).setCommonInstanceMetadata(
        project=provider.project_name, body=metadata).execute()
    provider.wait_for_operation(operation)


def get_metadata_item_value(provider, key):
    metadata = _get_common_metadata(provider)
    entries = [item['value'] for item in metadata.get('items', [])
               if item['key'] == key]
    if entries:
        return entries[-1]
    else:
        return None
