"""
Provider implementation based on boto library for EC2-compatible clouds.
"""

import boto
import os
from boto.ec2.regioninfo import RegionInfo

from cloudbridge.providers.base import BaseCloudProvider
from cloudbridge.providers.base import BaseSecurityGroup
from cloudbridge.providers.interfaces import SecurityService
from cloudbridge.providers.interfaces import KeyPair


class EC2CloudProviderV1(BaseCloudProvider):

    def __init__(self, config):
        self.config = config
        self.cloud_type = 'ec2'

        # Initialize cloud connection fields
        self.a_key = self._get_config_value(
            config, 'access_key', os.environ.get('EC2_ACCESS_KEY', None))
        self.s_key = self._get_config_value(
            config, 'secret_key', os.environ.get('EC2_SECRET_KEY', None))
        self.is_secure = self._get_config_value(config, 'is_secure', True)
        self.region_name = self._get_config_value(config, 'region_name', 'us-east-1')
        self.region_endpoint = self._get_config_value(
            config, 'region_endpoint', 'ec2.us-east-1.amazonaws.com')
        self.ec2_port = self._get_config_value(config, 'ec2_port', '')
        self.ec2_conn_path = self._get_config_value(config, 'ec2_port', '/')

        # Create a connection object
        self.ec2_conn = self._connect_ec2()

        # Initialize provider services
        self.compute = None  # EC2ComputeService(self)
        self.images = None  # EC2ImageService(self)
        self.security = EC2SecurityService(self)
        self.block_store = None  # EC2BlockStore(self)
        self.object_store = None  # EC2ObjectStore(self)

    def _connect_ec2(self):
        """
        Get a boto connection object for the given cloud.
        """
        r = RegionInfo(name=self.region_name, endpoint=self.region_endpoint)
        ec2_conn = boto.connect_ec2(aws_access_key_id=self.a_key,
                                    aws_secret_access_key=self.s_key,
                                    # api_version is needed for availability zone support for EC2
                                    api_version='2012-06-01' if self.cloud_type == 'ec2' else None,
                                    is_secure=self.is_secure,
                                    region=r,
                                    port=self.ec2_port,
                                    path=self.ec2_conn_path,
                                    validate_certs=False)
        return ec2_conn


class EC2SecurityService(SecurityService):

    def __init__(self, provider):
        self.provider = provider

    def list_key_pairs(self):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        key_pairs = self.provider.ec2_conn.get_all_key_pairs()
        return [KeyPair(kp.name) for kp in key_pairs]

    def list_security_groups(self):
        """
        Create a new security group

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        groups = self.provider.ec2_conn.get_all_security_groups()
        return [BaseSecurityGroup(group.name) for group in groups]
