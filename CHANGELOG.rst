0.3.0 - April 11, 2017. (sha 13539ccda9e4809082796574d18b1b9bb3f2c624)
-------

* Reworked test framework to rely on tox's test generation features. This
  allows for individual test cases to be run on a per provider basis.
* Added more OpenStack swift config options (OS_AUTH_TOKEN and OS_STORAGE_URL)
* Added supports for accessing EC2 containers with restricted permissions.
* Removed exists() method from object store interface. Use get()==None check
  instead.
* New method (img.min_disk) for geting size of machine image.
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
* Support for AWS mock test provder (via
  `moto <https://github.com/spulec/moto>`_)
