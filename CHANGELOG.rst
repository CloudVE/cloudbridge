4.4.1 - August 21, 2026 (sha 093ef669598d9f324be28d400a851396739cf1d8)
----------------------------------------------------------------------

## Fixes
* **``cryptography`` is now declared as a dependency.**
  ``cloudbridge.base.helpers`` imports it at module scope, and almost
  everything imports that module, so it was required for the library to
  import at all - but it appeared nowhere in ``pyproject.toml``. A plain
  ``pip install cloudbridge`` therefore produced an installation that raised
  ``ModuleNotFoundError: No module named 'cryptography'`` on
  ``import cloudbridge.base.resources``, as did ``cloudbridge[aws]``, since
  boto3 does not depend on it either. Installations that worked did so
  because something else in the environment happened to provide it. This
  affected 4.4.0 and earlier; the import has been there since 2019.

## Build and CI
* **A new ``Bare install imports`` job builds the wheel, installs it with no
  extras, and imports the modules a user reaches for first.** Every test
  environment installs the ``[dev]`` extra, which pulls in the provider SDKs
  and their transitive dependencies, so the suite passed against a package
  whose declared dependencies were incomplete. The job runs from outside the
  repository, so the source tree cannot satisfy the import in place of the
  installed wheel.

## Pull Requests
* Declare cryptography as a dependency, and guard bare installs by @nuwang in https://github.com/CloudVE/cloudbridge/pull/347

**Full Changelog**: https://github.com/CloudVE/cloudbridge/compare/v4.4.0...v4.4.1

4.4.0 - August 21, 2026 (sha 55d925d56eaad247b960ad00e636253637192549)
----------------------------------------------------------------------

## Release highlights
``BucketObject.iter_content`` becomes a real chunked stream on every provider:
it takes a ``chunk_size``, yields chunks sized by that rather than by the
content, and no longer materialises a whole object in memory anywhere.
Separately, two pathological patterns in AWS listing are removed - an image
search that scanned the region's entire public catalogue, and a paginated
call that used the caller's result limit as its transport page size.

## Enhancements
* **``iter_content`` and ``save_content`` accept a ``chunk_size``.** It
  defaults to 1 MiB and is settable globally through the ``iter_chunk_size``
  provider config value or the ``CB_ITER_CHUNK_SIZE`` environment variable,
  alongside the existing ``CB_MULTIPART_*`` knobs. Previously the read size
  was hardcoded and inconsistent - 4 KiB on AWS, 64 KiB on OpenStack Swift,
  the service's own chunking on Azure - and callers had no way to change it.
  The AWS value dated from the 2017 boto2-to-boto3 migration, where a
  ``BucketObjIterator`` shim replaced boto2's ``Key`` (which read in 8 KiB
  ``BufferSize`` chunks); it was never a tuning decision. Reading an HTTP body
  at 1 MiB measures ~12x cheaper per byte than at 4 KiB, and the curve is flat
  from 1 MiB up, so larger defaults would only cost memory. Note that
  ``save_content`` was never affected: it copied via ``shutil.copyfileobj``,
  which reads in 64 KiB blocks regardless.
* **New ``aws_page_size`` configuration value.** How many records to request
  from AWS per call while satisfying a list method, defaulting to 500. It is
  a transport setting, distinct from ``default_result_limit``, which bounds
  how many results the caller receives; the two used to be the same number.
  It is clamped to what the service permits for the call in hand, so a value
  outside those bounds is adjusted rather than rejected. AWS-specific
  because it only means anything where the provider walks pages itself:
  GCP, Azure and OpenStack each return a single page plus a continuation
  token and let the caller drive.

## Fixes
* **The default network is created with the configured default CIDR.**
  ``BaseNetworkService.get_or_create_default`` passed a hardcoded
  ``10.0.0.0/16`` instead of ``BaseNetwork.CB_DEFAULT_IPV4RANGE``, so setting
  ``CB_DEFAULT_IPV4RANGE`` was silently ignored on Azure and OpenStack, which
  inherit the base implementation. AWS and GCP override it and were already
  correct.
