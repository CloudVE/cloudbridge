"""Provider implementation based on boto library for AWS-compatible clouds."""

import os

import boto
from boto.ec2.regioninfo import RegionInfo
try:
    # These are installed only for the case of a dev instance
    from httpretty import HTTPretty
    from moto import mock_ec2
    from moto import mock_s3
except ImportError:
    # TODO: Once library logging is configured, change this
    print("[aws provider] moto library not available!")

from cloudbridge.cloud.base import BaseCloudProvider
from cloudbridge.cloud.interfaces import TestMockHelperMixin

from .services import AWSBlockStoreService
from .services import AWSComputeService
from .services import AWSNetworkService
from .services import AWSObjectStoreService
from .services import AWSSecurityService


class AWSCloudProvider(BaseCloudProvider):

    PROVIDER_ID = 'aws'
    AWS_INSTANCE_DATA_DEFAULT_URL = "https://d168wakzal7fp0.cloudfront.net/" \
                                    "aws_instance_data.json"

    def __init__(self, config):
        super(AWSCloudProvider, self).__init__(config)
        self.cloud_type = 'aws'

        # Initialize cloud connection fields
        self.a_key = self._get_config_value(
            'aws_access_key', os.environ.get('AWS_ACCESS_KEY', None))
        self.s_key = self._get_config_value(
            'aws_secret_key', os.environ.get('AWS_SECRET_KEY', None))
        self.session_token = self._get_config_value('aws_session_token', None)
        # EC2 connection fields
        self.ec2_is_secure = self._get_config_value('ec2_is_secure', True)
        self.region_name = self._get_config_value(
            'ec2_region_name', 'us-east-1')
        self.region_endpoint = self._get_config_value(
            'ec2_region_endpoint', 'ec2.us-east-1.amazonaws.com')
        self.ec2_port = self._get_config_value('ec2_port', None)
        self.ec2_conn_path = self._get_config_value('ec2_conn_path', '/')
        self.ec2_validate_certs = self._get_config_value(
            'ec2_validate_certs', False)
        # S3 connection fields
        self.s3_is_secure = self._get_config_value('s3_is_secure', True)
        self.s3_host = self._get_config_value('s3_host', 's3.amazonaws.com')
        self.s3_port = self._get_config_value('s3_port', None)
        self.s3_conn_path = self._get_config_value('s3_conn_path', '/')
        self.s3_validate_certs = self._get_config_value(
            's3_validate_certs', False)

        # service connections, lazily initialized
        self._ec2_conn = None
        self._vpc_conn = None
        self._s3_conn = None

        # Initialize provider services
        self._compute = AWSComputeService(self)
        self._network = AWSNetworkService(self)
        self._security = AWSSecurityService(self)
        self._block_store = AWSBlockStoreService(self)
        self._object_store = AWSObjectStoreService(self)

    @property
    def ec2_conn(self):
        if not self._ec2_conn:
            self._ec2_conn = self._connect_ec2()
        return self._ec2_conn

    @property
    def vpc_conn(self):
        if not self._vpc_conn:
            self._vpc_conn = self._connect_vpc()
        return self._vpc_conn

    @property
    def s3_conn(self):
        if not self._s3_conn:
            self._s3_conn = self._connect_s3()
        return self._s3_conn

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
        """
        Get a boto ec2 connection object.
        """
        r = RegionInfo(name=self.region_name, endpoint=self.region_endpoint)
        return self._conect_ec2_region(r)

    def _conect_ec2_region(self, region):
        ec2_conn = boto.connect_ec2(
            aws_access_key_id=self.a_key,
            aws_secret_access_key=self.s_key,
            is_secure=self.ec2_is_secure,
            region=region,
            port=self.ec2_port,
            path=self.ec2_conn_path,
            validate_certs=self.ec2_validate_certs,
            debug=2 if self.config.debug_mode else 0)
        return ec2_conn

    def _connect_vpc(self):
        """
        Get a boto VPC connection object.
        """
        r = RegionInfo(name=self.region_name, endpoint=self.region_endpoint)
        vpc_conn = boto.connect_vpc(
            aws_access_key_id=self.a_key,
            aws_secret_access_key=self.s_key,
            security_token=self.session_token,
            is_secure=self.ec2_is_secure,
            region=r,
            port=self.ec2_port,
            path=self.ec2_conn_path,
            validate_certs=self.ec2_validate_certs,
            debug=2 if self.config.debug_mode else 0)
        return vpc_conn

    def _connect_s3(self):
        """
        Get a boto S3 connection object.
        """
        s3_conn = boto.connect_s3(aws_access_key_id=self.a_key,
                                  aws_secret_access_key=self.s_key,
                                  security_token=self.session_token,
                                  is_secure=self.s3_is_secure,
                                  port=self.s3_port,
                                  host=self.s3_host,
                                  path=self.s3_conn_path,
                                  validate_certs=self.s3_validate_certs,
                                  debug=2 if self.config.debug_mode else 0)
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
            HTTPretty.GET,
            self.AWS_INSTANCE_DATA_DEFAULT_URL,
            body=u"""
[
  {
    "family": "General Purpose",
    "enhanced_networking": false,
    "vCPU": 1,
    "generation": "current",
    "ebs_iops": 0,
    "network_performance": "Low",
    "ebs_throughput": 0,
    "vpc": {
      "ips_per_eni": 2,
      "max_enis": 2
    },
    "arch": [
      "x86_64"
    ],
    "linux_virtualization_types": [
        "HVM"
    ],
    "ebs_optimized": false,
    "storage": null,
    "max_bandwidth": 0,
    "instance_type": "t2.nano",
    "ECU": "variable",
    "memory": 0.5,
    "ebs_max_bandwidth": 0
  }
]
""")

    def tearDownMock(self):
        """
        Stop Moto intercepting all socket communications
        """
        self.s3mock.stop()
        self.ec2mock.stop()
