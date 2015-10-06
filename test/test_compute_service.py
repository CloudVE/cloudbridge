from cloudbridge.providers import interfaces
from test.helpers import ProviderTestBase
import test.helpers


class ProviderComputeServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderComputeServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def setUp(self):
        self.instance = test.helpers.get_test_instance(self.provider)

    def tearDown(self):
        self.instance.terminate()

    def test_instance_status(self):
        """
        instance_state should return an object of type InstanceState
        """
        pass
