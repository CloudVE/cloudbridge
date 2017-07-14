# based on http://stackoverflow.com/a/39126754
import cloudbridge as cb
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization as crypt_serialization
from cryptography.hazmat.primitives.asymmetric import rsa


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
