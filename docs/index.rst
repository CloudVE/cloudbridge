	.. cloudbridge documentation master file, created by
   sphinx-quickstart on Sat Oct 10 03:17:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to cloudbridge's documentation!
=======================================

cloudbridge aims to provide a simple layer of abstraction over
different cloud providers, reducing or eliminating the need to write
conditional code for each cloud.

Usage example
-------------

The simplest possible example for doing something useful with cloudbridge would
look like the following.

.. code-block:: python

	from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

	provider = CloudProviderFactory().create_provider(ProviderList.AWS, {})
	print(provider.compute.instances.list())

In the example above, the AWS_ACCESS_KEY and AWS_SECRET_KEY environment variables
must be set to your cloud credentials.

Installation
------------

**Automatic installation**::

    pip install cloudbridge

**Manual installation**::

	$ git clone https://github.com/gvlproject/cloudbridge.git
	$ cd cloudbridge
	$ python setup.py install

**Developer installation**::

	pip install cloudbridge[dev]

This will install additional libraries required by cloudbridge contributors, such as tox.

**Prerequisites**: Cloudbridge runs on Python 2.7 and higher. Python 3 is recommended.


Documentation
-------------
.. toctree::
    :maxdepth: 2

    concepts.rst
    getting_started.rst
    api_docs/ref.rst

Page index
----------
* :ref:`genindex`

