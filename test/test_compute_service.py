from cloudbridge.providers import interfaces
from test.helpers import ProviderTestBase


class ProviderComputeServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderComputeServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

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
