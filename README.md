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


## ```python
## from cloudbridge.providers.interfaces import CloudProviderFactory
## from cloudbridge.providers.interfaces import CloudProvider


## ec2driver = CloudProviderFactory().get_interface_V1("EC2")
## provider = ec2driver(access_key="", secret_key="", region="", port="", connection_path="")
## instances = provider.Compute.list_instances()
## regions = provider.Compute.list_regions()
## images = provider.Images.list_images()
## volumes = provider.BlockStore.list_volumes()

## provider.Compute.launch_instance("my_instance", regions[0], images[0])
## ```
