from cloudbridge.cloud.interfaces import VolumeState
from cloudbridge.cloud.interfaces.exceptions import WaitStateException

from test import helpers
from test.helpers import ProviderTestBase


class CloudObjectLifeCycleTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    @helpers.skipIfNoService(['storage.volumes'])
    def test_object_life_cycle(self):
        """
        Test object life cycle methods by using a volume.
        """
        label = "cb-objlifecycle-{0}".format(helpers.get_uuid())
        test_vol = self.provider.storage.volumes.create(
            label, 1,
            helpers.get_provider_test_data(self.provider, "placement"))

        # Waiting for an invalid timeout should raise an exception
        with self.assertRaises(AssertionError):
            test_vol.wait_for([VolumeState.ERROR], timeout=-1, interval=1)
        with self.assertRaises(AssertionError):
            test_vol.wait_for([VolumeState.ERROR], timeout=1, interval=-1)

        # If interval < timeout, an exception should be raised
        with self.assertRaises(AssertionError):
            test_vol.wait_for([VolumeState.ERROR], timeout=10, interval=20)

        with helpers.cleanup_action(lambda: test_vol.delete()):
            test_vol.wait_till_ready()
            # Hitting a terminal state should raise an exception
            with self.assertRaises(WaitStateException):
                test_vol.wait_for([VolumeState.ERROR],
                                  terminal_states=[VolumeState.AVAILABLE])

            # Hitting the timeout should raise an exception
            with self.assertRaises(WaitStateException):
                test_vol.wait_for([VolumeState.ERROR], timeout=0, interval=0)
