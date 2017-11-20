import datetime
import logging
from io import BytesIO

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobPermissions
from azure.storage.blob import BlockBlobService
from azure.storage.table import TableService

log = logging.getLogger(__name__)


class AzureClient(object):
    """
    Azure client is the wrapper on top of azure python sdk
    """
    def __init__(self, config):
        self._config = config
        self.subscription_id = config.get('azure_subscription_id')
        self._credentials = ServicePrincipalCredentials(
            client_id=config.get('azure_client_id'),
            secret=config.get('azure_secret'),
            tenant=config.get('azure_tenant')
        )

        self._resource_client = None
        self._storage_client = None
        self._network_management_client = None
        self._subscription_client = None
        self._compute_client = None
        self._access_key_result = None
        self._block_blob_service = None
        self._table_service = None

        log.debug("azure subscription : %s", self.subscription_id)

    @property
    def access_key_result(self):
        if not self._access_key_result:
            self._access_key_result = self.storage_client.storage_accounts. \
                list_keys(self.resource_group, self.storage_account)
        return self._access_key_result

    @property
    def resource_group(self):
        return self._config.get('azure_resource_group')

    @property
    def storage_account(self):
        return self._config.get('azure_storage_account')

    @property
    def region_name(self):
        return self._config.get('azure_region_name')

    @property
    def public_key_storage_table_name(self):
        return self._config.get('azure_public_key_storage_table_name')

    @property
    def storage_client(self):
        if not self._storage_client:
            self._storage_client = \
                StorageManagementClient(self._credentials,
                                        self.subscription_id)
        return self._storage_client

    @property
    def subscription_client(self):
        if not self._subscription_client:
            self._subscription_client = SubscriptionClient(self._credentials)
        return self._subscription_client

    @property
    def resource_client(self):
        if not self._resource_client:
            self._resource_client = \
                ResourceManagementClient(self._credentials,
                                         self.subscription_id)
        return self._resource_client

    @property
    def compute_client(self):
        if not self._compute_client:
            self._compute_client = \
                ComputeManagementClient(self._credentials,
                                        self.subscription_id)
        return self._compute_client

    @property
    def network_management_client(self):
        if not self._network_management_client:
            self._network_management_client = NetworkManagementClient(
                self._credentials, self.subscription_id)
        return self._network_management_client

    @property
    def blob_service(self):
        if not self._block_blob_service:
            self._block_blob_service = BlockBlobService(
                self.storage_account,
                self.access_key_result.keys[0].value)
        return self._block_blob_service

    @property
    def table_service(self):
        if not self._table_service:
            self._table_service = TableService(
                self.storage_account,
                self.access_key_result.keys[0].value)
        if not self._table_service. \
                exists(table_name=self.public_key_storage_table_name):
            self._table_service.create_table(
                self.public_key_storage_table_name)
        return self._table_service

    def get_resource_group(self, name):
        return self.resource_client.resource_groups.get(name)

    def create_resource_group(self, name, parameters):
        return self.resource_client.resource_groups. \
            create_or_update(name, parameters)

    def get_storage_account(self, storage_account):
        return self.storage_client.storage_accounts. \
            get_properties(self.resource_group, storage_account)

    def create_storage_account(self, name, params):
        return self.storage_client.storage_accounts. \
            create(self.resource_group, name.lower(), params).result()

    def list_locations(self):
        return self.subscription_client.subscriptions. \
            list_locations(self.subscription_id)

    def list_vm_firewall(self):
        return self.network_management_client.network_security_groups. \
            list(self.resource_group)

    def create_vm_firewall(self, name, parameters):
        return self.network_management_client.network_security_groups. \
            create_or_update(self.resource_group, name,
                             parameters).result()

    def update_vm_firewall_tags(self, name, tags):
        return self.network_management_client.network_security_groups. \
            create_or_update(self.resource_group, name,
                             {'tags': tags,
                              'location': self.region_name}).result()

    def create_vm_firewall_rule(self, vm_firewall,
                                rule_name, parameters):
        return self.network_management_client.security_rules. \
            create_or_update(self.resource_group, vm_firewall,
                             rule_name, parameters).result()

    def delete_vm_firewall_rule(self, name, vm_firewall):
        return self.network_management_client.security_rules. \
            delete(self.resource_group, vm_firewall, name).result()

    def get_vm_firewall(self, name):
        return self.network_management_client.network_security_groups. \
            get(self.resource_group, name)

    def delete_vm_firewall(self, name):
        delete_async = self.network_management_client \
            .network_security_groups. \
            delete(self.resource_group, name)
        delete_async.wait()

    def list_containers(self, prefix=None):
        return self.blob_service.list_containers(prefix=prefix)

    def create_container(self, container_name):
        self.blob_service.create_container(container_name)
        return self.blob_service.get_container_properties(container_name)

    def get_container(self, container_name):
        return self.blob_service.get_container_properties(container_name)

    def delete_container(self, container_name):
        self.blob_service.delete_container(container_name)

    def list_blobs(self, container_name, prefix=None):
        return self.blob_service.list_blobs(container_name, prefix=prefix)

    def get_blob(self, container_name, blob_name):
        return self.blob_service.get_blob_properties(container_name, blob_name)

    def create_blob_from_text(self, container_name, blob_name, text):
        self.blob_service.create_blob_from_text(container_name,
                                                blob_name, text)

    def create_blob_from_file(self, container_name, blob_name, file_path):
        self.blob_service.create_blob_from_path(container_name,
                                                blob_name, file_path)

    def delete_blob(self, container_name, blob_name):
        self.blob_service.delete_blob(container_name, blob_name)

    def get_blob_url(self, container_name, blob_name, expiry_time):
        expiry_date = datetime.datetime.now() + datetime.timedelta(
            seconds=expiry_time)
        sas = self.blob_service.generate_blob_shared_access_signature(
            container_name, blob_name, permission=BlobPermissions.READ,
            expiry=expiry_date)
        return self.blob_service.make_blob_url(container_name, blob_name,
                                               sas_token=sas)

    def get_blob_content(self, container_name, blob_name):
        out_stream = BytesIO()
        self.blob_service.get_blob_to_stream(container_name,
                                             blob_name, out_stream)
        return out_stream

    def create_empty_disk(self, disk_name, params):
        return self.compute_client.disks.create_or_update(
            self.resource_group,
            disk_name,
            params,
            raw=True
        )

    def create_snapshot_disk(self, disk_name, params):
        return self.compute_client.disks.create_or_update(
            self.resource_group,
            disk_name,
            params,
            raw=True
        )

    def list_snapshots(self):
        return self.compute_client.snapshots. \
            list_by_resource_group(self.resource_group)

    def update_disk_tags(self, disk_name, tags):
        return self.compute_client.disks.update(
            self.resource_group,
            disk_name,
            {'tags': tags},
            raw=True
        )

    def get_disk(self, disk_name):
        return self.compute_client.disks. \
            get(self.resource_group, disk_name)

    def list_networks(self):
        return self.network_management_client.virtual_networks.list(
            self.resource_group)

    def get_network(self, network_name):
        return self.network_management_client.virtual_networks.get(
            self.resource_group, network_name)

    def create_network(self, name, params):
        return self.network_management_client.virtual_networks. \
            create_or_update(self.resource_group,
                             name,
                             parameters=params,
                             raw=True)

    def delete_network(self, network_name):
        return self.network_management_client.virtual_networks. \
            delete(self.resource_group, network_name).wait()

    def create_floating_ip(self, public_ip_name, public_ip_parameters):
        return self.network_management_client.public_ip_addresses. \
            create_or_update(self.resource_group,
                             public_ip_name,
                             public_ip_parameters).result()

    def delete_floating_ip(self, public_ip_address_name):
        return self.network_management_client.public_ip_addresses. \
            delete(self.resource_group,
                   public_ip_address_name).result()

    def list_floating_ips(self):
        return self.network_management_client.public_ip_addresses.list(
            self.resource_group)

    def update_network_tags(self, network_name, tags):
        return self.network_management_client.virtual_networks. \
            create_or_update(self.resource_group,
                             network_name, tags).result()

    def list_disks(self):
        return self.compute_client.disks. \
            list_by_resource_group(self.resource_group)

    def delete_disk(self, disk_name):
        async_deletion = self.compute_client.disks. \
            delete(self.resource_group, disk_name)
        async_deletion.wait()

    def get_snapshot(self, snapshot_name):
        return self.compute_client.snapshots.get(self.resource_group,
                                                 snapshot_name)

    def create_snapshot(self, snapshot_name, params):
        return self.compute_client.snapshots.create_or_update(
            self.resource_group,
            snapshot_name,
            params,
            raw=True
        )

    def delete_snapshot(self, snapshot_name):
        async_delete = self.compute_client.snapshots. \
            delete(self.resource_group, snapshot_name)
        async_delete.wait()

    def update_snapshot_tags(self, snapshot_name, tags):
        return self.compute_client.snapshots.update(
            self.resource_group,
            snapshot_name,
            {'tags': tags},
            raw=True
        )

    def create_image(self, name, params):
        return self.compute_client.images. \
            create_or_update(self.resource_group, name,
                             params, raw=True)

    def delete_image(self, name):
        self.compute_client.images. \
            delete(self.resource_group, name).wait()

    def list_images(self):
        return self.compute_client.images. \
            list_by_resource_group(self.resource_group)

    def get_image(self, image_name):
        return self.compute_client.images. \
            get(self.resource_group, image_name)

    def update_image_tags(self, name, tags):
        return self.compute_client.images. \
            create_or_update(self.resource_group, name,
                             {
                                 'tags': tags,
                                 'location': self.region_name
                             }).result()

    def list_instance_types(self):
        return self.compute_client.virtual_machine_sizes. \
            list(self.region_name)

    def list_subnets(self, network_name):
        return self.network_management_client.subnets.\
            list(self.resource_group, network_name)

    def get_subnet(self, network_name, subnet_name):
        return self.network_management_client.subnets.\
            get(self.resource_group, network_name, subnet_name)

    def create_subnet(self, network_name,
                      subnet_name, params):
        result_create = self.network_management_client \
            .subnets.create_or_update(
                self.resource_group,
                network_name,
                subnet_name,
                params
            )
        subnet_info = result_create.result()

        return subnet_info

    def delete_subnet(self, network_name, subnet_name):
        result_delete = self.network_management_client \
            .subnets.delete(
                self.resource_group,
                network_name,
                subnet_name
            )
        result_delete.wait()

    def list_vm(self):
        return self.compute_client.virtual_machines.list(
            self.resource_group
        )

    def restart_vm(self, vm_name):
        return self.compute_client.virtual_machines.restart(
            self.resource_group,
            vm_name
        ).wait()

    def delete_vm(self, vm_name):
        return self.compute_client.virtual_machines.delete(
            self.resource_group,
            vm_name
        ).wait()

    def get_vm(self, vm_name):
        return self.compute_client.virtual_machines.get(
            self.resource_group,
            vm_name,
            expand='instanceView'
        )

    def create_vm(self, vm_name, params):
        return self.compute_client.virtual_machines. \
            create_or_update(self.resource_group,
                             vm_name, params, raw=True)

    def deallocate_vm(self, vm_name):
        self.compute_client. \
            virtual_machines.deallocate(self.resource_group,
                                        vm_name).wait()

    def generalize_vm(self, vm_name):
        self.compute_client.virtual_machines. \
            generalize(self.resource_group, vm_name)

    def start_vm(self, vm_name):
        self.compute_client.virtual_machines. \
            start(self.resource_group,
                  vm_name).wait()

    def update_vm_tags(self, vm_name, tags):
        self.compute_client.virtual_machines. \
            create_or_update(self.resource_group,
                             vm_name, tags).result()

    def delete_nic(self, nic_name):
        self.network_management_client. \
            network_interfaces.delete(self.resource_group,
                                      nic_name).wait()

    def get_nic(self, name):
        return self.network_management_client. \
            network_interfaces.get(self.resource_group, name)

    def create_nic(self, nic_name, params):
        async_nic_creation = self.network_management_client. \
            network_interfaces.create_or_update(
                self.resource_group,
                nic_name,
                params
            )
        nic_info = async_nic_creation.result()

        return nic_info

    def get_public_ip(self, name):
        return self.network_management_client. \
            public_ip_addresses.get(self.resource_group, name)

    def delete_public_ip(self, public_ip_name):
        self.network_management_client. \
            public_ip_addresses.delete(self.resource_group,
                                       public_ip_name).wait()

    def create_public_key(self, entity):

        return self.table_service. \
            insert_or_replace_entity(self.public_key_storage_table_name,
                                     entity)

    def get_public_key(self, name):
        entities = self.table_service. \
            query_entities(self.public_key_storage_table_name,
                           "Name eq '{0}'".format(name), num_results=1)

        return entities.items[0] if len(entities.items) > 0 else None

    def delete_public_key(self, entity):
        self.table_service.delete_entity(self.public_key_storage_table_name,
                                         entity.PartitionKey, entity.RowKey)

    def list_public_keys(self, partition_key):
        items = []
        next_marker = None
        while True:
            entities = self.table_service. \
                query_entities(self.public_key_storage_table_name,
                               "PartitionKey eq '{0}'".format(partition_key),
                               marker=next_marker, num_results=1)
            items.extend(entities.items)
            next_marker = entities.next_marker
            if not next_marker:
                break
        return items

    def delete_route_table(self, route_table_name):
        self.network_management_client. \
            route_tables.delete(self.resource_group, route_table_name
                                ).wait()

    def attach_subnet_to_route_table(self, network_name,
                                     subnet_name, route_table_id):

        subnet_info = self.network_management_client.subnets.get(
            self.resource_group,
            network_name,
            subnet_name
        )
        if subnet_info:
            subnet_info.route_table = {
                'id': route_table_id
            }

            result_create = self.network_management_client. \
                subnets.create_or_update(
                 self.resource_group,
                 network_name,
                 subnet_name,
                 subnet_info)
            subnet_info = result_create.result()

        return subnet_info

    def detach_subnet_to_route_table(self, network_name,
                                     subnet_name, route_table_id):

        subnet_info = self.network_management_client.subnets.get(
            self.resource_group,
            network_name,
            subnet_name
        )

        if subnet_info and subnet_info.route_table.id == route_table_id:
            subnet_info.route_table = None

            result_create = self.network_management_client. \
                subnets.create_or_update(
                 self.resource_group,
                 network_name,
                 subnet_name,
                 subnet_info)
            subnet_info = result_create.result()

        return subnet_info

    def list_route_tables(self):
        return self.network_management_client. \
            route_tables.list(self.resource_group)

    def get_route_table(self, router_id):
        return self.network_management_client. \
            route_tables.get(self.resource_group, router_id)

    def create_route_table(self, route_table_name, params):
        return self.network_management_client. \
            route_tables.create_or_update(
             self.resource_group,
             route_table_name, params).result()

    def update_route_table_tags(self, route_table_name, tags):
        self.network_management_client.route_tables. \
            create_or_update(self.resource_group,
                             route_table_name, tags).result()
