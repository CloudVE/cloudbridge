from cloudbridge.providers.factory import CloudProviderFactory
from cloudbridge.providers.factory import ProviderList

config = {}
provider = CloudProviderFactory().create_provider(ProviderList.OPENSTACK, config)
# print provider.security.list_key_pairs()
print provider.security.list_security_groups()
