import itertools

from test.helpers import ProviderTestBase

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.resources import ServerPagedResultList


class DummyResult(object):

    def __init__(self, objid, name):
        self.id = objid
        self.name = name

    def __repr__(self):
        return "%s (%s)" % (self.id, self.name)


class CloudHelpersTestCase(ProviderTestBase):

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
