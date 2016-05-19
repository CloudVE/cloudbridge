import os
from Crypto.PublicKey import RSA


def generate_key_pair():
    kp = RSA.generate(2048, os.urandom)
    public_key = kp.publickey().exportKey("OpenSSH").split(" ")[1]
    private_key = kp.exportKey("PEM")
    return private_key, public_key
