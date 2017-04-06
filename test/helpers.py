from contextlib import contextmanager
import os
import sys
import unittest
import functools
from six import reraise

from cloudbridge.cloud.factory import CloudProviderFactory
from cloudbridge.cloud.interfaces import InstanceState
from cloudbridge.cloud.interfaces import TestMockHelperMixin


def parse_bool(val):
    if val:
        return str(val).upper() in ['TRUE', 'YES']
    else:
        return False


@contextmanager
def cleanup_action(cleanup_func):
    """n csdmmnd
    Context manager to carry out a given
    cleanup action after carrying out a set
    of tasks, or when an exception occurs.
    If any errors occur during the cleanup
    action, those are ignored, and the original
    traceback is preserved.

    :params func: This function is called if
    an exception occurs or at the end of the
    context block. If any exceptions raised
        by func are ignored.
    Usage:
        with cleanup_action(lambda e: print("Oops!")):
            do_something()
    """
    try:
        yield
    except Exception:
        ex_class, ex_val, ex_traceback = sys.exc_info()
        try:
            cleanup_func()
        except Exception as e:
            print("Error during exception cleanup: {0}".format(e))
        reraise(ex_class, ex_val, ex_traceback)
    try:
        cleanup_func()
    except Exception as e:
        print("Error during cleanup: {0}".format(e))


def skipIfNoService(services):
    """
    A decorator for skipping tests if the provider
    does not implement a given service.
    """
    def wrap(func):
        """
        The actual wrapper
        """
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            provider = getattr(self, 'provider')
            if provider:
                for service in services:
                    if not provider.has_service(service):
                        self.skipTest("Skipping test because '%s' service is"
                                      " not implemented" % (service,))
            func(self, *args, **kwargs)
        return wrapper
    return wrap


TEST_DATA_CONFIG = {
    "AWSCloudProvider": {
        "image": os.environ.get('CB_IMAGE_AWS', 'ami-5ac2cd4d'),
        "instance_type": os.environ.get('CB_INSTANCE_TYPE_AWS', 't2.nano'),
        "placement": os.environ.get('CB_PLACEMENT_AWS', 'us-east-1a'),
    },
    "OpenStackCloudProvider": {
        "image": os.environ.get('CB_IMAGE_OS',
                                '842b949c-ea76-48df-998d-8a41f2626243'),
        "instance_type": os.environ.get('CB_INSTANCE_TYPE_OS', 'm1.tiny'),
        "placement": os.environ.get('CB_PLACEMENT_OS', 'zone-r6'),
    }
}


def get_provider_test_data(provider, key):
    if "AWSCloudProvider" in provider.name:
        return TEST_DATA_CONFIG.get("AWSCloudProvider").get(key)
    elif "OpenStackCloudProvider" in provider.name:
        return TEST_DATA_CONFIG.get("OpenStackCloudProvider").get(key)
    return None


def create_test_network(provider, name):
    """
    Create a network with one subnet, returning the network and subnet objects.
    """
    net = provider.network.create(name=name)
    cidr_block = (net.cidr_block).split('/')[0] or '10.0.0.1'
    sn = net.create_subnet(cidr_block='{0}/28'.format(cidr_block), name=name,
                           zone=get_provider_test_data(provider, 'placement'))
    return net, sn


def delete_test_network(network):
    """
    Delete the supplied network, first deleting any contained subnets.
    """
    with cleanup_action(lambda: network.delete()):
        for sn in network.subnets():
            sn.delete()


def create_test_instance(
        provider, instance_name, subnet, zone=None, launch_config=None,
        key_pair=None, security_groups=None):
    return provider.compute.instances.create(
        instance_name,
        get_provider_test_data(provider, 'image'),
        get_provider_test_data(provider, 'instance_type'),
        subnet=subnet,
        zone=zone,
        key_pair=key_pair,
        security_groups=security_groups,
        launch_config=launch_config)