* **Azure no longer splits object content on newlines.** ``iter_content``
  returned an ``io.RawIOBase`` wrapper, and iterating a raw stream calls
  ``readline()`` - so chunks broke at ``b"\n"`` at whatever sizes the content
  happened to dictate, and a blob with no newline in it was buffered whole
  however large it was. It now yields ``chunk_size`` chunks read over a single
  connection.
* **GCP no longer loads the entire object into memory.** ``iter_content``
  returned ``io.BytesIO`` wrapped around a full ``get_media().execute()``, so
  streaming a large object cost its full size in RAM (and, being a
  ``BytesIO``, also iterated by line). Content is now fetched as successive
  ranged reads of ``chunk_size`` bytes, keeping memory flat at one chunk.
  ``download_to_file`` remains the faster path for downloading to disk, as it
  fetches ranges in parallel.
* **``save_content`` no longer requires ``iter_content`` to return a
  file-like object.** It copied with ``shutil.copyfileobj``, which needs a
  ``.read()`` that the interface never promised - only ``Iterable[bytes]``. It
  now writes the iterated chunks directly, so a provider returning a plain
  generator works.
* **``AWSImageService.find`` no longer scans every public image to run its
  tag search.** ``find(label=...)`` issues two ``describe_images`` calls, one
  filtered on ``name`` and one on ``tag:Name``, and neither was scoped by
  ``Owners``. The ``tag:Name`` half can only ever match images in the calling
  account - AMI tags are not visible across accounts, so an image owned by
  anyone else cannot satisfy the filter however it is tagged - so omitting
  ``Owners`` never widened what it could find. It only made EC2 evaluate the
  filter against the whole regional catalogue: measured in ap-southeast-1,
  10.0s unscoped against 0.1s scoped, for identical single-image results.
  The ``name`` half is unchanged and still searches public images, which is
  what most callers want; an explicit ``owners`` argument still overrides
  both.
* **Paginated AWS calls no longer use the caller's result limit as the
  transport page size.** ``BotoEC2Service._get_paginated_results`` set
  ``PaginationConfig={'MaxItems': limit, 'PageSize': limit}``, conflating how
  many results the caller wants with how many the service returns per
  request. Against a scan that matches sparsely that walks the collection in
  tiny increments: the same filtered ``describe_images`` took 977.6s at a
  page size of 5 and 10.0s at 1000, for one result either way. ``MaxItems``
  still bounds what the caller receives; ``PageSize`` is now a full page,
  clamped to whatever bounds the service model declares for the operation
  (``DescribeRouteTables`` permits 100 where most permit more, several require
  at least 5, and falling outside them is a hard ``InvalidParameterValue``).
  Since ``DEFAULT_RESULT_LIMIT`` is 50, every paginated AWS call was affected,
  not just filtered searches.

## Backward compatibility
``chunk_size`` is optional everywhere, so existing calls keep working. The
AWS return value still exposes ``read``/``close`` as before. The Azure and GCP
return values are now plain generators: code that called ``.read()`` on them
must iterate instead, or use ``save_content``/``download_to_file``.

## Pull Requests
* Make iter_content a chunked stream with a configurable chunk size by @nuwang in https://github.com/CloudVE/cloudbridge/pull/343
* Create the default network with the configured default CIDR by @nuwang in https://github.com/CloudVE/cloudbridge/pull/344
* Instrument the cloud suites to find where the AWS time goes by @nuwang in https://github.com/CloudVE/cloudbridge/pull/345
* Fix the two effects behind the AWS suite's runtime: unscoped tag search and transport page size by @nuwang in https://github.com/CloudVE/cloudbridge/pull/346

**Full Changelog**: https://github.com/CloudVE/cloudbridge/compare/v4.3.1...v4.4.0

4.3.1 - August 2, 2026 (sha 8fabc1e2d3916e2c100bdb18075f2caa3bd38b38)
---------------------------------------------------------------------

