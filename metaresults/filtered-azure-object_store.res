cloudbridge.test.test_object_store_service.CloudObjectStoreServiceTestCase


Test output
 .......s
----------------------------------------------------------------------
Ran 8 tests in 14.293s

OK (skipped=1)

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 8.72687 s
Function: create at line 578

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   578                                               @dispatch(event="provider.storage.buckets.create",
   579                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   580                                               @profile
   581                                               def create(self, name, location=None):
   582                                                   """
   583                                                   Create a new bucket.
   584                                                   """
   585        17        219.0     12.9      0.0          AzureBucket.assert_valid_resource_name(name)
   586         7    8726447.0 1246635.3    100.0          bucket = self.provider.azure_client.create_container(name)
   587         6        208.0     34.7      0.0          return AzureBucket(self.provider, bucket)

Total time: 0.680332 s
Function: create at line 641

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   641                                               @profile
   642                                               def create(self, bucket, name):
   643         5         35.0      7.0      0.0          self.provider.azure_client.create_blob_from_text(
   644         5     350171.0  70034.2     51.5              bucket.name, name, '')
   645         5     330126.0  66025.2     48.5          return self.get(bucket, name)

Total time: 0.585543 s
Function: get at line 604

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   604                                               @profile
   605                                               def get(self, bucket, object_id):
   606                                                   """
   607                                                   Retrieve a given object from this bucket.
   608                                                   """
   609         9          9.0      1.0      0.0          try:
   610         9         91.0     10.1      0.0              obj = self.provider.azure_client.get_blob(bucket.name,
   611         9     585148.0  65016.4     99.9                                                        object_id)
   612         8        153.0     19.1      0.0              return AzureBucketObject(self.provider, bucket, obj)
   613         1          3.0      3.0      0.0          except AzureException as azureEx:
   614         1        137.0    137.0      0.0              log.exception(azureEx)
   615         1          2.0      2.0      0.0              return None

Total time: 0.574927 s
Function: list at line 617

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   617                                               @profile
   618                                               def list(self, bucket, limit=None, marker=None, prefix=None):
   619                                                   """
   620                                                   List all objects within this bucket.
   621                                           
   622                                                   :rtype: BucketObject
   623                                                   :return: List of all available BucketObjects within this bucket.
   624                                                   """
   625         9         25.0      2.8      0.0          objects = [AzureBucketObject(self.provider, bucket, obj)
   626                                                              for obj in
   627         9         70.0      7.8      0.0                     self.provider.azure_client.list_blobs(
   628         9     574455.0  63828.3     99.9                         bucket.name, prefix=prefix)]
   629         9         38.0      4.2      0.0          return ClientPagedResultList(self.provider, objects,
   630         9        339.0     37.7      0.1                                       limit=limit, marker=marker)

Total time: 0.418262 s
Function: delete at line 589

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   589                                               @dispatch(event="provider.storage.buckets.delete",
   590                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   591                                               @profile
   592                                               def delete(self, bucket):
   593                                                   """
   594                                                   Delete this bucket.
   595                                                   """
   596         6         16.0      2.7      0.0          b_id = bucket.id if isinstance(bucket, AzureBucket) else bucket
   597         6     418246.0  69707.7    100.0          self.provider.azure_client.delete_container(b_id)

Total time: 0.378635 s
Function: list at line 568

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   568                                               @dispatch(event="provider.storage.buckets.list",
   569                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   570                                               @profile
   571                                               def list(self, limit=None, marker=None):
   572         6         16.0      2.7      0.0          buckets = [AzureBucket(self.provider, bucket)
   573                                                              for bucket
   574         6     378339.0  63056.5     99.9                     in self.provider.azure_client.list_containers()[0]]
   575         6         26.0      4.3      0.0          return ClientPagedResultList(self.provider, buckets,
   576         6        254.0     42.3      0.1                                       limit=limit, marker=marker)

Total time: 0.20334 s
Function: find at line 632

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   632                                               @profile
   633                                               def find(self, bucket, **kwargs):
   634         3          3.0      1.0      0.0          obj_list = [AzureBucketObject(self.provider, bucket, obj)
   635                                                               for obj in
   636         3     202075.0  67358.3     99.4                      self.provider.azure_client.list_blobs(bucket.name)]
   637         3          7.0      2.3      0.0          filters = ['name']
   638         3       1178.0    392.7      0.6          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   639         2         77.0     38.5      0.0          return ClientPagedResultList(self.provider, list(matches))

Total time: 0.139937 s
Function: find at line 163

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   163                                               @dispatch(event="provider.storage.buckets.find",
   164                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   165                                               @profile
   166                                               def find(self, **kwargs):
   167         3          3.0      1.0      0.0          obj_list = self
   168         3          3.0      1.0      0.0          filters = ['name']
   169         3     139871.0  46623.7    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   170                                           
   171                                                   # All kwargs should have been popped at this time.
   172         2          3.0      1.5      0.0          if len(kwargs) > 0:
   173                                                       raise InvalidParamException(
   174                                                           "Unrecognised parameters for search: %s. Supported "
   175                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   176                                           
   177         2          5.0      2.5      0.0          return ClientPagedResultList(self.provider,
   178         2         52.0     26.0      0.0                                       matches if matches else [])

Total time: 0.137179 s
Function: get at line 553

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   553                                               @dispatch(event="provider.storage.buckets.get",
   554                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   555                                               @profile
   556                                               def get(self, bucket_id):
   557                                                   """
   558                                                   Returns a bucket given its ID. Returns ``None`` if the bucket
   559                                                   does not exist.
   560                                                   """
   561         2          3.0      1.5      0.0          try:
   562         2     136958.0  68479.0     99.8              bucket = self.provider.azure_client.get_container(bucket_id)
   563         1         23.0     23.0      0.0              return AzureBucket(self.provider, bucket)
   564         1          4.0      4.0      0.0          except AzureException as error:
   565         1        189.0    189.0      0.1              log.exception(error)
   566         1          2.0      2.0      0.0              return None

