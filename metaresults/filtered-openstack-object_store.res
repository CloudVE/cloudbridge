cloudbridge.test.test_object_store_service.CloudObjectStoreServiceTestCase


Test output
 .......s
----------------------------------------------------------------------
Ran 8 tests in 45.191s

OK (skipped=1)

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 18.2557 s
Function: create at line 580

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   580                                               @dispatch(event="provider.storage.buckets.create",
   581                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   582                                               @profile
   583                                               def create(self, name, location=None):
   584        17        170.0     10.0      0.0          OpenStackBucket.assert_valid_resource_name(name)
   585         7         13.0      1.9      0.0          location = location or self.provider.region_name
   586         7          5.0      0.7      0.0          try:
   587         7   13532923.0 1933274.7     74.1              self.provider.swift.head_container(name)
   588         1          4.0      4.0      0.0              raise DuplicateResourceException(
   589         1          6.0      6.0      0.0                  'Bucket already exists with name {0}'.format(name))
   590         7         20.0      2.9      0.0          except SwiftClientException:
   591         6    2397391.0 399565.2     13.1              self.provider.swift.put_container(name)
   592         6    2325140.0 387523.3     12.7              return self.get(name)

Total time: 3.81699 s
Function: create at line 653

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   653                                               @profile
   654                                               def create(self, bucket, object_name):
   655         5    2103008.0 420601.6     55.1          self.provider.swift.put_object(bucket.name, object_name, None)
   656         5    1713986.0 342797.2     44.9          return self.get(bucket, object_name)

Total time: 3.40633 s
Function: list at line 624

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   624                                               @profile
   625                                               def list(self, bucket, limit=None, marker=None, prefix=None):
   626                                                   """
   627                                                   List all objects within this bucket.
   628                                           
   629                                                   :rtype: BucketObject
   630                                                   :return: List of all available BucketObjects within this bucket.
   631                                                   """
   632         9         62.0      6.9      0.0          _, object_list = self.provider.swift.get_container(
   633         9         48.0      5.3      0.0              bucket.name,
   634         9        264.0     29.3      0.0              limit=oshelpers.os_result_limit(self.provider, limit),
   635         9    3405456.0 378384.0    100.0              marker=marker, prefix=prefix)
   636         9         29.0      3.2      0.0          cb_objects = [OpenStackBucketObject(
   637         9        115.0     12.8      0.0              self.provider, bucket, obj) for obj in object_list]
   638                                           
   639         9         18.0      2.0      0.0          return oshelpers.to_server_paged_list(
   640         9         21.0      2.3      0.0              self.provider,
   641         9         11.0      1.2      0.0              cb_objects,
   642         9        306.0     34.0      0.0              limit)

Total time: 3.30085 s
Function: get at line 607

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   607                                               @profile
   608                                               def get(self, bucket, name):
   609                                                   """
   610                                                   Retrieve a given object from this bucket.
   611                                                   """
   612                                                   # Swift always returns a reference for the container first,
   613                                                   # followed by a list containing references to objects.
   614         9         53.0      5.9      0.0          _, object_list = self.provider.swift.get_container(
   615         9    3300631.0 366736.8    100.0              bucket.name, prefix=name)
   616                                                   # Loop through list of objects looking for an exact name vs. a prefix
   617         9         23.0      2.6      0.0          for obj in object_list:
   618         8         13.0      1.6      0.0              if obj.get('name') == name:
   619         8         32.0      4.0      0.0                  return OpenStackBucketObject(self.provider,
   620         8          7.0      0.9      0.0                                               bucket,
   621         8         91.0     11.4      0.0                                               obj)
   622         1          1.0      1.0      0.0          return None

Total time: 2.72294 s
Function: get at line 534

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   534                                               @dispatch(event="provider.storage.buckets.get",
   535                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   536                                               @profile
   537                                               def get(self, bucket_id):
   538                                                   """
   539                                                   Returns a bucket given its ID. Returns ``None`` if the bucket
   540                                                   does not exist.
   541                                                   """
   542         8         42.0      5.2      0.0          _, container_list = self.provider.swift.get_account(
   543         8    2722653.0 340331.6    100.0              prefix=bucket_id)
   544         8         18.0      2.2      0.0          if container_list:
   545         7         30.0      4.3      0.0              return OpenStackBucket(self.provider,
   546         7         14.0      2.0      0.0                                     next((c for c in container_list
   547         7        172.0     24.6      0.0                                           if c['name'] == bucket_id), None))
   548                                                   else:
   549         1         11.0     11.0      0.0              log.debug("Bucket %s was not found.", bucket_id)
   550         1          1.0      1.0      0.0              return None

Total time: 2.01567 s
Function: delete at line 594

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   594                                               @dispatch(event="provider.storage.buckets.delete",
   595                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   596                                               @profile
   597                                               def delete(self, bucket):
   598         6         17.0      2.8      0.0          b_id = bucket.id if isinstance(bucket, OpenStackBucket) else bucket
   599         6    2015651.0 335941.8    100.0          self.provider.swift.delete_container(b_id)

Total time: 1.16921 s
Function: list at line 569

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   569                                               @dispatch(event="provider.storage.buckets.list",
   570                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   571                                               @profile
   572                                               def list(self, limit=None, marker=None):
   573         4         22.0      5.5      0.0          _, container_list = self.provider.swift.get_account(
   574         4        176.0     44.0      0.0              limit=oshelpers.os_result_limit(self.provider, limit),
   575         4    1168776.0 292194.0    100.0              marker=marker)
   576         4         13.0      3.2      0.0          cb_buckets = [OpenStackBucket(self.provider, c)
   577         4         73.0     18.2      0.0                        for c in container_list]
   578         4        147.0     36.8      0.0          return oshelpers.to_server_paged_list(self.provider, cb_buckets, limit)

Total time: 1.02383 s
Function: find at line 644

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   644                                               @profile
   645                                               def find(self, bucket, **kwargs):
   646         3    1021641.0 340547.0     99.8          _, obj_list = self.provider.swift.get_container(bucket.name)
   647         3          9.0      3.0      0.0          cb_objs = [OpenStackBucketObject(self.provider, bucket, obj)
   648         3         54.0     18.0      0.0                     for obj in obj_list]
   649         3          3.0      1.0      0.0          filters = ['name']
   650         3       2051.0    683.7      0.2          matches = cb_helpers.generic_find(filters, kwargs, cb_objs)
   651         2         72.0     36.0      0.0          return ClientPagedResultList(self.provider, list(matches))

Total time: 0.492138 s
Function: find at line 552

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   552                                               @dispatch(event="provider.storage.buckets.find",
   553                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   554                                               @profile
   555                                               def find(self, **kwargs):
   556         3          6.0      2.0      0.0          name = kwargs.pop('name', None)
   557                                           
   558                                                   # All kwargs should have been popped at this time.
   559         3          6.0      2.0      0.0          if len(kwargs) > 0:
   560         1          1.0      1.0      0.0              raise InvalidParamException(
   561         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   562         1         15.0     15.0      0.0                  "attributes: %s" % (kwargs, 'name'))
   563         2     492008.0 246004.0    100.0          _, container_list = self.provider.swift.get_account()
   564         2          6.0      3.0      0.0          cb_buckets = [OpenStackBucket(self.provider, c)
   565         2         27.0     13.5      0.0                        for c in container_list
   566                                                                 if name in c.get("name")]
   567         2         68.0     34.0      0.0          return oshelpers.to_server_paged_list(self.provider, cb_buckets)

