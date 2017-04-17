from azure.mgmt.network.models import NetworkSecurityGroup
from azure.storage.blob.models import Container
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.network.models import SecurityRule

class MockAzureClient:
    sg_rule1 = SecurityRule(protocol='*', source_address_prefix='100', destination_address_prefix="*", access="Allow",
                            direction="Inbound")
    sg_rule1.name = "rule1"
    sg_rule1.id = "r1"
    sg_rule1.destination_port_range = "*"
    sg_rule1.source_port_range = "25-1"

    sg_rule2 = SecurityRule(protocol='*', source_address_prefix='100', destination_address_prefix="*", access="Allow",
                            direction="Inbound")
    sg_rule2.name = "rule2"
    sg_rule2.id = "r2"
    sg_rule2.is_default = True
    sg_rule2.destination_port_range = "*"
    sg_rule2.source_port_range = "*"


    sec_gr1 = NetworkSecurityGroup()
    sec_gr1.name = "sec_group1"
    sec_gr1.id = "sg1"
    sec_gr1.default_security_rules = [sg_rule1]
    sec_gr1.security_rules = [sg_rule2]

    sec_gr2 = NetworkSecurityGroup()
    sec_gr2.name = "sec_group2"
    sec_gr2.id = "sg2"
    sec_gr2.default_security_rules = [sg_rule1]
    sec_gr2.security_rules = [sg_rule2]

    sec_gr3 = NetworkSecurityGroup()
    sec_gr3.name = "sec_group3"
    sec_gr3.id = "sg3"
    sec_gr3.default_security_rules = [sg_rule1]
    sec_gr3.security_rules = [sg_rule2]

    security_groups = [sec_gr1, sec_gr2, sec_gr3]

    container1 = Container()
    container1.name = "container1"
    container2 = Container()
    container2.name = "container2"
    containers = [container1, container2]

    rg = ResourceGroup(location='westus')
    rg.name = "testResourceGroup"

    def __init__(self, provider):
        self._provider = provider


    def create_security_group(self, name, parameters):
        sg_create = NetworkSecurityGroup()
        sg_create.name = name
        sg_create.id = name
        sg_create.default_security_rules = [self.sg_rule1]
        sg_create.security_rules = [self.sg_rule2]
        self.security_groups.append(sg_create)
        return sg_create

    def list_security_group(self):
        return self.security_groups

    def delete_security_group(self, name):
        for item in self.security_groups:
            if item.name == name:
                self.security_groups.remove(item)
                return True
        return False

    def create_security_group_rule(self, security_group, rule_name, parameters):
        new_sg_rule = SecurityRule(protocol='*',source_address_prefix='100',destination_address_prefix="*",access="Allow",direction = "Inbound")
        new_sg_rule.name = "rule1"
        new_sg_rule.id = "r1"
        new_sg_rule.destination_port_range = "*"
        new_sg_rule.source_port_range = "25-1"
        return new_sg_rule

    def delete_security_group_rule(self, name, security_group):
        pass

    def get_resource_group(self, resource_group_name):
        return self.rg

    def create_resource_group(self, resource_group_name, params):
        rg = ResourceGroup(location='westus')
        rg.name = resource_group_name
        return rg

    def get_container(self, container_name):
        for container in self.containers:
            if container.name == container_name:
                return container
        return None

    def list_containers(self):
        return self.containers

    def create_container(self, container_name):
        new_container = Container()
        new_container.name = container_name
        return new_container


