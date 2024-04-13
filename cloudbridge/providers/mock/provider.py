"""
    Provider implementation based on the moto library (mock boto). This mock
    provider is useful for running tests against cloudbridge but should not
    be used in tandem with other providers, in particular the AWS provider.
    This is because instantiating this provider will result in all calls to
    boto being hijacked, which will cause AWS to malfunction.
    See notes below.
"""
from moto import mock_aws

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
        self.mock_aws = mock_aws()
        self.mock_aws.start()

    def tearDownMock(self):
        """
        Stop Moto intercepting all socket communications
        """
        self.mock_aws.stop()
