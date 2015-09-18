from cloudbridge.providers.factory import CloudProviderFactory
from cloudbridge.providers.factory import ProviderList
from bunch import Bunch

config = Bunch(access_key='AKIAJLFOW2JCQVPBVFAA',
               secret_key='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')

provider = CloudProviderFactory().create_provider(ProviderList.EC2, config)
print provider.Security.list_key_pairs()