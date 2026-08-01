"""
Unit tests for how ``AWSDnsRecordService`` waits on Route53 changes.

Creating or deleting a record blocks until Route53 reports the change INSYNC.
boto3's ``resource_record_sets_changed`` waiter polls every 30 seconds by
default, so a change that propagates in a few seconds still costs a full 30 --
and a test that makes four record changes pays 120 seconds of pure sleep.
Measured against real Route53, INSYNC was reached within the first poll
interval every time, making the granularity the entire cost.

These tests drive the real botocore waiter against a simulated clock, so they
assert on how long we *would* sleep without actually sleeping.
"""
import unittest
from unittest import mock

import botocore.client
import botocore.waiter
from botocore.exceptions import WaiterError

from cloudbridge.providers.aws import AWSCloudProvider
from cloudbridge.providers.aws.resources import AWSDnsRecord
from cloudbridge.providers.aws.resources import AWSDnsZone
from cloudbridge.providers.aws.services import AWSDnsRecordService

# Simulated seconds before Route53 reports INSYNC. Real-world measurement put
# this comfortably inside one 30s poll interval.
INSYNC_AFTER = 6.0
BOTO_DEFAULT_DELAY = 30.0
# The waiter's ceiling must stay at roughly 30 minutes however it is polled.
REQUIRED_CEILING = 1700.0

ZONE = {'Id': '/hostedzone/Z1EXAMPLE', 'Name': 'example.com.'}
RECORD = {'Name': 'sub.example.com.', 'Type': 'CNAME', 'TTL': 500,
          'ResourceRecords': [{'Value': 'hello.com.'}]}


class _Route53Sim:
    """Canned Route53 responses driven by a simulated clock."""

    def __init__(self, insync_after=INSYNC_AFTER):
        self.insync_after = insync_after
        self.clock = 0.0
        self.sleeps = []
        self.get_change_calls = 0

    def api(self, operation_name, params):
        if operation_name == 'ChangeResourceRecordSets':
            return {'ChangeInfo': {'Id': '/change/C1', 'Status': 'PENDING'}}
        if operation_name == 'GetChange':
            self.get_change_calls += 1
            status = ('INSYNC' if self.clock >= self.insync_after
                      else 'PENDING')
            return {'ChangeInfo': {'Id': '/change/C1', 'Status': status}}
        if operation_name == 'ListResourceRecordSets':
            return {'ResourceRecordSets': [RECORD], 'IsTruncated': False}
        raise AssertionError('unexpected operation: ' + operation_name)

    def sleep(self, secs):
        self.sleeps.append(secs)
        self.clock += secs

    @property
    def total_wait(self):
        return sum(self.sleeps)


def _provider():
    return AWSCloudProvider({'aws_access_key': 'dummy',
                             'aws_secret_key': 'dummy',
                             'aws_zone_name': 'us-east-1a'})


def _run(sim, fn):
    """Run fn with Route53 stubbed and the waiter's clock simulated."""
    with mock.patch.object(botocore.client.BaseClient, '_make_api_call',
                           lambda self, op, params: sim.api(op, params)), \
            mock.patch.object(botocore.waiter.time, 'sleep', sim.sleep):
        return fn()


class AWSDnsWaiterTestCase(unittest.TestCase):

    def setUp(self):
        self.provider = _provider()
        self.svc = AWSDnsRecordService(self.provider)
        self.zone = AWSDnsZone(self.provider, ZONE)
        self.record = AWSDnsRecord(self.provider, self.zone, RECORD)

    def test_create_does_not_burn_a_full_poll_interval_on_a_fast_change(self):
        sim = _Route53Sim()

        _run(sim, lambda: self.svc.create(
            self.zone, 'sub.example.com.', 'CNAME', 'hello.com', ttl=500))

        self.assertLess(
            sim.total_wait, BOTO_DEFAULT_DELAY,
            "A change that went INSYNC after %ss cost %ss of sleep; the "
            "waiter is still polling at boto3's %ss default"
            % (INSYNC_AFTER, sim.total_wait, BOTO_DEFAULT_DELAY))

    def test_delete_does_not_burn_a_full_poll_interval_on_a_fast_change(self):
        sim = _Route53Sim()

        _run(sim, lambda: self.svc.delete(self.zone, self.record))

        self.assertLess(
            sim.total_wait, BOTO_DEFAULT_DELAY,
            "A change that went INSYNC after %ss cost %ss of sleep; the "
            "waiter is still polling at boto3's %ss default"
            % (INSYNC_AFTER, sim.total_wait, BOTO_DEFAULT_DELAY))

    def test_waiter_polls_until_the_change_is_actually_insync(self):
        """Faster polling must not mean giving up early."""
        sim = _Route53Sim(insync_after=47.0)

        _run(sim, lambda: self.svc.create(
            self.zone, 'sub.example.com.', 'CNAME', 'hello.com', ttl=500))

        self.assertGreaterEqual(sim.clock, 47.0,
                                "Returned before the change was INSYNC")
        self.assertGreater(sim.get_change_calls, 1)

    def test_waiter_ceiling_is_still_about_thirty_minutes(self):
        """Polling more often must not shrink how long we are willing to
        wait -- a genuinely slow change should still be given ~30 minutes
        before the waiter gives up."""
        sim = _Route53Sim(insync_after=float('inf'))

        with self.assertRaises(WaiterError):
            _run(sim, lambda: self.svc.create(
                self.zone, 'sub.example.com.', 'CNAME', 'hello.com', ttl=500))

        self.assertGreaterEqual(
            sim.total_wait, REQUIRED_CEILING,
            "Waiter gave up after only %ss of simulated waiting"
            % sim.total_wait)


if __name__ == '__main__':
    unittest.main()
