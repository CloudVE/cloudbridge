"""
Provider-agnostic unit tests for ``BaseNetworkService.get_or_create_default``.

AWS and GCP override this method, and the mock provider used in CI is
AWS-backed, so the base implementation - the one Azure and OpenStack actually
inherit - is never executed by the networking service suite. It is exercised
here directly against in-memory fakes.
"""
import unittest
from unittest import mock

from cloudbridge.base.resources import BaseNetwork
from cloudbridge.base.services import BaseNetworkService


class _NetworkRecorder:
    """Stands in for provider.networking.networks."""

    def __init__(self, existing=None):
        self.existing = existing or []
        self.created = []
        self.find_labels = []

    def find(self, label=None, **kwargs):
        self.find_labels.append(label)
        return list(self.existing)

    def create(self, label, cidr_block, **kwargs):
        self.created.append((label, cidr_block))
        return ("network", label, cidr_block)


class _FakeProvider:
    def __init__(self, networks):
        self.middleware = mock.Mock()
        self.networking = mock.Mock(networks=networks)


class DefaultNetworkTestCase(unittest.TestCase):

    def test_creates_default_network_with_the_default_cidr(self):
        networks = _NetworkRecorder()
        service = BaseNetworkService(_FakeProvider(networks))

        # Patched away from the built-in so that a hardcoded 10.0.0.0/16 in
        # the service cannot pass by coincidence.
        with mock.patch.object(BaseNetwork, 'CB_DEFAULT_IPV4RANGE',
                               '192.168.0.0/16'):
            service.get_or_create_default()

        self.assertEqual(
            networks.created,
            [(BaseNetwork.CB_DEFAULT_NETWORK_LABEL, '192.168.0.0/16')],
            "The default network must be created with the configured default "
            "CIDR, not a hardcoded one.")

    def test_returns_the_existing_default_network_without_creating(self):
        networks = _NetworkRecorder(existing=["existing-net"])
        service = BaseNetworkService(_FakeProvider(networks))

        self.assertEqual(service.get_or_create_default(), "existing-net")
        self.assertEqual(networks.created, [])
        self.assertEqual(networks.find_labels,
                         [BaseNetwork.CB_DEFAULT_NETWORK_LABEL])


if __name__ == "__main__":
    unittest.main()
