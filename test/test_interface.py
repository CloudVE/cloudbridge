import cloudbridge
from cloudbridge.cloud import interfaces
from test.helpers import ProviderTestBase


class CloudInterfaceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(CloudInterfaceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_name_property(self):
        """
        Name should always return a value and should not raise an exception
        """
        assert self.provider.name

    def test_has_service_valid_service_type(self):
        """
        has_service with a valid service type should return
        a boolean and raise no exceptions
        """
        for key, value in interfaces.CloudServiceType.__dict__.items():
            if not key.startswith("__"):
                self.provider.has_service(value)

    def test_has_service_invalid_service_type(self):
        """
        has_service with an invalid service type should return False
        """
        self.assertFalse(
            self.provider.has_service("NON_EXISTENT_SERVICE"),
            "has_service should not return True for a non-existent service")

    def test_library_version(self):
        """
        Check that the library version can be retrieved.
        """
        self.assertIsNotNone(cloudbridge.get_version(),
                             "Did not get library version.")
