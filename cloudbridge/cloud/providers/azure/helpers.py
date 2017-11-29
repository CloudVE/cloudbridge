def filter_by_tag(list_items, filters):
    """
    This function filter items on the tags
    :param list_items:
    :param filters:
    :return:
    """
    filtered_list = []
    if filters:
        for obj in list_items:
            for key in filters:
                if obj.tags and filters[key] in obj.tags.get(key, ''):
                    filtered_list.append(obj)

        return filtered_list
    else:
        return list_items


def parse_url(template_url, original_url):
    """
    In Azure all the resource IDs are returned as URIs.
    ex: '/subscriptions/{subscriptionId}/resourceGroups/' \
       '{resourceGroupName}/providers/Microsoft.Compute/' \
       'virtualMachines/{vmName}'
    This function splits the resource ID based on the template url passed
    and returning the dictionary.
    """
    template_url_parts = template_url.split('/')
    original_url_parts = original_url.split('/')
    if len(template_url_parts) != len(original_url_parts):
        raise Exception('Invalid url parameter passed')
    resource_param = {}
    for key, value in zip(template_url_parts, original_url_parts):
        if key.startswith('{') and key.endswith('}'):
            resource_param.update({key[1:-1]: value})

    return resource_param
