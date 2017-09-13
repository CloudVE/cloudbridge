import time
import uuid

from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit

from cloudbridge.cloud.interfaces import SnapshotState
from cloudbridge.cloud.interfaces import VolumeState
from cloudbridge.cloud.interfaces.resources import AttachmentInfo

import six


class CloudSnapshotServiceTestCase(ProviderTestBase):
    def test_crud_snapshot_a(self):
        name = "cb_crudsnap-{0}".format(helpers.get_uuid())
        test_vol = self.provider.block_store.volumes.create(
            name,
            1,
            helpers.get_provider_test_data(self.provider, "placement"))
        with helpers.cleanup_action(lambda: test_vol.delete()):
            test_vol.wait_till_ready()
            snap_name = "cb_snap-{0}".format(name)
            test_snap = test_vol.create_snapshot(name=snap_name,
                                                 description=snap_name)

            def cleanup_snap(snap):
                snap.delete()
                snap.wait_for(
                    [SnapshotState.UNKNOWN],
                    terminal_states=[SnapshotState.ERROR])

            with helpers.cleanup_action(lambda: cleanup_snap(test_snap)):
                test_snap.wait_till_ready()
                print(test_snap.state)
                for x in range(0, 20):
                    list_objs = self.provider.block_store.snapshots.list()
                    all_records = list_objs
                    while list_objs.is_truncated:
                        list_objs = self.provider.block_store.snapshots.list(marker=list_objs.marker)
                        all_records += list_objs
                    match_objs = [o for o in all_records if o.id == test_snap.id]
                    print("List - " + match_objs[0].state)
                    # obj = self.provider.block_store.snapshots.get(test_snap.id)
                    # print("Get - " + obj.state)
