"""
Provider implementation based on boto library for AWS-compatible clouds.
"""

import os

import boto
from boto.ec2.regioninfo import RegionInfo
from httpretty import HTTPretty
from moto.ec2 import mock_ec2
from moto.s3 import mock_s3

from cloudbridge.cloud.base import BaseCloudProvider
from test.helpers import TestMockHelperMixin

from .services import AWSBlockStoreService
from .services import AWSComputeService
from .services import AWSObjectStoreService
from .services import AWSSecurityService


class AWSCloudProvider(BaseCloudProvider):

    def __init__(self, config):
        super(AWSCloudProvider, self).__init__(config)
        self.cloud_type = 'aws'

        # Initialize cloud connection fields
        self.a_key = self._get_config_value(
            'access_key', os.environ.get('AWS_ACCESS_KEY', None))
        self.s_key = self._get_config_value(
            'secret_key', os.environ.get('AWS_SECRET_KEY', None))
        self.is_secure = self._get_config_value('is_secure', True)
        self.region_name = self._get_config_value('region_name', 'us-east-1')
        self.region_endpoint = self._get_config_value(
            'region_endpoint', 'ec2.us-east-1.amazonaws.com')
        self.ec2_port = self._get_config_value('ec2_port', '')
        self.ec2_conn_path = self._get_config_value('ec2_port', '/')

        # service connections, lazily initialized
        self._ec2_conn = None
        self._s3_conn = None

        # Initialize provider services
        self._compute = AWSComputeService(self)
        self._security = AWSSecurityService(self)
        self._block_store = AWSBlockStoreService(self)
        self._object_store = AWSObjectStoreService(self)

    @property
    def ec2_conn(self):
        if not self._ec2_conn:
            self._ec2_conn = self._connect_ec2()
        return self._ec2_conn

    @property
    def s3_conn(self):
        if not self._s3_conn:
            self._s3_conn = self._connect_s3()
        return self._s3_conn

    @property
    def compute(self):
        return self._compute

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
        """
        Get a boto ec2 connection object.
        """
        r = RegionInfo(name=self.region_name, endpoint=self.region_endpoint)
        ec2_conn = boto.connect_ec2(
            aws_access_key_id=self.a_key,
            aws_secret_access_key=self.s_key,
            # api_version is needed for availability
            # zone support for EC2
            api_version='2012-06-01' if self.cloud_type == 'aws' else None,
            is_secure=self.is_secure,
            region=r,
            port=self.ec2_port,
            path=self.ec2_conn_path,
            validate_certs=False,
            debug=2 if self.config.debug_mode else 0)
        return ec2_conn

    def _connect_s3(self):
        """
        Get a boto S3 connection object.
        """
        s3_conn = boto.connect_s3(aws_access_key_id=self.a_key,
                                  aws_secret_access_key=self.s_key)
        return s3_conn


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
            uri="https://swift.rc.nectar.org.au:8888/v1/"
            "AUTH_377/cloud-bridge/aws/instance_data.json",
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
