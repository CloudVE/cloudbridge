# libcloudbridge
libcloudbridge provides a layer of abstraction over different cloud providers. It's a straightfoward implementation of
the bridge pattern.

Usage example
```python
from cloudbridge.providers.interfaces import CloudProviderFactory
from cloudbridge.util import Bunch

config = Bunch(access_key='a_key',
               secret_key='s_key')

ec2 = CloudProviderFactory().get_interface_V1("ec2", config)
print ec2.Security.list_key_pairs()
```
