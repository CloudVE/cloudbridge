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
            return self.provider.dns.host_zones.create(name)

        def cleanup_dns_zone(dns_zone):
            if dns_zone:
                dns_zone.delete()

        sit.check_crud(self, self.provider.dns.host_zones, DnsZone,
                       "cb-crudzone", create_dns_zone, cleanup_dns_zone,
                       skip_name_check=True)

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
            test_zone = self.provider.dns.host_zones.create(zone_name)
            sit.check_crud(self, test_zone.records, DnsRecord,
                           "cb-dnsrec", create_dns_rec,
                           cleanup_dns_rec, skip_name_check=True)

    @helpers.skipIfNoService(['dns.host_zones'])
    def test_dns_record_properties(self):
        test_zone = None
        zone_name = "cb-recprop-{0}.com.".format(helpers.get_uuid())

        with cb_helpers.cleanup_action(lambda: test_zone.delete()):
            test_zone = self.provider.dns.host_zones.create(zone_name)
            test_rec = None

            with cb_helpers.cleanup_action(lambda: test_rec.delete()):
                zone_name = "subdomain." + zone_name
                test_rec = test_zone.records.create(
                    zone_name, DnsRecordType.CNAME, data='hello.com.', ttl=500)
                self.assertEqual(test_rec.zone_id, test_zone.id)
                self.assertEqual(test_rec.type, DnsRecordType.CNAME)
                self.assertEqual(test_rec.data, 'hello.com.')
                self.assertEqual(test_rec.ttl, 500)
