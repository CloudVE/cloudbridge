from cloudbridge.providers import interfaces
import test.helpers
from test.helpers import ProviderTestBase


class ProviderComputeServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderComputeServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def setUp(self):
        self.instance = test.helpers.get_test_instance(self.provider)

    def tearDown(self):
        self.instance.terminate()

    def test_create_instance(self):
        # Need a less dangerous test
        #         instance = self.provider.compute.create_instance(
        #             "HelloBridgeCloud",
        #             "ami-d85e75b0",
        #             "t1.micro")
        #
        #         self.assertIsInstance(instance, interfaces.Instance)
        #         self.assertEqual(instance.name, "HelloBridgeCloud")
        #         instance.terminate()
        pass
