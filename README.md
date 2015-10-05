# cloudbridge
cloudbridge provides a layer of abstraction over different cloud providers.
It's a straightfoward implementation of the [bridge pattern](https://en.wikipedia.org/wiki/Bridge_pattern).

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

provider = CloudProviderFactory().create_provider(ProviderList.AWS, config)
print(provider.security.list_key_pairs())
```

### Running tests
To run the test suite locally, install [tox](https://tox.readthedocs.org/en/latest/)
with `pip install tox` and run `tox` command. This will run all the tests for
all the environments defined in file `tox.ini`. In order to properly run the
tests, you should have all the environment variables listed in
`tox.ini` file (under `passenv`) exported.

If you’d like to run the tests on a specific environment only, use a command
like this: `tox -e py27` (or ``python setup.py test`` directly). If you'd
like to run the tests for a specific cloud only, you should export env var
``CB_TEST_PROVIDER`` and specify the desired provider name (e.g., ``aws`` or
``openstack``) and then run the ``tox`` command.

Note that running the tests will create various cloud resources, for which you
may incur costs.
