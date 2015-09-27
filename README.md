# cloudbridge
cloudbridge provides a layer of abstraction over different cloud providers. It's a straightfoward implementation of
the bridge pattern.

[![Code Climate](https://codeclimate.com/github/gvlproject/libcloudbridge/badges/gpa.svg)](https://codeclimate.com/github/gvlproject/cloudbridge)
[![Code Health](https://landscape.io/github/gvlproject/cloudbridge/master/landscape.svg?style=flat)](https://landscape.io/github/gvlproject/cloudbridge/master)
[![Coverage Status](https://coveralls.io/repos/gvlproject/cloudbridge/badge.svg?branch=master&service=github)](https://coveralls.io/github/gvlproject/cloudbridge?branch=master)
[![Build Status](https://travis-ci.org/gvlproject/cloudbridge.svg?branch=master)](https://travis-ci.org/gvlproject/cloudbridge)
[![Release Status](https://img.shields.io/pypi/status/cloudbridge.svg)](https://pypi.python.org/pypi/cloudbridge/)

Usage example
```python
from cloudbridge.providers.interfaces import CloudProviderFactory
from bunch import Bunch

config = Bunch(access_key='a_key',
               secret_key='s_key')

provider = CloudProviderFactory().create_provider(ProviderList.EC2, config)
print(provider.security.list_key_pairs())
```
