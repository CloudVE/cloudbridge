import re

from googleapiclient.errors import HttpError

import tenacity

from cloudbridge.cloud.interfaces.exceptions import ProviderInternalException


def gce_projects(provider):
    return provider.gce_compute.projects()


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

    gce_metadata_save_op(provider, _add_metadata_key)


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

    gce_metadata_save_op(provider, _remove_metadata_by_key)
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
    print(labels)
    labels[key] = value
    request_body = {
        "labels": labels,
        "labelFingerprint":
            getattr(resource, res_att).get('labelFingerprint'),
    }
    try:
        request.body = str(request_body)
        request.body_size = len(str(request_body))
        response = request.execute()
        resource._provider.wait_for_operation(response,
                                              zone=resource.zone_name)
    finally:
        resource.refresh()
