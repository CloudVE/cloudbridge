"""Provider implementation based on boto library for AWS-compatible clouds."""
import logging as log

import boto3

from botocore.client import Config

from cloudbridge.base import BaseCloudProvider
from cloudbridge.base.helpers import get_env

from .services import AWSComputeService
from .services import AWSDnsService
from .services import AWSNetworkingService
from .services import AWSSecurityService
from .services import AWSStorageService


class AWSCloudProvider(BaseCloudProvider):
    '''AWS cloud provider interface'''
    PROVIDER_ID = 'aws'
    AWS_INSTANCE_DATA_DEFAULT_URL = "http://cloudve.org/cb-aws-vmtypes.json"

    def __init__(self, config):
        super(AWSCloudProvider, self).__init__(config)

        # Initialize cloud connection fields
        # These are passed as-is to Boto
        self._region_name = self._get_config_value('aws_region_name',
                                                   'us-east-1')
        self._zone_name = self._get_config_value('aws_zone_name')
        self.session_cfg = {
            'aws_access_key_id': self._get_config_value(
                'aws_access_key', get_env('AWS_ACCESS_KEY')),
            'aws_secret_access_key': self._get_config_value(
                'aws_secret_key', get_env('AWS_SECRET_KEY')),
            'aws_session_token': self._get_config_value(
                'aws_session_token', None)
        }
        self.ec2_cfg = {
            'use_ssl': self._get_config_value('ec2_is_secure', True),
            'verify': self._get_config_value('ec2_validate_certs', True),
            'endpoint_url': self._get_config_value('ec2_endpoint_url')
        }
        self.s3_cfg = {
            'use_ssl': self._get_config_value('s3_is_secure', True),
            'verify': self._get_config_value('s3_validate_certs', True),
            'endpoint_url': self._get_config_value('s3_endpoint_url'),
            'config': Config(
                signature_version=self._get_config_value(
                    's3_signature_version', 's3v4'))
        }

        # service connections, lazily initialized
        self._session = None
        self._ec2_conn = None
        self._vpc_conn = None
        self._s3_conn = None

        # Initialize provider services
        self._compute = AWSComputeService(self)
        self._networking = AWSNetworkingService(self)
        self._security = AWSSecurityService(self)
        self._storage = AWSStorageService(self)
        self._dns = AWSDnsService(self)

    @property
    def session(self):
        '''Get a low-level session object or create one if needed'''
        if not self._session:
            if self.config.debug_mode:
                boto3.set_stream_logger(level=log.DEBUG)
            self._session = boto3.session.Session(
                region_name=self.region_name, **self.session_cfg)
        return self._session

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
    def networking(self):
        return self._networking

    @property
    def security(self):
        return self._security

    @property
    def storage(self):
        return self._storage

    @property
    def dns(self):
        return self._dns

    def _connect_ec2(self):
        """
        Get a boto ec2 connection object.
        """
        return self._connect_ec2_region(region_name=self.region_name)

    def _connect_ec2_region(self, region_name=None):
        '''Get an EC2 resource object'''
        return self.session.resource(
            'ec2', region_name=region_name, **self.ec2_cfg)

    def _connect_s3(self):
        '''Get an S3 resource object'''
        return self.session.resource(
            's3', region_name=self.region_name, **self.s3_cfg)
