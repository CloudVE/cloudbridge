cloudbridge.test.test_object_store_service.CloudObjectStoreServiceTestCase


Test output
 .......s
----------------------------------------------------------------------
Ran 8 tests in 60.193s

OK (skipped=1)

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 23.1735 s
Function: create at line 508

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   508                                               @dispatch(event="provider.storage.buckets.create",
   509                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   510                                               @profile
   511                                               def create(self, name, location=None):
   512        17        218.0     12.8      0.0          AWSBucket.assert_valid_resource_name(name)
   513         7         41.0      5.9      0.0          location = location or self.provider.region_name
   514                                                   # Due to an API issue in S3, specifying us-east-1 as a
   515                                                   # LocationConstraint results in an InvalidLocationConstraint.
   516                                                   # Therefore, it must be special-cased and omitted altogether.
   517                                                   # See: https://github.com/boto/boto3/issues/125
   518                                                   # In addition, us-east-1 also behaves differently when it comes
   519                                                   # to raising duplicate resource exceptions, so perform a manual
   520                                                   # check
   521         7          6.0      0.9      0.0          if location == 'us-east-1':
   522         7          4.0      0.6      0.0              try:
   523                                                           # check whether bucket already exists
   524         7   19622481.0 2803211.6     84.7                  self.provider.s3_conn.meta.client.head_bucket(Bucket=name)
   525         6         20.0      3.3      0.0              except ClientError as e:
   526         6          9.0      1.5      0.0                  if e.response['Error']['Code'] == "404":
   527                                                               # bucket doesn't exist, go ahead and create it
   528         6    3550680.0 591780.0     15.3                      return self.svc.create('create_bucket', Bucket=name)
   529         1          3.0      3.0      0.0              raise DuplicateResourceException(
   530         1          5.0      5.0      0.0                      'Bucket already exists with name {0}'.format(name))
   531                                                   else:
   532                                                       try:
   533                                                           return self.svc.create('create_bucket', Bucket=name,
   534                                                                                  CreateBucketConfiguration={
   535                                                                                      'LocationConstraint': location
   536                                                                                   })
   537                                                       except ClientError as e:
   538                                                           if e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
   539                                                               raise DuplicateResourceException(
   540                                                                   'Bucket already exists with name {0}'.format(name))
   541                                                           else:
   542                                                               raise

Total time: 1.97919 s
Function: delete at line 544

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   544                                               @dispatch(event="provider.storage.buckets.delete",
   545                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   546                                               @profile
   547                                               def delete(self, bucket):
   548         6     213103.0  35517.2     10.8          b = bucket if isinstance(bucket, AWSBucket) else self.get(bucket)
   549         6          9.0      1.5      0.0          if b:
   550                                                       # pylint:disable=protected-access
   551         6    1766083.0 294347.2     89.2              b._bucket.delete()

Total time: 0.801255 s
Function: list at line 502

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   502                                               @dispatch(event="provider.storage.buckets.list",
   503                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   504                                               @profile
   505                                               def list(self, limit=None, marker=None):
   506        12     801255.0  66771.2    100.0          return self.svc.list(limit=limit, marker=marker)

Total time: 0.408806 s
Function: list at line 570

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   570                                               @profile
   571                                               def list(self, bucket, limit=None, marker=None, prefix=None):
   572         9         15.0      1.7      0.0          if prefix:
   573                                                       # pylint:disable=protected-access
   574         1         79.0     79.0      0.0              boto_objs = bucket._bucket.objects.filter(Prefix=prefix)
   575                                                   else:
   576                                                       # pylint:disable=protected-access
   577         8        371.0     46.4      0.1              boto_objs = bucket._bucket.objects.all()
   578         9     407969.0  45329.9     99.8          objects = [AWSBucketObject(self.provider, obj) for obj in boto_objs]
   579         9         35.0      3.9      0.0          return ClientPagedResultList(self.provider, objects,
   580         9        337.0     37.4      0.1                                       limit=limit, marker=marker)

Total time: 0.323 s
Function: get at line 471

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   471                                               @dispatch(event="provider.storage.buckets.get",
   472                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   473                                               @profile
   474                                               def get(self, bucket_id):
   475                                                   """
   476                                                   Returns a bucket given its ID. Returns ``None`` if the bucket
   477                                                   does not exist.
   478                                                   """
   479         8         14.0      1.8      0.0          try:
   480                                                       # Make a call to make sure the bucket exists. There's an edge case
   481                                                       # where a 403 response can occur when the bucket exists but the
   482                                                       # user simply does not have permissions to access it. See below.
   483         8     305130.0  38141.2     94.5              self.provider.s3_conn.meta.client.head_bucket(Bucket=bucket_id)
   484         7         44.0      6.3      0.0              return AWSBucket(self.provider,
   485         7      17786.0   2540.9      5.5                               self.provider.s3_conn.Bucket(bucket_id))
   486         1          3.0      3.0      0.0          except ClientError as e:
   487                                                       # If 403, it means the bucket exists, but the user does not have
   488                                                       # permissions to access the bucket. However, limited operations
   489                                                       # may be permitted (with a session token for example), so return a
   490                                                       # Bucket instance to allow further operations.
   491                                                       # http://stackoverflow.com/questions/32331456/using-boto-upload-file-to-s3-
   492                                                       # sub-folder-when-i-have-no-permissions-on-listing-fo
   493         1         23.0     23.0      0.0              if e.response['Error']['Code'] == "403":
   494                                                           log.warning("AWS Bucket %s already exists but user doesn't "
   495                                                                       "have enough permissions to access the bucket",
   496                                                                       bucket_id)
   497                                                           return AWSBucket(self.provider,
   498                                                                            self.provider.s3_conn.Bucket(bucket_id))
   499                                                   # For all other responses, it's assumed that the bucket does not exist.
   500         1          0.0      0.0      0.0          return None

Total time: 0.154444 s
Function: find at line 582

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   582                                               @profile
   583                                               def find(self, bucket, **kwargs):
   584                                                   # pylint:disable=protected-access
   585         3          4.0      1.3      0.0          obj_list = [AWSBucketObject(self.provider, o)
   586         3     153314.0  51104.7     99.3                      for o in bucket._bucket.objects.all()]
   587         3          7.0      2.3      0.0          filters = ['name']
   588         3       1040.0    346.7      0.7          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   589         2          8.0      4.0      0.0          return ClientPagedResultList(self.provider, list(matches),
   590         2         71.0     35.5      0.0                                       limit=None, marker=None)

Total time: 0.138302 s
Function: find at line 163

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   163                                               @dispatch(event="provider.storage.buckets.find",
   164                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   165                                               @profile
   166                                               def find(self, **kwargs):
   167         3          3.0      1.0      0.0          obj_list = self
   168         3          3.0      1.0      0.0          filters = ['name']
   169         3     138220.0  46073.3     99.9          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   170                                           
   171                                                   # All kwargs should have been popped at this time.
   172         2          5.0      2.5      0.0          if len(kwargs) > 0:
   173                                                       raise InvalidParamException(
   174                                                           "Unrecognised parameters for search: %s. Supported "
   175                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   176                                           
   177         2          9.0      4.5      0.0          return ClientPagedResultList(self.provider,
   178         2         62.0     31.0      0.0                                       matches if matches else [])

Total time: 0.125817 s
Function: get at line 559

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   559                                               @profile
   560                                               def get(self, bucket, object_id):
   561         4          3.0      0.8      0.0          try:
   562                                                       # pylint:disable=protected-access
   563         4       9762.0   2440.5      7.8              obj = bucket._bucket.Object(object_id)
   564                                                       # load() throws an error if object does not exist
   565         4     115995.0  28998.8     92.2              obj.load()
   566         3         40.0     13.3      0.0              return AWSBucketObject(self.provider, obj)
   567         1          3.0      3.0      0.0          except ClientError:
   568         1         14.0     14.0      0.0              return None

Total time: 0.015893 s
Function: create at line 592

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   592                                               @profile
   593                                               def create(self, bucket, name):
   594                                                   # pylint:disable=protected-access
   595         5      15831.0   3166.2     99.6          obj = bucket._bucket.Object(name)
   596         5         62.0     12.4      0.4          return AWSBucketObject(self.provider, obj)