## Release highlights
This point release makes downloads safe when the destination path is written
concurrently, and removes two pathological API-call patterns in the AWS
provider that dominated integration test runtimes - listing VM types and
waiting on Route53 record changes. Fully backward compatible with 4.3.0 - no
code changes are required.

## Fixes
* **AWS VM type listings no longer refetch the whole catalogue for every
  page.** EC2 offers no server-side paging for instance types, so
  ``AWSVMTypeService.list`` materialises the full catalogue and pages it
  client-side. It previously refetched that catalogue on every call - one
  ``DescribeInstanceTypeOfferings`` walk plus a ``DescribeInstanceTypes`` call
  per 100 types, about 14 API calls - which made walking the pages of a full
  listing quadratic in API calls. Walking all 1343 types offered in
  ``us-east-1a`` at a result limit of 5 cost roughly 4300 API calls; it now
  costs 14. The catalogue is memoised per availability zone for the lifetime
  of the provider.
* **AWS DNS record changes no longer wait a full 30 seconds each.** Creating
  or deleting a record blocks until Route53 reports the change INSYNC, using
  boto3's ``resource_record_sets_changed`` waiter. That waiter polls every 30
  seconds by default, so a change that propagated in a few seconds still cost
  a full 30. Measured against Route53, INSYNC was reached inside the first
  poll interval every time, making the granularity the entire cost. The
  waiter now polls every 5 seconds while keeping the same ~30 minute ceiling.
* **Downloads no longer assemble the object at the destination path.**
  ``BucketObject.download_to_file`` builds the file out of the way and moves it
  into place once complete, so the destination only ever holds a whole object.
  Previously the generic ranged driver (used by GCP and OpenStack Swift)
  created the destination up front and reopened it for every range, so anything
  that replaced that path mid-transfer - notably a second download of the same
  object to the same path, as a download cache does - could truncate the
  in-progress file or make the next range fail with ``FileNotFoundError``. A
  failed transfer no longer deletes an existing file at the destination either,
  and the Azure downloader (which wrote in place) gains the same guarantee.
  Ranges are now also written through a single file handle rather than
  reopening the path per range.

## Build and CI
* The AWS cloud integration job now requests a 3 hour OIDC session instead of
  relying on the 1 hour default. The credentials are exported to tox as static
  environment variables and cannot be refreshed mid-run, so a suite that ran
  past the hour failed its remaining tests with ``RequestExpired`` - and,
  because cleanup handlers need working credentials too, leaked the instances
  and images those tests had created. Requires the IAM role's
  ``MaxSessionDuration`` to permit the longer session.

## Pull Requests
* Never assemble a download at its destination path by @nuwang in https://github.com/CloudVE/cloudbridge/pull/341
* Cut AWS integration suite runtime and stop credentials expiring mid-run by @nuwang in https://github.com/CloudVE/cloudbridge/pull/342

**Full Changelog**: https://github.com/CloudVE/cloudbridge/compare/v4.3.0...v4.3.1

4.3.0 - July 11, 2026 (sha 863d0c8297e74e62a72b98643952f9a923807b7b)
--------------------------------------------------------------------

## Release highlights
This release adds cross-provider ranged, parallel downloads, completing the
transfer story started with 4.2.0's multipart uploads. Fully backward
compatible — no code changes are required.

## What's new
* **Cross-provider ranged, parallel downloads.** The new
  ``BucketObject.download_to_file`` fetches objects larger than the configured
  threshold as ranged reads of ``part_size`` bytes, up to ``max_concurrency``
  parts in parallel, so large downloads are no longer bound to a single
  connection (and the whole object is never held in memory). AWS delegates to
  boto3's TransferManager and Azure to azure-storage-blob's concurrent
  downloader; GCP and OpenStack Swift use CloudBridge's generic driver, which
  fetches ranges in parallel via cloned providers. A new
  ``BucketObjectService.download_range`` primitive is also available directly
  for partial reads. The per-call ``TransferConfig`` knobs (threshold, part
  size, concurrency) now tune transfers in both directions — pass a different
  instance per call to tune uploads and downloads differently.

