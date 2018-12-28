import itertools

import six

from cloudbridge.cloud.base.helpers import get_env
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.resources import ServerPagedResultList

from test.helpers import ProviderTestBase


class DummyResult(object):

    def __init__(self, objid, name):
        self.id = objid
        self.name = name

    def __repr__(self):
        return "%s (%s)" % (self.id, self.name)


class CloudHelpersTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    def setUp(self):
        super(CloudHelpersTestCase, self).setUp()
        self.objects = [DummyResult(1, "One"),
                        DummyResult(2, "Two"),
                        DummyResult(3, "Three"),
                        DummyResult(4, "Four"),
                        ]

    def test_client_paged_result_list(self):
        objects = self.objects

        # A list with limit=2 and marker=None
        results = ClientPagedResultList(self.provider, objects, 2, None)
        self.assertListEqual(results, list(itertools.islice(objects, 2)))
        self.assertEqual(results.marker, objects[1].id)
        self.assertTrue(results.is_truncated)
        self.assertTrue(results.supports_total)
        self.assertEqual(results.total_results, 4)
        self.assertEqual(results.data, objects)

        # A list with limit=2 and marker=2
        results = ClientPagedResultList(self.provider, objects, 2, 2)
        self.assertListEqual(results, list(itertools.islice(objects, 2, 4)))
        self.assertEqual(results.marker, None)
        self.assertFalse(results.is_truncated)
        self.assertTrue(results.supports_total)
        self.assertEqual(results.total_results, 4)
        self.assertEqual(results.data, objects)

        # A list with limit=2 and marker=3
        results = ClientPagedResultList(self.provider, objects, 2, 3)
        self.assertListEqual(results, list(itertools.islice(objects, 3, 4)))
        self.assertFalse(results.is_truncated)
        self.assertEqual(results.marker, None)
        self.assertEqual(results.data, objects)

        self.assertFalse(results.supports_server_paging, "Client paged result"
                         " lists should return False for server paging.")

    def test_server_paged_result_list(self):

        objects = list(itertools.islice(self.objects, 2))
        results = ServerPagedResultList(is_truncated=True,
                                        marker=objects[-1].id,
                                        supports_total=True,
                                        total=2, data=objects)
        self.assertTrue(results.is_truncated)
        self.assertListEqual(results, objects)
        self.assertEqual(results.marker, objects[-1].id)
        self.assertTrue(results.supports_total)
        self.assertEqual(results.total_results, 2)
        self.assertTrue(results.supports_server_paging, "Server paged result"
                        " lists should return True for server paging.")
        with self.assertRaises(NotImplementedError):
            results.data

    def test_type_validation(self):
        """
        Make sure internal type checking implementation properly sets types.
        """
        self.provider.config['text_type_check'] = 'test-text'
        config_value = self.provider._get_config_value('text_type_check', None)
        self.assertIsInstance(config_value, six.string_types)

        env_value = self.provider._get_config_value(
            'some_config_value', get_env('MOTO_AMIS_PATH'))
        self.assertIsInstance(env_value, six.string_types)

        none_value = self.provider._get_config_value(
            'some_config_value', get_env('MISSING_ENV', None))
        self.assertIsNone(none_value)

        bool_value = self.provider._get_config_value(
            'some_config_value', get_env('MISSING_ENV', True))
        self.assertIsInstance(bool_value, bool)

        int_value = self.provider._get_config_value(
            'default_result_limit', None)
        self.assertIsInstance(int_value, int)
