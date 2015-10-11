import uuid
from test.helpers import ProviderTestBase


class ProviderSecurityServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderSecurityServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_crud_key_pair_service(self):
        name = 'cbtestkeypair-{0}'.format(uuid.uuid4())
        kp = self.provider.security.key_pairs.create(key_name=name)
        kpl = self.provider.security.key_pairs.list()
        found_kp = [k for k in kpl if k.name == name]
        self.assertTrue(
            len(found_kp) == 1,
            "List key pairs did not return the expected key {0}."
            .format(name))
        self.provider.security.key_pairs.delete(key_name=kp.name)
        kpl = self.provider.security.key_pairs.list()
        found_kp = [k for k in kpl if k.name == name]
        self.assertTrue(
            len(found_kp) == 0,
            "Key pair {0} should have been deleted but still exists."
            .format(name))

    def test_crud_security_group_service(self):
        name = 'cbtestsecuritygroup-{0}'.format(uuid.uuid4())
        sg = self.provider.security.security_groups.create(
            name=name, description=name)
        sgl = self.provider.security.security_groups.get(group_names=[sg.name])
        found_sg = [g for g in sgl if g.name == name]
        self.assertTrue(
            len(found_sg) == 1,
            "List security groups did not return the expected group {0}."
            .format(name))
        self.provider.security.security_groups.delete(group_id=sg.id)
        sgl = self.provider.security.security_groups.list()
        found_sg = [g for g in sgl if g.name == name]
        self.assertTrue(
            len(found_sg) == 0,
            "Security group {0} should have been deleted but still exists."
            .format(name))