## Pull Requests
* Add cross-provider ranged, parallel downloads by @nuwang in https://github.com/CloudVE/cloudbridge/pull/340

**Full Changelog**: https://github.com/CloudVE/cloudbridge/compare/v4.2.1...v4.3.0

4.2.1 - July 10, 2026 (sha f06765d1100ec461908396475a4510460843a65c)
--------------------------------------------------------------------

## Release highlights
This point release lowers the supported Python floor to 3.10 and adds
response-header overrides to signed object URLs. Fully backward compatible
with 4.2.0 — no code changes are required.

## What's new
* **Supported Python floor lowered to 3.10.** ``requires-python`` was ``>=3.13``
  since the PEP 621 packaging migration, but nothing in the codebase or its
  dependencies needs more than 3.10. CloudBridge now installs on Python
  3.10–3.13, and CI runs the mock-provider suite on both the lowest and highest
  supported versions. ``mypy`` type-checks against 3.10 so newer-stdlib usage
  is caught at lint time.
* **Response-header overrides on signed URLs.** ``BucketObject.generate_url`` now
  accepts optional ``content_disposition`` and ``content_type`` parameters that ask
  the backing store to serve the object with those response headers on GET. Honored
  fully by AWS, Azure and GCP; OpenStack Swift honors the filename portion of the
  disposition via its tempurl ``filename`` parameter (the content type cannot be
  overridden). Both are ignored for writable URLs.

## Pull Requests
* Lower supported Python floor to 3.10 by @nuwang in https://github.com/CloudVE/cloudbridge/pull/338
* Add response-header overrides to BucketObject.generate_url by @nuwang in https://github.com/CloudVE/cloudbridge/pull/339

**Full Changelog**: https://github.com/CloudVE/cloudbridge/compare/v4.2.0...v4.2.1


4.2.0 - July 9, 2026 (sha 60dbe305f0af46a7ce3eadd093756d31b8131b2e)
-------------------------------------------------------------------

## Release highlights
This release makes CloudBridge's entire public API strongly typed (shipped with a
PEP 561 ``py.typed`` marker), adds cross-provider multipart upload for large objects,
and removes the long-deprecated ``deprecation`` dependency along with the deprecated
APIs it supported.

## What's new
* **Comprehensive type hints.** The whole public interface is now annotated and ships a
  PEP 561 ``py.typed`` marker, so downstream users get a fully-typed API even though the
  underlying cloud SDKs are untyped. A ``mypy`` check runs in CI — the interface and base
  layers under a strict bar, and the SDK-wrapping providers under a pragmatic tier.
* **Cross-provider multipart upload.** Large object uploads now use multipart transfer
  with per-call ``TransferConfig`` knobs (threshold, part size, concurrency), with parts
  uploaded in parallel via cloned providers.

## Breaking changes
* Removed the ``deprecation`` dependency and the long-expired deprecated APIs it
  supported (both marked ``removed_in=2.0``):

  * the ``network_id=`` keyword alias on ``security.vm_firewalls.create`` — use
    ``network=`` instead;
  * the ``AZURE_VM_DEFAULT_USER_NAME`` environment/config variable — use
    ``AZURE_VM_DEFAULT_USERNAME`` instead.

## Fixes and maintenance
* Typing surfaced and fixed several latent provider issues: Azure ``Volume.source`` now
  resolves to a ``Snapshot`` object, the Azure multi-firewall merge on launch passes the
  required network, and Azure ``parse_url`` reports a meaningful parameter on error.
* GCP volume attach/detach now waits for the operation to complete, and the attachments
  check was corrected.
* Reconciled numerous cross-provider return-type and behaviour inconsistencies to match
  the interface — e.g. ``start``/``stop``/``delete`` return ``None`` consistently,
  firewall-rule ``direction`` returns the ``TrafficDirection`` enum, and fatal missing-id
  paths raise ``ProviderInternalException`` instead of returning ``None``.

