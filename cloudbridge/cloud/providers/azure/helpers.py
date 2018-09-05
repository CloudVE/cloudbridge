from cloudbridge.cloud.interfaces.exceptions import InvalidValueException


# def filter_by_tag(list_items, filters):
#     """
#     This function filter items on the tags
#     :param list_items:
#     :param filters:
#     :return:
#     """
#     filtered_list = []
#     if filters:
#         for obj in list_items:
#             for key in filters:
#                 if obj.tags and filters[key] in obj.tags.get(key, ''):
#                     filtered_list.append(obj)
#
#         return filtered_list
#     else:
#         return list_items


def parse_url(template_urls, original_url):
    """
    In Azure all the resource IDs are returned as URIs.
    ex: '/subscriptions/{subscriptionId}/resourceGroups/' \
       '{resourceGroupName}/providers/Microsoft.Compute/' \
       'virtualMachines/{vmName}'
    This function splits the resource ID based on the template urls passed
    and returning the dictionary.

    The only exception to that format are image URN's which are used for
    public gallery references:
    https://docs.microsoft.com/en-us/azure/virtual-machines/linux/cli-ps-findimage
    """
    if not original_url:
        raise InvalidValueException(template_urls, original_url)
    original_url_parts = original_url.split('/')
    if len(original_url_parts) == 1:
        original_url_parts = original_url.split(':')
    for each_template in template_urls:
        template_url_parts = each_template.split('/')
        if len(template_url_parts) == 1:
            template_url_parts = each_template.split(':')
        if len(template_url_parts) == len(original_url_parts):
            break
    if len(template_url_parts) != len(original_url_parts):
        raise InvalidValueException(template_urls, original_url)
    resource_param = {}
    for key, value in zip(template_url_parts, original_url_parts):
        if key.startswith('{') and key.endswith('}'):
            resource_param.update({key[1:-1]: value})
    return resource_param


def generate_urn(gallery_image):
    """
    This function takes an azure gallery image and outputs a corresponding URN
    :param gallery_image: a GalleryImageReference object
    :return: URN as string
    """
    reference_dict = gallery_image.as_dict()
    return ':'.join([reference_dict['publisher'],
                     reference_dict['offer'],
                     reference_dict['sku'],
                     reference_dict['version']])
