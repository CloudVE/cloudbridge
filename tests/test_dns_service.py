from cloudbridge.base import helpers as cb_helpers
from cloudbridge.interfaces.resources import DnsRecord
from cloudbridge.interfaces.resources import DnsRecordType
from cloudbridge.interfaces.resources import DnsZone

from tests import helpers
from tests.helpers import ProviderTestBase
from tests.helpers import standard_interface_tests as sit


class CloudDnsServiceTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    @helpers.skipIfNoService(['dns.host_zones'])
    def test_crud_dns_zones(self):

        def create_dns_zone(name):
            if name:
                name = name + ".com."
            return self.provider.dns.host_zones.create(
                name, "admin@cloudve.org")

        def cleanup_dns_zone(dns_zone):
            if dns_zone:
                dns_zone.delete()

        def test_zone_props(dns_zone):
            self.assertEqual(dns_zone.admin_email, "admin@cloudve.org")

        sit.check_crud(self, self.provider.dns.host_zones, DnsZone,
                       "cb-crudzone", create_dns_zone, cleanup_dns_zone,
                       skip_name_check=True, extra_test_func=test_zone_props)

    @helpers.skipIfNoService(['dns.host_zones'])
    def test_create_dns_zones_not_fully_qualified(self):
        zone_name = "cb-dnszonenfq-{0}.com".format(helpers.get_uuid())
        test_zone = None
        with cb_helpers.cleanup_action(lambda: test_zone.delete()):
            # If zone name is not fully qualified, it should automatically be
            # handled
            test_zone = self.provider.dns.host_zones.create(
                zone_name, "admin@cloudve.org")

    @helpers.skipIfNoService(['dns.host_zones'])
    def test_crud_dns_record(self):
        test_zone = None
        zone_name = "cb-dnsrec-{0}.com.".format(helpers.get_uuid())

        def create_dns_rec(name):
            if name:
                name = name + "." + zone_name
            else:
                name = zone_name
            return test_zone.records.create(
                name, DnsRecordType.A, data='10.1.1.1')

        def cleanup_dns_rec(dns_rec):
            if dns_rec:
                dns_rec.delete()

        with cb_helpers.cleanup_action(lambda: test_zone.delete()):
            test_zone = self.provider.dns.host_zones.create(
                zone_name, "admin@cloudve.org")
            sit.check_crud(self, test_zone.records, DnsRecord,
                           "cb-dnsrec", create_dns_rec,
                           cleanup_dns_rec, skip_name_check=True)

    @helpers.skipIfNoService(['dns.host_zones'])
    def test_create_wildcard_dns_record(self):
        test_zone = None
        zone_name = "cb-dnswild-{0}.com.".format(helpers.get_uuid())

        with cb_helpers.cleanup_action(lambda: test_zone.delete()):
            test_zone = self.provider.dns.host_zones.create(
                zone_name, "admin@cloudve.org")
            test_rec = None
            with cb_helpers.cleanup_action(lambda: test_rec.delete()):
                test_rec = test_zone.records.create(
                    "*.cb-wildcard." + zone_name, DnsRecordType.A,
                    data='10.1.1.1')

    @helpers.skipIfNoService(['dns.host_zones'])
    def test_dns_record_properties(self):
        test_zone = None
        zone_name = "cb-recprop-{0}.com.".format(helpers.get_uuid())

        with cb_helpers.cleanup_action(lambda: test_zone.delete()):
            test_zone = self.provider.dns.host_zones.create(
                zone_name, "admin@cloudve.org")
            test_rec = None

            with cb_helpers.cleanup_action(lambda: test_rec.delete()):
                zone_name = "subdomain." + zone_name
                test_rec = test_zone.records.create(
                    zone_name, DnsRecordType.CNAME, data='hello.com.', ttl=500)
                self.assertEqual(test_rec.zone_id, test_zone.id)
                self.assertEqual(test_rec.type, DnsRecordType.CNAME)
                self.assertEqual(test_rec.data, ['hello.com.'])
                self.assertEqual(test_rec.ttl, 500)

            # Check setting data array
            test_rec2 = None
            with cb_helpers.cleanup_action(lambda: test_rec2.delete()):
                MX_DATA = ['10 mx1.hello.com.', '20 mx2.hello.com.']
                test_rec2 = test_zone.records.create(
                    zone_name, DnsRecordType.MX, data=MX_DATA, ttl=300)
                self.assertEqual(test_rec2.zone_id, test_zone.id)
                self.assertEqual(test_rec2.type, DnsRecordType.MX)
                self.assertSetEqual(set(test_rec2.data), set(MX_DATA))
                self.assertEqual(test_rec2.ttl, 300)

    @helpers.skipIfNoService(['dns.host_zones'])
    def test_create_dns_rec_not_fully_qualified(self):
        test_zone = None
        root_zone_name = "cb-recprop-{0}.com.".format(helpers.get_uuid())

        with cb_helpers.cleanup_action(lambda: test_zone.delete()):
            test_zone = self.provider.dns.host_zones.create(
                root_zone_name, "admin@cloudve.org")
            test_rec = None

            with cb_helpers.cleanup_action(lambda: test_rec.delete()):
                zone_name = "subdomain." + root_zone_name
                test_rec = test_zone.records.create(
                    zone_name, DnsRecordType.CNAME, data='hello.com', ttl=500)

            with cb_helpers.cleanup_action(lambda: test_rec.delete()):
                test_rec = test_zone.records.create(
                    root_zone_name, DnsRecordType.MX,
                    data=['10 mx1.hello.com', '20 mx2.hello.com'], ttl=500)
