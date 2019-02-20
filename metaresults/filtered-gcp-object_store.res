cloudbridge.test.test_object_store_service.CloudObjectStoreServiceTestCase


Test output
 .......s
----------------------------------------------------------------------
Ran 8 tests in 53.740s

OK (skipped=1)

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 20.0851 s
Function: create at line 1483

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1483                                               @dispatch(event="provider.storage.buckets.create",
  1484                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
  1485                                               @profile
  1486                                               def create(self, name, location=None):
  1487        17        171.0     10.1      0.0          GCPBucket.assert_valid_resource_name(name)
  1488         7         10.0      1.4      0.0          body = {'name': name}
  1489         7          5.0      0.7      0.0          if location:
  1490                                                       body['location'] = location
  1491         7          4.0      0.6      0.0          try:
  1492         7     752095.0 107442.1      3.7              response = (self.provider
  1493                                                                       .gcp_storage
  1494                                                                       .buckets()
  1495         7         28.0      4.0      0.0                              .insert(project=self.provider.project_name,
  1496         7    7309697.0 1044242.4     36.4                                      body=body)
  1497                                                                       .execute())
  1498                                                       # GCP has a rate limit of 1 operation per 2 seconds for bucket
  1499                                                       # creation/deletion: https://cloud.google.com/storage/quotas.
  1500                                                       # Throttle here to avoid future failures.
  1501         6   12022742.0 2003790.3     59.9              time.sleep(2)
  1502         6        340.0     56.7      0.0              return GCPBucket(self.provider, response)
  1503         1          5.0      5.0      0.0          except googleapiclient.errors.HttpError as http_error:
  1504                                                       # 409 = conflict
  1505         1          2.0      2.0      0.0              if http_error.resp.status in [409]:
  1506         1          1.0      1.0      0.0                  raise DuplicateResourceException(
  1507         1          7.0      7.0      0.0                      'Bucket already exists with name {0}'.format(name))
  1508                                                       else:
  1509                                                           raise

Total time: 17.3862 s
Function: delete at line 1511

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1511                                               @dispatch(event="provider.storage.buckets.delete",
  1512                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
  1513                                               @profile
  1514                                               def delete(self, bucket):
  1515                                                   """
  1516                                                   Delete this bucket.
  1517                                                   """
  1518         6    1763632.0 293938.7     10.1          b = bucket if isinstance(bucket, GCPBucket) else self.get(bucket)
  1519         6          6.0      1.0      0.0          if b:
  1520         6      56022.0   9337.0      0.3              (self.provider
  1521                                                            .gcp_storage
  1522                                                            .buckets()
  1523         6    3537017.0 589502.8     20.3                   .delete(bucket=b.name)
  1524                                                            .execute())
  1525                                                       # GCP has a rate limit of 1 operation per 2 seconds for bucket
  1526                                                       # creation/deletion: https://cloud.google.com/storage/quotas.
  1527                                                       # Throttle here to avoid future failures.
  1528         6   12029521.0 2004920.2     69.2              time.sleep(2)

Total time: 3.30274 s
Function: list at line 1545

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1545                                               @profile
  1546                                               def list(self, bucket, limit=None, marker=None, prefix=None):
  1547                                                   """
  1548                                                   List all objects within this bucket.
  1549                                                   """
  1550        11         23.0      2.1      0.0          max_result = limit if limit is not None and limit < 500 else 500
  1551        11     199638.0  18148.9      6.0          response = (self.provider
  1552                                                                   .gcp_storage
  1553                                                                   .objects()
  1554        11         37.0      3.4      0.0                          .list(bucket=bucket.name,
  1555        11         10.0      0.9      0.0                                prefix=prefix if prefix else '',
  1556        11          6.0      0.5      0.0                                maxResults=max_result,
  1557        11    3102655.0 282059.5     93.9                                pageToken=marker)
  1558                                                                   .execute())
  1559        11         27.0      2.5      0.0          objects = []
  1560        19         34.0      1.8      0.0          for obj in response.get('items', []):
  1561         8        146.0     18.2      0.0              objects.append(GCPBucketObject(self.provider, bucket, obj))
  1562        11         18.0      1.6      0.0          if len(objects) > max_result:
  1563                                                       log.warning('Expected at most %d results; got %d',
  1564                                                                   max_result, len(objects))
  1565        11         13.0      1.2      0.0          return ServerPagedResultList('nextPageToken' in response,
  1566        11         17.0      1.5      0.0                                       response.get('nextPageToken'),
  1567        11        120.0     10.9      0.0                                       False, data=objects)

Total time: 2.65239 s
Function: create at line 1586

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1586                                               @profile
  1587                                               def create(self, bucket, name):
  1588         5         13.0      2.6      0.0          response = self._create_object_with_media_body(
  1589         5          7.0      1.4      0.0                              bucket,
  1590         5          5.0      1.0      0.0                              name,
  1591         5         20.0      4.0      0.0                              googleapiclient.http.MediaIoBaseUpload(
  1592         5    2652248.0 530449.6    100.0                                  io.BytesIO(b''), mimetype='plain/text'))
  1593                                                   return GCPBucketObject(self._provider,
  1594                                                                          bucket,
  1595         5         95.0     19.0      0.0                                 response) if response else None

Total time: 2.37478 s
Function: get at line 1430

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1430                                               @dispatch(event="provider.storage.buckets.get",
  1431                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
  1432                                               @profile
  1433                                               def get(self, bucket_id):
  1434                                                   """
  1435                                                   Returns a bucket given its ID. Returns ``None`` if the bucket
  1436                                                   does not exist or if the user does not have permission to access the
  1437                                                   bucket.
  1438                                                   """
  1439         8    2374578.0 296822.2    100.0          bucket = self.provider.get_resource('buckets', bucket_id)
  1440         8        197.0     24.6      0.0          return GCPBucket(self.provider, bucket) if bucket else None

Total time: 2.05451 s
Function: get at line 1536

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1536                                               @profile
  1537                                               def get(self, bucket, name):
  1538                                                   """
  1539                                                   Retrieve a given object from this bucket.
  1540                                                   """
  1541         4          8.0      2.0      0.0          obj = self.provider.get_resource('objects', name,
  1542         4    2054458.0 513614.5    100.0                                           bucket=bucket.name)
  1543         4         49.0     12.2      0.0          return GCPBucketObject(self.provider, bucket, obj) if obj else None

Total time: 0.978596 s
Function: list at line 1458

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1458                                               @dispatch(event="provider.storage.buckets.list",
  1459                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
  1460                                               @profile
  1461                                               def list(self, limit=None, marker=None):
  1462                                                   """
  1463                                                   List all containers.
  1464                                                   """
  1465         6         15.0      2.5      0.0          max_result = limit if limit is not None and limit < 500 else 500
  1466         6      50428.0   8404.7      5.2          response = (self.provider
  1467                                                                   .gcp_storage
  1468                                                                   .buckets()
  1469         6         18.0      3.0      0.0                          .list(project=self.provider.project_name,
  1470         6          5.0      0.8      0.0                                maxResults=max_result,
  1471         6     926411.0 154401.8     94.7                                pageToken=marker)
  1472                                                                   .execute())
  1473         6         18.0      3.0      0.0          buckets = []
  1474       113        123.0      1.1      0.0          for bucket in response.get('items', []):
  1475       107       1472.0     13.8      0.2              buckets.append(GCPBucket(self.provider, bucket))
  1476         6         12.0      2.0      0.0          if len(buckets) > max_result:
  1477                                                       log.warning('Expected at most %d results; got %d',
  1478                                                                   max_result, len(buckets))
  1479         6         11.0      1.8      0.0          return ServerPagedResultList('nextPageToken' in response,
  1480         6          8.0      1.3      0.0                                       response.get('nextPageToken'),
  1481         6         75.0     12.5      0.0                                       False, data=buckets)

Total time: 0.399978 s
Function: find at line 1569

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1569                                               @profile
  1570                                               def find(self, bucket, limit=None, marker=None, **kwargs):
  1571         3          5.0      1.7      0.0          filters = ['name']
  1572         3     399875.0 133291.7    100.0          matches = cb_helpers.generic_find(filters, kwargs, bucket.objects)
  1573         2          5.0      2.5      0.0          return ClientPagedResultList(self._provider, list(matches),
  1574         2         93.0     46.5      0.0                                       limit=limit, marker=marker)

Total time: 0.342205 s
Function: find at line 1442

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1442                                               @dispatch(event="provider.storage.buckets.find",
  1443                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
  1444                                               @profile
  1445                                               def find(self, limit=None, marker=None, **kwargs):
  1446         3          7.0      2.3      0.0          name = kwargs.pop('name', None)
  1447                                           
  1448                                                   # All kwargs should have been popped at this time.
  1449         3          5.0      1.7      0.0          if len(kwargs) > 0:
  1450         1          1.0      1.0      0.0              raise InvalidParamException(
  1451         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
  1452         1         17.0     17.0      0.0                  "attributes: %s" % (kwargs, 'name'))
  1453                                           
  1454         2     342071.0 171035.5    100.0          buckets = [bucket for bucket in self if name in bucket.name]
  1455         2          6.0      3.0      0.0          return ClientPagedResultList(self.provider, buckets, limit=limit,
  1456         2         97.0     48.5      0.0                                       marker=marker)

