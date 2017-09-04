CloudBridge aims to provide a simple layer of abstraction over
different cloud providers, reducing or eliminating the need to write
conditional code for each cloud.

.. image:: https://landscape.io/github/gvlproject/cloudbridge/master/landscape.svg?style=flat
   :target: https://landscape.io/github/gvlproject/cloudbridge/master
   :alt: Landscape Code Health

.. image:: https://coveralls.io/repos/gvlproject/cloudbridge/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/gvlproject/cloudbridge?branch=master
   :alt: Code Coverage

.. image:: https://travis-ci.org/gvlproject/cloudbridge.svg?branch=master
   :target: https://travis-ci.org/gvlproject/cloudbridge
   :alt: Travis Build Status

.. image:: https://codeclimate.com/github/gvlproject/cloudbridge/badges/gpa.svg
   :target: https://codeclimate.com/github/gvlproject/cloudbridge
   :alt: Code Climate

.. image:: https://img.shields.io/pypi/v/cloudbridge.svg
   :target: https://pypi.python.org/pypi/cloudbridge/
   :alt: latest version available on PyPI

.. image:: https://readthedocs.org/projects/cloudbridge/badge/?version=latest
   :target: http://cloudbridge.readthedocs.org/en/latest/?badge=latest
   :alt: Documentation Status


Installation
~~~~~~~~~~~~
Install the latest release from PyPi:

.. code-block:: shell

  pip install cloudbridge

For other installation options, see the `installation page`_ in
the documentation.


Usage example
~~~~~~~~~~~~~

To `get started`_ with CloudBridge, export your cloud access credentials
(e.g., AWS_ACCESS_KEY and AWS_SECRET_KEY for your AWS credentials) and start
exploring the API:

.. code-block:: python

  from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

  provider = CloudProviderFactory().create_provider(ProviderList.AWS, {})
  print(provider.security.key_pairs.list())


Citation
~~~~~~~~

N. Goonasekera, A. Lonie, J. Taylor, and E. Afgan,
"CloudBridge: a Simple Cross-Cloud Python Library,"
presented at the Proceedings of the XSEDE16 Conference on Diversity, Big Data, and Science at Scale, Miami, USA, 2016.
DOI: http://dx.doi.org/10.1145/2949550.2949648


Documentation
~~~~~~~~~~~~~
Documentation can be found at https://cloudbridge.readthedocs.org.


Quick Reference
~~~~~~~~~~~~~~~
The following object graph shows how to access various provider services, and the resource
that they return.

.. image:: http://cloudbridge.readthedocs.org/en/latest/_images/object_relationships_detailed.svg
   :target: http://cloudbridge.readthedocs.org/en/latest/?badge=latest#quick-reference
   :alt: CloudBridge Quick Reference


Design Goals
~~~~~~~~~~~~

1. Create a cloud abstraction layer which minimises or eliminates the need for
   cloud specific special casing (i.e., Not require clients to write
   ``if EC2 do x else if OPENSTACK do y``.)

2. Have a suite of conformance tests which are comprehensive enough that goal
   1 can be achieved. This would also mean that clients need not manually test
   against each provider to make sure their application is compatible.

3. Opt for a minimum set of features that a cloud provider will support,
   instead of  a lowest common denominator approach. This means that reasonably
   mature clouds like Amazon and OpenStack are used as the benchmark against
   which functionality & features are determined. Therefore, there is a
   definite expectation that the cloud infrastructure will support a compute
   service with support for images and snapshots and various machine sizes.
   The cloud infrastructure will very likely support block storage, although
   this is currently optional. It may optionally support object storage.

4. Make the CloudBridge layer as thin as possible without compromising goal 1.
   By wrapping the cloud provider's native SDK and doing the minimal work
   necessary to adapt the interface, we can achieve greater development speed
   and reliability since the native provider SDK is most likely to have both
   properties.


Contributing
~~~~~~~~~~~~
Community contributions for any part of the project are welcome. If you have
a completely new idea or would like to bounce your idea before moving forward
with the implementation, feel free to create an issue to start a discussion.

Contributions should come in the form or a pull request. We strive for 100% test
coverage so code will only be accepted if it comes with appropriate tests and it
does not break existing functionality. Further, the code needs to be well
documented and all methods have docstrings. We are largely adhering to the
`PEP8 style guide`_ with 80 character lines, 4-space indentation (spaces
instead of tabs), explicit, one-per-line imports among others. Please keep the
style consistent with the rest of the project.

Conceptually, the library is laid out such that there is a factory used to
create a reference to a cloud provider. Each provider offers a set of services
and resources. Services typically perform actions while resources offer
information (and can act on itself, when appropriate). The structure of each
object is defined via an abstract interface (see
``cloudbridge/providers/interfaces``) and any object should implement the
defined interface. If adding a completely new provider, take a look at the
`provider development page`_ in the documentation.


.. _`installation page`: http://cloudbridge.readthedocs.org/en/
   latest/topics/install.html
.. _`get started`: http://cloudbridge.readthedocs.org/en/latest/
    getting_started.html
.. _`PEP8 style guide`: https://www.python.org/dev/peps/pep-0008/
.. _`provider development page`: http://cloudbridge.readthedocs.org/
   en/latest/
    topics/provider_development.html
