from test import helpers

from cloudbridge.cloud.factory import CloudProviderFactory
from cloudbridge.cloud.factory import ProviderList


config = {}
provider = CloudProviderFactory().create_provider(
    ProviderList.OPENSTACK,
    config)
# print provider.security.list_key_pairs()
# print provider.compute.instance_types.list()
# print next(provider.compute.instance_types.find_by_name("m1.small"))
instance = helpers.get_test_instance(provider)
# print provider.security.list_security_groups()
