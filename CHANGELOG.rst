1.0.0 - Aug ??, 2018. (sha ??)
-------

* Added Microsoft Azure as a provider
* Restructured the interface to make it more comprehensible and uniform across
  all supported providers. See `issue #69 <https://github.com/CloudVE/cloudbridge/issues/69>`_
  for more details as well as the library layout image for an easy visual
  reference: http://cloudbridge.cloudve.org/en/v1.0.0/#quick-reference.
* Migrated AWS implementation to use boto3 library from boto (thanks @01000101)
* Cleaned up use of ``name`` property for resources. Resources now have ``id``,
  ``name``, and ``label`` properties to represent respectively: a unique
  identifier supplied by the provider; a descriptive, unchangeable name; and a
  user-supplied label that can be modified during the existence of a resource.
* Added enforcement of name and label value: names must be less than 64 chars
  in length and consist of only lower case letters and dashes
* Refactored tests and extracted standard interface tests where all resources
  are being tested using the same code structure. Also, tests will run only
  for providers that implement a given service.
* When deleting an OpenStack network, clear any ports
* Added support for launching OpenStack instances into a specific subnet
* Update image list interface to allow filtering by owner
* When listing images on AWS, filter only the ones by current account owner
* Retrieve AWS instance types from a public service to include latest values
* Instance state uses ``DELETED`` state instead of ``TERMINATED``
* Return VM type RAM in GB
* Add implementation for ``generate_url`` on OpenStack
* General documentation updates

0.3.3 - Aug 7, 2017. (sha 348e1e88935f61f53a83ed8d6a0e012a46621e25)
-------

* Remove explicit versioning of requests and Babel

0.3.2 - June 10, 2017. (sha f07f3cbd758a0872b847b5537d9073c90f87c24d)
-------

* Patch release to support files>5GB with OpenStack (thanks @MartinPaulo)
* Misc bug fixes

0.3.1 - April 18, 2017. (sha f36a462e886d8444cb2818f6573677ecf0565315)
-------

* Patch for binary file handling in OpenStack

0.3.0 - April 11, 2017. (sha 13539ccda9e4809082796574d18b1b9bb3f2c624)
-------

* Reworked test framework to rely on tox's test generation features. This
  allows for individual test cases to be run on a per provider basis.
* Added more OpenStack swift config options (OS_AUTH_TOKEN and OS_STORAGE_URL)
* Added supports for accessing EC2 containers with restricted permissions.
* Removed exists() method from object store interface. Use get()==None check
  instead.
* New method (img.min_disk) for getting size of machine image.
* Test improvements (flake8 during build, more tests)
* Misc bug fixes and improvements
* Changed library to beta state
* General documentation updates (testing, release process)

0.2.0 - March 23, 2017. (sha a442d96b829ea2c721728520b01981fa61774625)
-------

* Reworked the instance launch method to require subnet vs. network. This
  removed the option of adding network interface to a launch config object.
* Added object store methods: upload from file path, list objects with a
  prefix, check if an object exists, (AWS only) get an accessible URL for an
  object (thanks @VJalili)
* Modified `get_ec2_credentials()` method to `get_or_create_ec2_credentials()`
* Added an option to read provider config values from a file
  (`~/.cloudbridge` or `/etc/cloudbridge`)
* Replaced py35 with py36 for running tests
* Added logging configuration for the library
* General documentation updates


0.1.1 - Aug 10, 2016. (sha 0122fb1173c88ae64e40140ffd35ff3797e9e4ad)
-------

* For AWS, always launch instances into private networking (i.e., VPC)
* Support for using OpenStack Keystone v3
* Add functionality to manipulate routers and routes
* Add FloatingIP resource type and integrate with Network service
* Numerous documentation updates
* For an OpenStack provider, add method to get the ec2 credentials for a user


0.1.0 - Jan 30, 2016.
-------

* Initial release of CloudBridge
* Support for Bucket, Instance, Instance type, Key pair, Machine image
  Region, Security group, Snapshot, Volume, Network and Subnet services
* Support for paging results, block device mapping and launching into VPCs
* Support for AWS and OpenStack clouds
* Basic usage docs and complete API docs
* 95% test coverage
* Support for AWS mock test provider (via
  `moto <https://github.com/spulec/moto>`_)