## Build and CI
* Added a ``mypy`` tox environment (``tox -e mypy``) and a CI step; the ``lint``
  environment now also enforces import order via ``flake8-import-order``.

## Pull Requests
* Add cross-provider multipart upload support by @nuwang in https://github.com/CloudVE/cloudbridge/pull/333
* Wait for GCP volume attach/detach operations; fix attachments check by @nuwang in https://github.com/CloudVE/cloudbridge/pull/334
* Add comprehensive typing to cloudbridge + mypy tox check by @nuwang in https://github.com/CloudVE/cloudbridge/pull/335
* Remove the deprecation dependency and long-expired deprecated APIs by @nuwang in https://github.com/CloudVE/cloudbridge/pull/336
* Fix latent provider bugs surfaced during the typing work by @nuwang in https://github.com/CloudVE/cloudbridge/pull/337

**Full Changelog**: https://github.com/CloudVE/cloudbridge/compare/v4.1.0...v4.2.0


4.1.0 - June 15, 2026 (sha 4d7999ac8785bececaa62964d25f4f552df7c3a0)
---------------------------------------------------------------------

## Release highlights
This minor release adds Azure DNS support and modernizes the release pipeline. The public CloudBridge
API is backward compatible with 4.0 — no code changes are required.

## What's new
* **Azure DNS support.** The Azure provider can now manage DNS zones and records, bringing it in line
  with the DNS service already offered by the other providers. This adds ``azure-mgmt-dns`` to the
  Azure dependency set.

## Fixes and maintenance
* Azure disks now use the region name (not the zone name) when resolving their location.
* Test reliability: retry default-subnet creation, and allow storage-account creation enough time to
  resolve DNS.

## Build and CI
* PyPI releases now use a trusted publisher (PyPI OIDC) from GitHub Actions instead of a stored API
  token. The deploy workflow is split into separate build and publish jobs, and integration runs are
  skipped on docs-only changes.

## Pull Requests
* Use a trusted publisher when publishing to PyPI by @ksuderman in https://github.com/CloudVE/cloudbridge/pull/330
* Add Azure DNS support by @nuwang in https://github.com/CloudVE/cloudbridge/pull/331
* CI hygiene: split deploy job + dedicated env, skip CI on docs-only changes by @nuwang in https://github.com/CloudVE/cloudbridge/pull/332

**Full Changelog**: https://github.com/CloudVE/cloudbridge/compare/v4.0.0...v4.1.0


4.0.0 - May 15, 2026 (sha 4963adc3f5f10cd885640138062800d7cd20e93a)
---------------------------------------------------------------------

## Release highlights
This is a major release that brings the dependency stack up to date. The public CloudBridge API is unchanged —
most users will not need any code changes. The version bump reflects the breadth of the underlying modernization
rather than interface breakage.

## What users should know
Python 3.13 or higher is now required. Support for older Python versions, including 2.7 compatibility
shims (``six``), has been removed. Earlier Python versions are no longer tested; the default test environment
is Python 3.13.

Azure public IPs now use the Standard SKU. Basic-SKU public IPs are being retired by Azure. Public IPs created
by CloudBridge are now Standard SKU. Within a single virtual network, public IPs of different SKUs cannot be
mixed (Azure restriction). If you have a network that already contains Basic-SKU IPs created by CloudBridge 3.x,
plan to standardize on one SKU before letting 4.0 add new IPs to that network.

Mock provider now requires moto >= 5.0. If you use MockAWSCloudProvider in your own test suite alongside direct
moto usage, your test harness must be on moto 5. In moto 5, the per-service decorators (mock_ec2, mock_s3, …) were
unified into a single mock_aws.

If you pin cloud SDKs alongside CloudBridge, you may need to relax upper bounds. The biggest jumps:
azure-mgmt-compute (up to <39), azure-mgmt-network (<31), openstacksdk (<5).

