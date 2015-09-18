# libcloudbridge
libcloudbridge provides a layer of abstraction over different cloud providers. It's a straightfoward implementation of
the bridge pattern.

Usage example
```python
from cloudbridge.providers.interfaces import CloudProviderFactory
from cloudbridge.util import Bunch

config = Bunch(access_key='a_key',
               secret_key='s_key')

provider = CloudProviderFactory().create_provider(ProviderList.EC2, config)
print provider.Security.list_key_pairs()
```
