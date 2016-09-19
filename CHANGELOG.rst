0.1.1 - Aug 10, 2016.
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