### Under the hood (no action required)
CloudBridge migrated off several abandoned Azure libraries (msrestazure, azure-cosmosdb-table, pysftp) and onto their
maintained successors. The migration is transparent at the API level. Existing Azure resources created by
3.x — including key pairs stored in Azure Table Storage — are read by 4.0 without migration.

## Pull Requests
* Update codecov badge by @nuwang in https://github.com/CloudVE/cloudbridge/pull/319
* pull_request to pull_request_target for tests by @almahmoud in https://github.com/CloudVE/cloudbridge/pull/322
* Azure - add AZURE_NETWORK_RESOURCE_GROUP to pick vnet from another ResourceGroup by @patchkez in https://github.com/CloudVE/cloudbridge/pull/321
* Run in pull_request mode with approval by @nuwang in https://github.com/CloudVE/cloudbridge/pull/327
* Upgrade azure, openstack sdks and moto to latest by @nuwang in https://github.com/CloudVE/cloudbridge/pull/323
* Modernize project setup by @nuwang in https://github.com/CloudVE/cloudbridge/pull/328

## New Contributors
* @patchkez made their first contribution in https://github.com/CloudVE/cloudbridge/pull/321

**Full Changelog**: https://github.com/CloudVE/cloudbridge/compare/v3.2.0...v4.0.0


3.2.0 - September 06, 2023 (sha dd7ccbba9457232880da755ca66f8ae9d2e7dce4)
---------------------------------------------------------------------

* Use external non-shared network for gateway by @almahmoud in https://github.com/CloudVE/cloudbridge/pull/307
* Install cloudbridge full in examples by @nuwang in https://github.com/CloudVE/cloudbridge/pull/310
* Add new `ec2_retries_value` config for  `AWSCloudProvider` by @MosheFriedland in https://github.com/CloudVE/cloudbridge/pull/313
* Add packaging action by @nuwang in https://github.com/CloudVE/cloudbridge/pull/314
* Fix linting error in resource comparison by @nuwang in https://github.com/CloudVE/cloudbridge/pull/315
* Fix tox syntax and branch references by @nuwang in https://github.com/CloudVE/cloudbridge/pull/316
* Switch to pytest by @nuwang in https://github.com/CloudVE/cloudbridge/pull/317
* Update tox syntax and pin min tox version by @nuwang in https://github.com/CloudVE/cloudbridge/pull/318

3.1.0 - August 19, 2022 (sha 28067e22377a60423e7fcf4f995ce224307b8b09)
---------------------------------------------------------------------

* Added app credentials support to openstack.
* Added VM instance create time property to all providers (thanks to @rodrigonull)
* Added Azure stop VM instance method (thanks to @rodrigonull)
* Cloud provider sdks updated to latest versions
* Other misc fixes.

3.0.0 - December 3, 2021 (sha 327e330bed78b8b70c9ff9d256513d71bc27545f)
---------------------------------------------------------------------

* This is a major release due to packaging changes, although there are no backward incompatible interface changes.
* The cloudbridge package no longer installs any providers by default, and you must use `pip install cloudbridge[full]`
  instead of `pip install cloudbridge` to obtain previous behaviour. This is to allow greater control over what
  providers are installed. To install only specific providers, use `pip install cloudbridge[aws,gcp]` etc. #292
  (thanks to @RyanSiu1995)
* Allow users to create signed urls with write permissions #294 (thanks to @FabioRosado)

2.2.0 - November 5, 2021 (sha f3fb8e18781cd3ede4509ef75a69e7c2a420a167)
---------------------------------------------------------------------

* This is a maintenance release with no backward incompatible changes.
* Azure dependencies updated to latest version and associated fixes #274, #277, #278, #279, #281, #282
  (thanks to @FabioRosado)
* AWS, GCP and OpenStack dependencies updated to latest versions and associated fixes.
* AWS resources use TagSpecification support, removing extra requests for initial tagging.
* Fixed wrong logging object in cloud provider #272 (thanks to @MosheFriedland)
* Switched to github actions from travis
* Patch discovery.build calls in GCP provider to use google's improved httplib2 #263 (thanks to @selshowk)
* Added feature to start and stop aws instance #271 (thanks to @abhi005)
* Miscellaneous doc and maintenance fixes.

