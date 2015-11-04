from cloudbridge.cloud import interfaces
from test.helpers import ProviderTestBase


class ProviderInterfaceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderInterfaceTestCase, self).__init__(
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
        for key, value in interfaces.CloudProviderServiceType.__dict__.items():
            if not key.startswith("__"):
                self.provider.has_service(value)

    def test_has_service_invalid_service_type(self):
        """
        has_service with an invalid service type should return False
        """
        self.assertFalse(
            self.provider.has_service("NON_EXISTENT_SERVICE"),
            "has_service should not return True for a non-existent service")
