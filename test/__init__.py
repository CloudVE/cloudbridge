"""
Tests the functionality of each provider implementation against registered
test cases. These tests require that provider credentials are set as
environment variables, as required for each provider (see `tox.ini` for a list
of env variables).

Since the tests exercise the ``cloudbridge`` interfaces, and there are multiple
implementations of these interfaces, for m interfaces and n implementation,
exercising all interfaces means that m*n test case classes are needed.
Otherwise, the standard test runners such as unittest and nose2 do not
correctly pick up the tests.

To avoid an explosion of repetitive test cases, the
``ProviderTestCaseGenerator`` class will automatically generate a new Python
class for each combination of test and provider. The ``load_tests`` protocol
(https://docs.python.org/2/library/unittest.html#load-tests-protocol)
is used to aid test discovery.

Use ``python setup.py test`` to run these unit tests (alternatively, use
``python -m unittest test``).

All test cases need to be registered below, and available providers will be
discovered through the ``ProviderFactory``. Test Cases must not inherit from
``unittest.TestCase``, to avoid confusing unittest and nose2's automatic
discovery. (The test generator will automatically add ``unittest.TestCase``
as a base class to each combination).
"""
import cloudbridge
from test.helpers import ProviderTestCaseGenerator
from test.test_instance_types_service import \
    ProviderInstanceTypesServiceTestCase
from test.test_provider_block_store_service import \
    ProviderBlockStoreServiceTestCase
from test.test_provider_compute_service import ProviderComputeServiceTestCase
from test.test_provider_image_service import ProviderImageServiceTestCase
from test.test_provider_interface import ProviderInterfaceTestCase
from test.test_provider_object_store_service import \
    ProviderObjectStoreServiceTestCase
from test.test_provider_security_service import ProviderSecurityServiceTestCase


PROVIDER_TESTS = [
    ProviderInterfaceTestCase,
    ProviderSecurityServiceTestCase,
    ProviderInstanceTypesServiceTestCase,
    ProviderComputeServiceTestCase,
    ProviderImageServiceTestCase,
    ProviderBlockStoreServiceTestCase,
    ProviderObjectStoreServiceTestCase
]


def load_tests(loader=None, tests=None, pattern=None):
    """
    This function is required to aid the load_tests protocol
    (https://docs.python.org/2/library/unittest.html#load-tests-protocol)
    """
    cloudbridge.init_logging()
    return ProviderTestCaseGenerator(PROVIDER_TESTS).generate_tests()
