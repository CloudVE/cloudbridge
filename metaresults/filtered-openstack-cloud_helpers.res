cloudbridge.test.test_cloud_helpers.CloudHelpersTestCase


Test output
 ..F
======================================================================
FAIL: test_type_validation (cloudbridge.test.test_cloud_helpers.CloudHelpersTestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_cloud_helpers.py", line 92, in test_type_validation
    self.assertIsInstance(env_value, six.string_types)
AssertionError: None is not an instance of (<class 'str'>,)

----------------------------------------------------------------------
Ran 3 tests in 1.402s

FAILED (failures=1)

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

