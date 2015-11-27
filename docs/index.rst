.. cloudbridge documentation master file, created by
   sphinx-quickstart on Sat Oct 10 03:17:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CloudBridge's documentation!
=======================================

CloudBridge aims to provide a simple layer of abstraction over
different cloud providers, reducing or eliminating the need to write
conditional code for each cloud.

Usage example
-------------

The simplest possible example for doing something useful with CloudBridge would
look like the following.

.. code-block:: python

	from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

	provider = CloudProviderFactory().create_provider(ProviderList.AWS, {})
	print(provider.compute.instances.list())

In the example above, the AWS_ACCESS_KEY and AWS_SECRET_KEY environment variables
must be set to your cloud credentials.

Quick Reference
---------------

The following object graph shows how to access various provider services, and the resource
that they return. Click on any object to drill down into its details.

.. raw:: html

   <object data="_static/object_relationships_detailed.svg" type="image/svg+xml"></object>

Installation
------------

The latest release can always be installed form PyPI. For other installation
options, see the `installation page <topics/install.html>`_::

    pip install cloudbridge

Documentation
-------------
.. toctree::
    :maxdepth: 2

    concepts.rst
    getting_started.rst
    topics/overview.rst
    api_docs/ref.rst

Page index
----------
* :ref:`genindex`

