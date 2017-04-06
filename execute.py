from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

config = {'azure_subscription_id': '7904d702-e01c-4826-8519-f5a25c866a96',
          'azure_client_Id': '69621fe1-f59f-43de-8799-269007c76b95',
          'azure_secret': 'Orcw9U5Kd4cUDntDABg0dygN32RQ4FGBYyLRaJ/BlrM=',
          'azure_tenant': '75ec242e-054d-4b22-98a9-a4602ebb6027'
          }

provider = CloudProviderFactory().create_provider(ProviderList.AZURE, config)

containers = provider.object_store.find('vhds')
#new_container = provider.object_store.create('mysharedfiles')
print(len(containers))
