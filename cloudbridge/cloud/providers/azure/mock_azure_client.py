from azure.mgmt.network.models import NetworkSecurityGroup


class MockAzureClient:
    sec_gr1 = NetworkSecurityGroup()
    sec_gr1.name = "sec_group1"
    sec_gr1.id = "sg1"
    sec_gr2 = NetworkSecurityGroup()
    sec_gr2.name = "sec_group2"
    sec_gr2.id = "sg2"
    sec_gr3 = NetworkSecurityGroup()
    sec_gr3.name = "sec_group3"
    sec_gr3.id = "sg3"
    security_groups = [sec_gr1, sec_gr2, sec_gr3]

    def __init__(self, provider):
        self._provider = provider

    def list_security_group(self, resource_group_name):
        return self.security_groups
