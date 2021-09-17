import binascii
import collections
import datetime
import hashlib
import re

import six
from six.moves.urllib.parse import quote

from googleapiclient.errors import HttpError

import tenacity

from cloudbridge.interfaces.exceptions import ProviderInternalException


def gcp_projects(provider):
    return provider.gcp_compute.projects()


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
    metadata = gcp_projects(provider).get(
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
def gcp_metadata_save_op(provider, callback):
    """
    Carries out a metadata save operation. In GCP, a fingerprint based
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
        operation = gcp_projects(provider).setCommonInstanceMetadata(
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

    gcp_metadata_save_op(provider, _update_metadata_key)


# This function will raise an HttpError with message containing
# "Metadata has duplicate key" if it's not unique, unlike the previous
# method which either adds or updates the value corresponding to that key
def add_metadata_item(provider, key, value):
    def _add_metadata_key(metadata):
        entry = {'key': key, 'value': value}
        entries = metadata.get('items', [])
        entries.append(entry)
        # Reassign explicitly in case the original get returned [] although
        # if not it will be already updated
        metadata['items'] = entries

    gcp_metadata_save_op(provider, _add_metadata_key)


def find_matching_metadata_items(provider, key_regex):
    metadata = get_common_metadata(provider)
    items = metadata.get('items', [])
    if not items:
        return []
    return [item for item in items
            if re.search(key_regex, item['key'])]


def get_metadata_item_value(provider, key):
    metadata = get_common_metadata(provider)
    entries = [item['value'] for item in metadata.get('items', [])
               if item['key'] == key]
    if entries:
        return entries[-1]
    else:
        return None


def remove_metadata_item(provider, key):
    def _remove_metadata_by_key(metadata):
        items = metadata.get('items', [])
        # No metadata to delete
        if not items:
            return False
        else:
            entries = [item for item in metadata.get('items', [])
                       if item['key'] != key]

            # Make sure only one entry is deleted
            if len(entries) < len(items) - 1:
                raise ProviderInternalException("Multiple metadata entries "
                                                "found for the same key {}"
                                                .format(key))
            # If none is deleted indicate so by returning False
            elif len(entries) == len(items):
                return False

            else:
                metadata['items'] = entries

    gcp_metadata_save_op(provider, _remove_metadata_by_key)
    return True


def __if_label_fingerprint_differs(e):
    # return True if the CloudError exception is due to subnet being in use
    if isinstance(e, HttpError):
        expected_message = 'Labels fingerprint either invalid or ' \
                           'resource labels have changed'
        # str wrapper required for Python 2.7
        if expected_message in str(e.content):
            return True
    return False


@tenacity.retry(stop=tenacity.stop_after_attempt(10),
                retry=tenacity.retry_if_exception(
                    __if_label_fingerprint_differs),
                wait=tenacity.wait_exponential(max=10),
                reraise=True)
def change_label(resource, key, value, res_att, request):
    resource.assert_valid_resource_label(value)
    labels = getattr(resource, res_att).get("labels", {})
    # The returned value from above command yields a unicode dict key, which
    # cannot be simply cast into a str for py2 so pop the key and re-add it
    # The casting needs to be done for all labels, as to support both
    # description and label setting
    labels[key] = str(value)
    for k in list(labels):
        labels[str(k)] = str(labels.pop(k))

    request_body = {
        "labels": labels,
        "labelFingerprint":
            str(getattr(resource, res_att).get('labelFingerprint')),
    }
    try:
        request.body = str(request_body)
        request.body_size = len(str(request_body))
        response = request.execute()
        # pylint:disable=protected-access
        resource._provider.wait_for_operation(
            response, zone=getattr(resource, 'zone_name', None))
    finally:
        resource.refresh()


# https://cloud.google.com/storage/docs/access-control/signing-urls-manually#python-sample
def generate_signed_url(credentials, bucket_name, object_name,
                        subresource=None, expiration=604800, http_method='GET',
                        query_parameters=None, headers=None):

    if expiration > 604800:
        # max allowed expiration time is 7 days
        expiration = 604800

    escaped_object_name = quote(six.ensure_binary(object_name), safe=b'/~')
    canonical_uri = '/{}'.format(escaped_object_name)

    datetime_now = datetime.datetime.utcnow()
    request_timestamp = datetime_now.strftime('%Y%m%dT%H%M%SZ')
    datestamp = datetime_now.strftime('%Y%m%d')

    client_email = credentials.service_account_email
    credential_scope = '{}/auto/storage/goog4_request'.format(datestamp)
    credential = '{}/{}'.format(client_email, credential_scope)

    if headers is None:
        headers = dict()
    host = '{}.storage.googleapis.com'.format(bucket_name)
    headers['host'] = host

    canonical_headers = ''
    ordered_headers = collections.OrderedDict(sorted(headers.items()))
    for k, v in ordered_headers.items():
        lower_k = str(k).lower()
        strip_v = str(v).lower()
        canonical_headers += '{}:{}\n'.format(lower_k, strip_v)

    signed_headers = ''
    for k, _ in ordered_headers.items():
        lower_k = str(k).lower()
        signed_headers += '{};'.format(lower_k)
    signed_headers = signed_headers[:-1]  # remove trailing ';'

    if query_parameters is None:
        query_parameters = dict()
    query_parameters['X-Goog-Algorithm'] = 'GOOG4-RSA-SHA256'
    query_parameters['X-Goog-Credential'] = credential
    query_parameters['X-Goog-Date'] = request_timestamp
    query_parameters['X-Goog-Expires'] = expiration
    query_parameters['X-Goog-SignedHeaders'] = signed_headers
    if subresource:
        query_parameters[subresource] = ''

    canonical_query_string = ''
    ordered_query_parameters = collections.OrderedDict(
        sorted(query_parameters.items()))
    for k, v in ordered_query_parameters.items():
        encoded_k = quote(str(k), safe='')
        encoded_v = quote(str(v), safe='')
        canonical_query_string += '{}={}&'.format(encoded_k, encoded_v)
    canonical_query_string = canonical_query_string[:-1]  # remove trailing '&'

    canonical_request = '\n'.join([http_method,
                                   canonical_uri,
                                   canonical_query_string,
                                   canonical_headers,
                                   signed_headers,
                                   'UNSIGNED-PAYLOAD'])

    canonical_request_hash = hashlib.sha256(
        canonical_request.encode()).hexdigest()

    string_to_sign = '\n'.join(['GOOG4-RSA-SHA256',
                                request_timestamp,
                                credential_scope,
                                canonical_request_hash])

    # signer.sign() signs using RSA-SHA256 with PKCS1v15 padding
    signature = binascii.hexlify(
        credentials.signer.sign(string_to_sign)
    ).decode()

    scheme_and_host = '{}://{}'.format('https', host)
    signed_url = '{}{}?{}&x-goog-signature={}'.format(
        scheme_and_host, canonical_uri, canonical_query_string, signature)

    return signed_url
