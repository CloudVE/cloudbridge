from cloudbridge.providers.factory import CloudProviderFactory
from cloudbridge.providers.factory import ProviderList
from bunch import Bunch

config = Bunch(access_key='<ak>',
               secret_key='<sk>')

provider = CloudProviderFactory().create_provider(ProviderList.EC2, config)
print provider.Security.list_key_pairs()