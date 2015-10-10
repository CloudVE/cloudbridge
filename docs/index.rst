.. cloudbridge documentation master file, created by
   sphinx-quickstart on Sat Oct 10 03:17:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to cloudbridge's documentation!
=======================================

cloudbridge provides a layer of abstraction over different cloud providers.
It's a straightfoward implementation of the `bridge pattern`_.

Usage example
~~~~~~~~~~~~~

The simplest possible example for doing something useful with cloudbridge would
look like the following.

.. code-block:: python

	from cloudbridge.providers.factory import CloudProviderFactory, ProviderList

	provider = CloudProviderFactory().create_provider(ProviderList.AWS, {})
	print(provider.security.key_pairs.list())

In the example above, the AWS_ACCESS_KEY and AWS_SECRET_KEY environment variables
must be set to your cloud credentials.

Contents:

.. toctree::
   :glob:
   :maxdepth: 2

   api_docs/cloudbridge


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _`bridge pattern`: https://en.wikipedia.org/wiki/Bridge_pattern