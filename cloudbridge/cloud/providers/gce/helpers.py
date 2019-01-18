# based on http://stackoverflow.com/a/39126754
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization as crypt_serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from googleapiclient.errors import HttpError

import tenacity


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
    return private_key.decode(), public_key.decode()


def iter_all(resource, **kwargs):
    token = None
    while True:
        response = resource.list(pageToken=token, **kwargs).execute()
        for item in response.get('items', []):
            yield item
        if 'nextPageToken' not in response:
            return
        token = response['nextPageToken']


def get_common_metadata(provider):
    """
    Get a project's commonInstanceMetadata entry
    """
    metadata = gce_projects(provider).get(
        project=provider.project_name).execute()
    return metadata["commonInstanceMetadata"]


def __if_fingerprint_differs(e):
    # return True if the CloudError exception is due to subnet being in use
    if isinstance(e, HttpError):
        expected_message = 'Supplied fingerprint does not match current ' \
                           'metadata fingerprint.'
        # str wrapper required for Python 2.7
        if expected_message in str(e.content):
            return True
    return False


@tenacity.retry(stop=tenacity.stop_after_attempt(10),
                retry=tenacity.retry_if_exception(__if_fingerprint_differs),
                wait=tenacity.wait_exponential(max=10),
                reraise=True)
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
        # get the latest metadata (so we get the latest fingerprint)
        metadata = get_common_metadata(provider)
        # allow callback to do processing on it
        callback(metadata)
        # save the metadata
        operation = gce_projects(provider).setCommonInstanceMetadata(
            project=provider.project_name, body=metadata).execute()
        provider.wait_for_operation(operation)

    # Retry a few times if the fingerprints conflict
    _save_common_metadata(provider)


def modify_or_add_metadata_item(provider, key, value):
    def _update_metadata_key(metadata):
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

    gce_metadata_save_op(provider, _update_metadata_key)


def get_metadata_item_value(provider, key):
    metadata = get_common_metadata(provider)
    entries = [item['value'] for item in metadata.get('items', [])
               if item['key'] == key]
    if entries:
        return entries[-1]
    else:
        return None
