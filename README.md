# cloudbridge
cloudbridge provides a layer of abstraction over different cloud providers. It's a straightfoward implementation of
the bridge pattern.

[![Code Climate](https://codeclimate.com/github/gvlproject/libcloudbridge/badges/gpa.svg)](https://codeclimate.com/github/gvlproject/cloudbridge)
[![Test Coverage](https://codeclimate.com/github/gvlproject/libcloudbridge/badges/coverage.svg)](https://codeclimate.com/github/gvlproject/cloudbridge/coverage)
[![Build Status](https://travis-ci.org/gvlproject/cloudbridge.svg?branch=master)](https://travis-ci.org/gvlproject/cloudbridge)

Usage example
```python
from cloudbridge.providers.interfaces import CloudProviderFactory
from bunch import Bunch

config = Bunch(access_key='a_key',
               secret_key='s_key')

provider = CloudProviderFactory().create_provider(ProviderList.EC2, config)
print(provider.security.list_key_pairs())
```
