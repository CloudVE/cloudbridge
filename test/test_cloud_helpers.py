import itertools

from cloudbridge.cloud.base import ClientPagedResultList
from test.helpers import ProviderTestBase


class CloudHelpersTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(CloudHelpersTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_result_list_conversion(self):

        class DummyResult(object):

            def __init__(self, objid, name):
                self.id = objid
                self.name = name

            def __repr__(self):
                return "%s (%s)" % (self.id, self.name)

        objects = [DummyResult(1, "One"),
                   DummyResult(2, "Two"),
                   DummyResult(3, "Three"),
                   DummyResult(4, "Four"),
                   ]

        results = ClientPagedResultList(self.provider, objects, 2, None)
        self.assertListEqual(results, list(itertools.islice(objects, 2)))
        self.assertEqual(results.marker, objects[1].id)
        self.assertTrue(results.supports_total)
        self.assertEqual(results.total_results, 4)

        results = ClientPagedResultList(self.provider, objects, 2, 2)
        self.assertListEqual(results, list(itertools.islice(objects, 2, 4)))
        self.assertEqual(results.marker, None)
        self.assertTrue(results.supports_total)
        self.assertEqual(results.total_results, 4)

        results = ClientPagedResultList(self.provider, objects, 2, 3)
        self.assertListEqual(results, list(itertools.islice(objects, 3, 4)))
        self.assertEqual(results.marker, None)
