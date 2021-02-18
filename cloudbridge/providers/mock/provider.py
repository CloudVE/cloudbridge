"""
    Provider implementation based on the moto library (mock boto). This mock
    provider is useful for running tests against cloudbridge but should not
    be used in tandem with other providers, in particular the AWS provider.
    This is because instantiating this provider will result in all calls to
    boto being hijacked, which will cause AWS to malfunction.
    See notes below.
"""
from moto import mock_ec2
from moto import mock_route53
from moto import mock_s3

from ..aws import AWSCloudProvider
from ...interfaces.provider import TestMockHelperMixin


class MockAWSCloudProvider(AWSCloudProvider, TestMockHelperMixin):
    """
    Using this mock driver will result in all boto communications being
    hijacked. As a result, this mock driver and the AWS driver cannot be used
    at the same time. Do not instantiate the mock driver if you plan to use
    the AWS provider within the same python process. Alternatively, call
    provider.tearDownMock() to stop the hijacking.
    """
    PROVIDER_ID = 'mock'

    def __init__(self, config):
        self.setUpMock()
        super(MockAWSCloudProvider, self).__init__(config)

    def setUpMock(self):
        """
        Let Moto take over all socket communications
        """
        self.ec2mock = mock_ec2()
        self.ec2mock.start()
        self.s3mock = mock_s3()
        self.s3mock.start()
        self.route53mock = mock_route53()
        self.route53mock.start()

    def tearDownMock(self):
        """
        Stop Moto intercepting all socket communications
        """
        self.s3mock.stop()
        self.ec2mock.stop()
        self.route53mock.stop()
