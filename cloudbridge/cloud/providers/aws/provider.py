"""
Provider implementation based on boto library for AWS-compatible clouds.
"""

import os

import boto3
try:
    # These are installed only for the case of a dev instance
    from httpretty import HTTPretty
    from moto.ec2 import mock_ec2
    from moto.s3 import mock_s3
except ImportError:
    # TODO: Once library logging is configured, change this
    print '[aws provider] moto library not available!'

from cloudbridge.cloud.base import BaseCloudProvider
from cloudbridge.cloud.interfaces import TestMockHelperMixin

from .services import AWSBlockStoreService
from .services import AWSComputeService
from .services import AWSNetworkService
from .services import AWSObjectStoreService
from .services import AWSSecurityService

# pylint: disable=R0902


class AWSCloudProvider(BaseCloudProvider):
    '''AWS cloud provider interface'''
    PROVIDER_ID = 'aws'

    def __init__(self, config):
        super(AWSCloudProvider, self).__init__(config)
        self.cloud_type = 'aws'

        # Initialize cloud connection fields
        # These are passed as-is to Boto
        self.session_cfg = {
            'aws_access_key_id': self._get_config_value(
                'aws_access_key', os.environ.get('AWS_ACCESS_KEY', None)),
            'aws_secret_access_key': self._get_config_value(
                'aws_secret_key', os.environ.get('AWS_SECRET_KEY', None)),
            'region_name': self._get_config_value(
                'ec2_region_name', 'us-east-1')
        }
        self.ec2_cfg = {
            'service_name': 'ec2',
            'use_ssl': self._get_config_value('ec2_is_secure', True),
            'verify': self._get_config_value('ec2_validate_certs', True)
        }
        self.s3_cfg = {
            'service_name': 's3',
            'use_ssl': self._get_config_value('s3_is_secure', True),
            'verify': self._get_config_value('s3_validate_certs', True)
        }

        # Service connections, lazily initialized
        self._session = None
        self._ec2_conn = None
        self._s3_conn = None

        # Initialize provider services
        self._compute = AWSComputeService(self)
        self._network = AWSNetworkService(self)
        self._security = AWSSecurityService(self)
        self._block_store = AWSBlockStoreService(self)
        self._object_store = AWSObjectStoreService(self)

    @property
    def session(self):
        '''Get a low-level session object or create one if needed'''
        return self._session if self._session else \
            boto3.session.Session(**self.session_cfg)

    @property
    def ec2_conn(self):
        '''Get an EC2 connection object or create one if needed'''
        return self._ec2_conn if self._ec2_conn else self._connect_ec2()

    @property
    def s3_conn(self):
        '''Get an S3 connection object or create one if needed'''
        return self._s3_conn if self._s3_conn else self._connect_s3()

    @property
    def compute(self):
        return self._compute

    @property
    def network(self):
        return self._network

    @property
    def security(self):
        return self._security

    @property
    def block_store(self):
        return self._block_store

    @property
    def object_store(self):
        return self._object_store

    def _connect_ec2(self):
        '''Get an EC2 resource object'''
        return self.session.resource(**self.ec2_cfg)

    def _connect_s3(self):
        '''Get an S3 resource object'''
        return self.session.resource(**self.s3_cfg)


class MockAWSCloudProvider(AWSCloudProvider, TestMockHelperMixin):

    def __init__(self, config):
        super(MockAWSCloudProvider, self).__init__(config)

    def setUpMock(self):
        """
        Let Moto take over all socket communications
        """
        self.ec2mock = mock_ec2()
        self.ec2mock.start()
        self.s3mock = mock_s3()
        self.s3mock.start()
        HTTPretty.register_uri(
            method="GET",
            uri="https://d168wakzal7fp0.cloudfront.net/aws_instance_data.json",
            body="""
[
  {
    "family": "General Purpose",
    "enhanced_networking": false,
    "vCPU": 1,
    "generation": "previous",
    "ebs_iops": 0,
    "network_performance": "Low",
    "ebs_throughput": 0,
    "vpc": {
      "ips_per_eni": 4,
      "max_enis": 2
    },
    "arch": [
      "i386",
      "x86_64"
    ],
    "linux_virtualization_types": [],
    "ebs_optimized": false,
    "storage": {
      "ssd": false,
      "devices": 1,
      "size": 160
    },
    "max_bandwidth": 0,
    "instance_type": "t1.micro",
    "ECU": 1.0,
    "memory": 1.7
  }
]
"""
        )

    def tearDownMock(self):
        """
        Stop Moto intercepting all socket communications
        """
        self.s3mock.stop()
        self.ec2mock.stop()
