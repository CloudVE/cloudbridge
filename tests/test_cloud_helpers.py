import itertools

from cloudbridge.base.helpers import get_env
from cloudbridge.base.resources import ClientPagedResultList
from cloudbridge.base.resources import ServerPagedResultList

from tests.helpers import ProviderTestBase


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
        # Make sure internal type checking implementation properly sets types.
        self.provider.config['text_type_check'] = 'test-text'
        # pylint:disable=protected-access
        config_value = self.provider._get_config_value('text_type_check', None)
        self.assertIsInstance(config_value, str)

        # pylint:disable=protected-access
        none_value = self.provider._get_config_value(
            'some_config_value', get_env('MISSING_ENV', None))
        self.assertIsNone(none_value)

        # pylint:disable=protected-access
        bool_value = self.provider._get_config_value(
            'some_config_value', get_env('MISSING_ENV', True))
        self.assertIsInstance(bool_value, bool)

        # pylint:disable=protected-access
        int_value = self.provider._get_config_value(
            'default_result_limit', None)
        self.assertIsInstance(int_value, int)

    def test_config_value_set_to_false_is_honored(self):
        # A boolean option turned off must not be mistaken for an unset one:
        # `s3_validate_certs: False` has to reach the SDK as False, not as
        # the default of True.
        self.provider.config['falsy_bool_check'] = False
        # pylint:disable=protected-access
        self.assertIs(
            self.provider._get_config_value('falsy_bool_check', True), False)

    def test_config_value_set_to_zero_is_honored(self):
        self.provider.config['falsy_int_check'] = 0
        # pylint:disable=protected-access
        self.assertEqual(
            self.provider._get_config_value('falsy_int_check', 4), 0)

    def test_config_value_none_or_blank_falls_back_to_default(self):
        # None and the empty string are what an absent value looks like
        # coming from YAML, a blank environment variable or a blank ini
        # option, so those alone mean "not configured".
        for unset in (None, ''):
            self.provider.config['unset_check'] = unset
            # pylint:disable=protected-access
            self.assertEqual(
                self.provider._get_config_value('unset_check', 'default'),
                'default', repr(unset))