def get_test_instance(provider, name, key_pair=None, security_groups=None,
                      subnet=None):
    launch_config = None
    instance = create_test_instance(
        provider,
        name,
        subnet=subnet,
        key_pair=key_pair,
        security_groups=security_groups,
        launch_config=launch_config)
    instance.wait_till_ready()
    return instance


def cleanup_test_resources(instance=None, network=None, security_group=None,
                           key_pair=None):
    with cleanup_action(lambda: delete_test_network(network)
                        if network else None):
        with cleanup_action(lambda: key_pair.delete() if key_pair else None):
            with cleanup_action(lambda: security_group.delete()
                                if security_group else None):
                instance.terminate()
                instance.wait_for(
                    [InstanceState.TERMINATED, InstanceState.UNKNOWN],
                    terminal_states=[InstanceState.ERROR])


class ProviderTestBase(object):

    """
    A dummy base class for Test Cases. Does not inherit from unittest.TestCase
    to avoid confusing test discovery by unittest and nose2. unittest.TestCase
    is injected as a base class by the generator, so calling the unittest
    constructor works correctly.
    """

    def __init__(self, methodName, provider):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.provider = provider

    def setUp(self):
        if isinstance(self.provider, TestMockHelperMixin):
            self.provider.setUpMock()

    def tearDown(self):
        if isinstance(self.provider, TestMockHelperMixin):
            self.provider.tearDownMock()


class ProviderTestCaseGenerator():

    """
    Generates test cases for all provider - testcase combinations.
    Detailed docs at test/__init__.py
    """

    def __init__(self, test_classes):
        self.all_test_classes = test_classes

    def get_provider_wait_interval(self, provider_class):
        if issubclass(provider_class, TestMockHelperMixin):
            return 0
        else:
            return 1

    def create_provider_instance(self, provider_class):
        """
        Instantiate a default provider instance. All required connection
        settings are expected to be set as environment variables.
        """
        config = {'default_wait_interval':
                  self.get_provider_wait_interval(provider_class)}
        return provider_class(config)

    def generate_new_test_class(self, name, testcase_class):
        """
        Generates a new type which inherits from the given testcase_class and
        unittest.TestCase
        """
        class_name = "{0}{1}".format(name, testcase_class.__name__)
        return type(class_name, (testcase_class, unittest.TestCase), {})

    def generate_test_suite_for_provider_testcase(
            self, provider_class, testcase_class):
        """
        Generate and return a suite of tests for a specific provider class and
        testcase combination
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_class)
        suite = unittest.TestSuite()
        for name in testnames:
            generated_cls = self.generate_new_test_class(
                provider_class.__name__,
                testcase_class)
            suite.addTest(
                generated_cls(
                    name,
                    self.create_provider_instance(provider_class)))
        return suite

    def generate_test_suite_for_provider(self, provider_class):
        """
        Generate and return a suite of all available tests for a given provider
        class
        """
        suite = unittest.TestSuite()
        suites = [
            self.generate_test_suite_for_provider_testcase(
                provider_class, test_class)
            for test_class in self.all_test_classes]
        for s in suites:
            suite.addTest(s)
        return suite

    def generate_tests(self):
        """
        Generate and return a suite of tests for all provider and test class
        combinations
        """
        factory = CloudProviderFactory()
        use_mock_drivers = parse_bool(
            os.environ.get("CB_USE_MOCK_PROVIDERS", True))
        provider_name = os.environ.get("CB_TEST_PROVIDER", "azure")
        if provider_name:
            provider_classes = [
                factory.get_provider_class(
                    provider_name,
                    get_mock=use_mock_drivers)]
            if not provider_classes[0]:
                raise ValueError(
                    "Could not find specified test provider %s" %
                    provider_name)
        else:
            provider_classes = factory.get_all_provider_classes(
                get_mock=use_mock_drivers)
        suite = unittest.TestSuite()
        suites = [
            self.generate_test_suite_for_provider(p) for p in provider_classes]
        for s in suites:
            suite.addTest(s)
        return suite
