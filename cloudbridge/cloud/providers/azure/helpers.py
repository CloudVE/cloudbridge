from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def filter(list_items, filters):
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
    dict = {}
    for key, value in zip(template_url_parts, original_url_parts):
        if key.startswith('{') and key.endswith('}'):
            dict.update({key[1:-1]: value})

    return dict


def gen_key_pair():
    """
    This method generates the public and private key pair.
    The public key format is OpenSSH and private key format is PEM container
    :return:
    """

    private_key = rsa.generate_private_key(backend=default_backend(),
                                           public_exponent=65537,
                                           key_size=2048)

    public_key_str = private_key.public_key().\
        public_bytes(serialization.Encoding.OpenSSH,
                     serialization.PublicFormat.OpenSSH).decode('utf-8')

    private_key_str = private_key.\
        private_bytes(encoding=serialization.Encoding.PEM,
                      format=serialization.PrivateFormat.TraditionalOpenSSL,
                      encryption_algorithm=serialization.NoEncryption()
                      ).decode('utf-8')

    return (private_key_str, public_key_str)