2.1.0 - December 1, 2020 (sha a5c3af8ebc5be3ed44db34ebba097848f17305fb)
---------------------------------------------------------------------

* This release introduces the DNS service, which is a top level service for managing DNS zones and records.
* Support for using the newly added AWS instance type offerings API. This removes the dependency on a static machine
  type list, and returns up-to-date information on instance type availability.
* The default package no longer bundles Azure, as the Azure python libraries are very large and affects docker
  container size when using cloudbridge. To install with Azure, use `pip install cloudbridge[full]` or
  `pip install cloudbridge[azure]`.
* A convenience method for cloning providers in different zones has been added, which helps with multi-zone operations.
* Support for specifying s3 signature version for the AWS provider.
* Miscellaneous bug fixes and error handling improvements.
* Support for python<3 dropped.
* No major backward incompatible changes (apart from Azure not being bundled by default)


2.0.0 - March 13, 2019 (sha 10e28a0d07251af4a424fcbf11435fa4d52e5277)
---------------------------------------------------------------------

* This is a major release which contains many improvements and some breaking
  changes to the interface, but the changes are fairly straightforward.
* Support for Google Cloud (thanks to @mbookman, @chiniforooshan, @baizhang)
* Support for middleware, event listening and interception, allowing
  CloudBridge to be extended without needing to modify library code (This is
  also potentially useful for handling corner cases for specific clouds).
* The mock provider is now available by default as a standard cloud provider,
  which is useful for testing applications that use CloudBridge.
* Providers now operate in a single zone, and therefore, all methods that
  previously required the zone as a parameter no longer do. Specifically,
  ``instance.create()``, ``volume.create()``, ``subnet.create``,
  ``subnet.get_or_create_default()`` are affected in services,
  and ``snap.create_volume`` is affected in resources. The provider's default
  zone must now be specified through the provider config.
* All exceptions that are generated by CloudBridge will now extend from
  ``CloudBridgeBaseException``
* The cloud package is deprecated and everything under it has been moved
  one level up. For example, instead of
  ``from cloudbridge.cloud.factory import CloudProviderFactory`` use
  ``from cloudbridge.factory import CloudProviderFactory``.
* Services are much more uniform now, and sub-services have been introduced
  for greater uniformity. For example, ``net.create_subnet()`` is now
  ``net.subnets.create()``
* ``gateways.get_or_create_inet_gateway()`` is now simply
  ``gateways.get_or_create()``
* AWS instance types are now served through Amazon CloudFront for better
  performance.
* Miscellaneous bug fixes and improvements.

1.0.2 - September 25, 2018 (sha 621aeed1a8d7c5ad270649f8ee960e9682e57dae)
-------------------------------------------------------------------------
* Added AWS instance types caching for better performance
* Added ``router.subnets`` property
* Ensure the default network for CloudBridge on AWS has subnets

1.0.1 - September 7, 2018. (sha 3130492008c5e0e115b8dfec880d32a4ac90b761)
-------------------------------------------------------------------------
* Fixed minor bug when retrieving buckets with only limited access.
* Relaxed some library version dependencies (e.g. six).

1.0.0 - September 6, 2018. (sha 11bccd822f21a598fc753995440cf1a409984889)
-------------------------------------------------------------------------

* Added Microsoft Azure as a provider.
* Restructured the interface to make it more comprehensible and uniform across
  all supported providers. See `issue #69 <https://github.com/CloudVE/cloudbridge/issues/69>`_
  for more details as well as the library layout image for an easy visual
  reference: https://github.com/CloudVE/cloudbridge#quick-reference.
* Migrated AWS implementation to use the boto3 library (thanks @01000101)
* Cleaned up use of ``name`` property for resources. Resources now have ``id``,
  ``name``, and ``label`` properties to represent respectively: a unique
  identifier supplied by the provider; a descriptive, unchangeable name; and a
  user-supplied label that can be modified during the existence of a resource.
