from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def filter(list_items, filters):
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
    template_url_parts = template_url.split('/')
    original_url_parts = original_url.split('/')
    if len(template_url_parts) != len(original_url_parts):
        raise Exception('Invalid url parameter passed')
    d = {}
    for k, v in zip(template_url_parts, original_url_parts):
        if k.startswith('{') and k.endswith('}'):
            d.update({k[1:-1]: v})

    return d


def gen_key_pair():
    # generate private/public key pair
    key = rsa.generate_private_key(backend=default_backend(),
                                   public_exponent=65537,
                                   key_size=2048)

    # get public key in OpenSSH format
    public_key = key.public_key().\
        public_bytes(serialization.Encoding.OpenSSH,
                     serialization.PublicFormat.OpenSSH)

    # get private key in PEM container format
    pem = key.\
        private_bytes(encoding=serialization.Encoding.PEM,
                      format=serialization.PrivateFormat.TraditionalOpenSSL,
                      encryption_algorithm=serialization.NoEncryption())

    # decode to printable strings
    private_key_str = pem.decode('utf-8')
    public_key_str = public_key.decode('utf-8')

    return (private_key_str, public_key_str)
