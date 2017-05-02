import azure_test.helpers as helpers
from azure_test.helpers import ProviderTestBase


class AzureSnapshotsServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_azure_snapshots_list(self):
        snapshot_list = self.provider \
            .block_store.snapshots.list()
        print("Snapshot List - " + str(snapshot_list))
        self.assertTrue(
            snapshot_list.total_results > 0)