* Added enforcement of name and label value: names must be at least 3 characters
  in length at minimum, and 64 characters at maximum, consisting of only lower
  case letters and dashes. Should not start or end with a dash.
* Refactored tests and extracted standard interface tests where all resources
  are being tested using the same code structure. Also, tests will run only
  for providers that implement a given service.
* Moved the repository from github.com/gvlproject to github.com/cloudve org.
* When deleting an OpenStack network, clear any ports.
* Added support for launching OpenStack instances into a specific subnet
* Update image list interface to allow filtering by owner.
* When listing images on AWS, filter only the ones by current account owner.
* Retrieve AWS instance types from a public service to include latest values.
* Instance state uses ``DELETED`` state instead of ``TERMINATED``.
* Return VM type RAM in GB.
* Add implementation for ``generate_url`` on OpenStack.
* General documentation updates.

0.3.3 - August 7, 2017. (sha 348e1e88935f61f53a83ed8d6a0e012a46621e25)
----------------------------------------------------------------------

* Remove explicit versioning of requests and Babel.

0.3.2 - June 10, 2017. (sha f07f3cbd758a0872b847b5537d9073c90f87c24d)
---------------------------------------------------------------------

* Patch release to support files>5GB with OpenStack (thanks @MartinPaulo).
* Misc bug fixes.

0.3.1 - April 18, 2017. (sha f36a462e886d8444cb2818f6573677ecf0565315)
----------------------------------------------------------------------

* Patch for binary file handling in OpenStack.

0.3.0 - April 11, 2017. (sha 13539ccda9e4809082796574d18b1b9bb3f2c624)
----------------------------------------------------------------------

* Reworked test framework to rely on tox's test generation features. This
  allows for individual test cases to be run on a per provider basis.
* Added more OpenStack swift config options (OS_AUTH_TOKEN and OS_STORAGE_URL)
* Added supports for accessing EC2 containers with restricted permissions.
* Removed exists() method from object store interface. Use get()==None check
  instead.
* New method (img.min_disk) for getting size of machine image.
* Test improvements (flake8 during build, more tests).
* Misc bug fixes and improvements.
* Changed library to beta state
* General documentation updates (testing, release process)

0.2.0 - March 23, 2017. (sha a442d96b829ea2c721728520b01981fa61774625)
----------------------------------------------------------------------

* Reworked the instance launch method to require subnet vs. network. This
  removed the option of adding network interface to a launch config object.
* Added object store methods: upload from file path, list objects with a
  prefix, check if an object exists, (AWS only) get an accessible URL for an
  object (thanks @VJalili).
* Modified `get_ec2_credentials()` method to `get_or_create_ec2_credentials()`
* Added an option to read provider config values from a file
  (`~/.cloudbridge` or `/etc/cloudbridge`).
* Replaced py35 with py36 for running tests.
* Added logging configuration for the library.
* General documentation updates.


0.1.1 - Aug 10, 2016. (sha 0122fb1173c88ae64e40140ffd35ff3797e9e4ad)
--------------------------------------------------------------------

* For AWS, always launch instances into private networking (i.e., VPC).
* Support for using OpenStack Keystone v3.
* Add functionality to manipulate routers and routes.
* Add FloatingIP resource type and integrate with Network service.
* Numerous documentation updates.
* For an OpenStack provider, add method to get the ec2 credentials for a user.


0.1.0 - Jan 30, 2016.
---------------------

* Initial release of CloudBridge.
* Support for Bucket, Instance, Instance type, Key pair, Machine image.
  Region, Security group, Snapshot, Volume, Network and Subnet services.
* Support for paging results, block device mapping and launching into VPCs.
* Support for AWS and OpenStack clouds.
* Basic usage docs and complete API docs.
* 95% test coverage.
* Support for AWS mock test provider (via
  `moto <https://github.com/spulec/moto>`_).
