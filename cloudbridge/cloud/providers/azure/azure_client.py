import datetime
import logging
from io import BytesIO

from azure.common import AzureConflictHttpError
from azure.common.credentials import ServicePrincipalCredentials
from azure.cosmosdb.table.tableservice import TableService
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.devtestlabs.models import GalleryImageReference
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobPermissions
from azure.storage.blob import BlockBlobService
from azure.storage.common import TokenCredential

from msrestazure.azure_exceptions import CloudError

import tenacity

from cloudbridge.cloud.interfaces.exceptions import \
    DuplicateResourceException, InvalidLabelException, \
    ProviderConnectionException, WaitStateException

from . import helpers as azure_helpers

log = logging.getLogger(__name__)

IMAGE_RESOURCE_ID = ['/subscriptions/{subscriptionId}/resourceGroups/'
                     '{resourceGroupName}/providers/Microsoft.Compute/'
                     'images/{imageName}',
                     '{imageName}',
                     '{publisher}:{offer}:{sku}:{version}']
NETWORK_RESOURCE_ID = ['/subscriptions/{subscriptionId}/resourceGroups/'
                       '{resourceGroupName}/providers/Microsoft.Network'
                       '/virtualNetworks/{virtualNetworkName}',
                       '{virtualNetworkName}']
NETWORK_INTERFACE_RESOURCE_ID = ['/subscriptions/{subscriptionId}/'
                                 'resourceGroups/{resourceGroupName}'
                                 '/providers/Microsoft.Network/'
                                 'networkInterfaces/{networkInterfaceName}',
                                 '{networkInterfaceName}']
PUBLIC_IP_RESOURCE_ID = ['/subscriptions/{subscriptionId}/resourceGroups'
                         '/{resourceGroupName}/providers/Microsoft.Network'
                         '/publicIPAddresses/{publicIpAddressName}',
                         '{publicIpAddressName}']
ROUTER_RESOURCE_ID = ['/subscriptions/{subscriptionId}'
                      '/resourceGroups/{resourceGroupName}'
                      '/providers/Microsoft.Network/routeTables/{routerName}',
                      '{routerName}']
SNAPSHOT_RESOURCE_ID = ['/subscriptions/{subscriptionId}/resourceGroups/'
                        '{resourceGroupName}/providers/Microsoft.Compute/'
                        'snapshots/{snapshotName}',
                        '{snapshotName}']
SUBNET_RESOURCE_ID = ['/subscriptions/{subscriptionId}/resourceGroups/'
                      '{resourceGroupName}/providers/Microsoft.Network'
                      '/virtualNetworks/{virtualNetworkName}/subnets'
                      '/{subnetName}',
                      '{virtualNetworkName}/{subnetName}']
VM_RESOURCE_ID = ['/subscriptions/{subscriptionId}/resourceGroups/'
                  '{resourceGroupName}/providers/Microsoft.Compute/'
                  'virtualMachines/{vmName}',
                  '{vmName}']
VM_FIREWALL_RESOURCE_ID = ['/subscriptions/{subscriptionId}/'
                           'resourceGroups/{resourceGroupName}/'
                           'providers/Microsoft.Network/'
                           'networkSecurityGroups/'
                           '{networkSecurityGroupName}',
                           '{networkSecurityGroupName}']
VM_FIREWALL_RULE_RESOURCE_ID = ['/subscriptions/{subscriptionId}/'
                                'resourceGroups/{resourceGroupName}/'
                                'providers/Microsoft.Network/'
                                'networkSecurityGroups/'
                                '{networkSecurityGroupName}/'
                                'securityRules/{securityRuleName}',
                                '{securityRuleName}']
VOLUME_RESOURCE_ID = ['/subscriptions/{subscriptionId}/resourceGroups/'
                      '{resourceGroupName}/providers/Microsoft.Compute/'
                      'disks/{diskName}',
                      '{diskName}']

IMAGE_NAME = 'imageName'
NETWORK_NAME = 'virtualNetworkName'
NETWORK_INTERFACE_NAME = 'networkInterfaceName'
PUBLIC_IP_NAME = 'publicIpAddressName'
ROUTER_NAME = 'routerName'
SNAPSHOT_NAME = 'snapshotName'
SUBNET_NAME = 'subnetName'
VM_NAME = 'vmName'
VM_FIREWALL_NAME = 'networkSecurityGroupName'
VM_FIREWALL_RULE_NAME = 'securityRuleName'
VOLUME_NAME = 'diskName'

# Listing possible somewhat through:
# azure.mgmt.devtestlabs.operations.GalleryImageOperations
gallery_image_references = \
    [GalleryImageReference(publisher='Canonical',
                           offer='UbuntuServer',
                           sku='16.04.0-LTS',
                           version='latest'),
     GalleryImageReference(publisher='Canonical',
                           offer='UbuntuServer',
                           sku='14.04.5-LTS',
                           version='latest'),
     GalleryImageReference(publisher='OpenLogic',
                           offer='CentOS',
                           sku='7.5',
                           version='latest'),
     GalleryImageReference(publisher='OpenLogic',
                           offer='CentOS',
                           sku='6.9',
                           version='latest'),
     GalleryImageReference(publisher='MicrosoftWindowsServer',
                           offer='WindowsServer',
                           sku='2016-Nano-Server',
                           version='latest'),
     GalleryImageReference(publisher='MicrosoftWindowsServer',
                           offer='WindowsServer',
                           sku='2016-Datacenter',
                           version='latest'),
     GalleryImageReference(publisher='MicrosoftWindowsDesktop',
                           offer='Windows-10',
                           sku='rs4-pron',
                           version='latest'),
     GalleryImageReference(publisher='MicrosoftVisualStudio',
                           offer='Windows',
                           sku='Windows-10-N-x64',
                           version='latest'),
     GalleryImageReference(publisher='MicrosoftVisualStudio',
                           offer='VisualStudio',
                           sku='VS-2017-Ent-WS2016',
                           version='latest'),
     GalleryImageReference(publisher='MicrosoftSQLServer',
                           offer='SQL2017-WS2016',
                           sku='Web',
                           version='latest'),
     GalleryImageReference(publisher='MicrosoftSQLServer',
                           offer='SQL2017-WS2016',
                           sku='Standard',
                           version='latest'),
     GalleryImageReference(publisher='MicrosoftSQLServer',
                           offer='SQL2017-WS2016',
                           sku='SQLDEV',
                           version='latest'),
     GalleryImageReference(publisher='MicrosoftSQLServer',
                           offer='SQL2017-WS2016',
                           sku='Express',
                           version='latest'),
     GalleryImageReference(publisher='MicrosoftSQLServer',
                           offer='SQL2017-WS2016',
                           sku='Enterprise',
                           version='latest')]


class AzureClient(object):
    """
    Azure client is the wrapper on top of azure python sdk
    """
    def __init__(self, config):
        self._config = config
        self.subscription_id = str(config.get('azure_subscription_id'))
        self._credentials = ServicePrincipalCredentials(
            client_id=config.get('azure_client_id'),
            secret=config.get('azure_secret'),
            tenant=config.get('azure_tenant')
        )

        self._access_token = config.get('azure_access_token')
        self._resource_client = None
        self._storage_client = None
        self._network_management_client = None
        self._subscription_client = None
        self._compute_client = None
        self._access_key_result = None
        self._block_blob_service = None
        self._table_service = None
        self._storage_account = None

        log.debug("azure subscription : %s", self.subscription_id)

    @property
    @tenacity.retry(stop=tenacity.stop_after_attempt(5), reraise=True)
    def access_key_result(self):
        if not self._access_key_result:
            storage_account = self.storage_account

            if self.get_storage_account(storage_account).\
                    provisioning_state.value != 'Succeeded':
                log.debug(
                    "Storage account %s is not in Succeeded state yet. ",
                    storage_account)
                raise WaitStateException(
                    "Waited too long for storage account: {0} to "
                    "become ready.".format(
                        storage_account,
                        self.get_storage_account(storage_account).
                        provisioning_state))

            self._access_key_result = self.storage_client.storage_accounts. \
                list_keys(self.resource_group, storage_account)
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
        self._get_or_create_storage_account()
        if not self._block_blob_service:
            if self._access_token:
                token_credential = TokenCredential(self._access_token)
                self._block_blob_service = BlockBlobService(
                    account_name=self.storage_account,
                    token_credential=token_credential)
            else:
                self._block_blob_service = BlockBlobService(
                    account_name=self.storage_account,
                    account_key=self.access_key_result.keys[0].value)
        return self._block_blob_service

    @property
    def table_service(self):
        self._get_or_create_storage_account()
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

    # Create a storage account. To prevent a race condition, try
    # to get or create at least twice
    @tenacity.retry(stop=tenacity.stop_after_attempt(2),
                    retry=tenacity.retry_if_exception_type(CloudError),
                    reraise=True)
    def _get_or_create_storage_account(self):
        if self._storage_account:
            return self._storage_account
        else:
            try:
                self._storage_account = \
                    self.get_storage_account(self.storage_account)
            except CloudError as cloud_error:
                if cloud_error.error.error == "ResourceNotFound":
                    storage_account_params = {
                        'sku': {
                            'name': 'Standard_LRS'
                        },
                        'kind': 'storage',
                        'location': self.region_name,
                    }
                    try:
                        self._storage_account = \
                            self.create_storage_account(self.storage_account,
                                                        storage_account_params)
                    except CloudError as cloud_error2:  # pragma: no cover
                        if cloud_error2.error.error == "AuthorizationFailed":
                            mess = 'The following error was returned by ' \
                                   'Azure:\n%s\n\nThis is likely because the' \
                                   ' Role associated with the provided ' \
                                   'credentials does not allow for Storage ' \
                                   'Account creation.\nA Storage Account is ' \
                                   'necessary in order to perform the ' \
                                   'desired operation. You must either ' \
                                   'provide an existing Storage Account name' \
                                   ' as part of the configuration, or ' \
                                   'elevate the associated Role.\nFor more ' \
                                   'information on roles, see: https://docs.' \
                                   'microsoft.com/en-us/azure/role-based-' \
                                   'access-control/overview\n' % cloud_error2
                            raise ProviderConnectionException(mess)

                        elif cloud_error2.error.error == \
                                "StorageAccountAlreadyTaken":
                            mess = 'The following error was ' \
                                   'returned by Azure:\n%s\n\n' \
                                   'Note that Storage Account names must be ' \
                                   'unique across Azure (not just in your ' \
                                   'subscription).\nFor more information ' \
                                   'see https://docs.microsoft.com/en-us/' \
                                   'azure/azure-resource-manager/resource-' \
                                   'manager-storage-account-name-errors\n' \
                                   % cloud_error2
                            raise InvalidLabelException(mess)
                        else:
                            raise cloud_error2
                else:
                    raise cloud_error

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

    def update_vm_firewall_tags(self, fw_id, tags):
        url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
                                             fw_id)
        name = url_params.get(VM_FIREWALL_NAME)
        return self.network_management_client.network_security_groups. \
            create_or_update(self.resource_group, name,
                             {'tags': tags,
                              'location': self.region_name}).result()

    def get_vm_firewall(self, fw_id):
        url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
                                             fw_id)
        fw_name = url_params.get(VM_FIREWALL_NAME)
        return self.network_management_client.network_security_groups. \
            get(self.resource_group, fw_name)

    def delete_vm_firewall(self, fw_id):
        url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
                                             fw_id)
        name = url_params.get(VM_FIREWALL_NAME)
        self.network_management_client \
            .network_security_groups.delete(self.resource_group, name).wait()

    def create_vm_firewall_rule(self, fw_id,
                                rule_name, parameters):
        url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
                                             fw_id)
        vm_firewall_name = url_params.get(VM_FIREWALL_NAME)
        return self.network_management_client.security_rules. \
            create_or_update(self.resource_group, vm_firewall_name,
                             rule_name, parameters).result()

    def delete_vm_firewall_rule(self, fw_rule_id, vm_firewall):
        url_params = azure_helpers.parse_url(VM_FIREWALL_RULE_RESOURCE_ID,
                                             fw_rule_id)
        name = url_params.get(VM_FIREWALL_RULE_NAME)
        return self.network_management_client.security_rules. \
            delete(self.resource_group, vm_firewall, name).result()

    def list_containers(self, prefix=None):
        return self.blob_service.list_containers(prefix=prefix)

    def create_container(self, container_name):
        try:
            self.blob_service.create_container(container_name,
                                               fail_on_exist=True)
        except AzureConflictHttpError as cloud_error:
            if cloud_error.error_code == "ContainerAlreadyExists":
                msg = "The given Bucket name '%s' already exists. Please " \
                      "use the `get` or `find` method to get a reference to " \
                      "an existing Bucket, or specify a new Bucket name to " \
                      "create.\nNote that in Azure, Buckets are contained " \
                      "in Storage Accounts." % container_name
                raise DuplicateResourceException(msg)

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
        expiry_date = datetime.datetime.utcnow() + datetime.timedelta(
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
            params
        ).result()

    def create_snapshot_disk(self, disk_name, params):
        return self.compute_client.disks.create_or_update(
            self.resource_group,
            disk_name,
            params
        ).result()

    def get_disk(self, disk_id):
        url_params = azure_helpers.parse_url(VOLUME_RESOURCE_ID,
                                             disk_id)
        disk_name = url_params.get(VOLUME_NAME)
        return self.compute_client.disks.get(self.resource_group, disk_name)

    def list_disks(self):
        return self.compute_client.disks. \
            list_by_resource_group(self.resource_group)

    def delete_disk(self, disk_id):
        url_params = azure_helpers.parse_url(VOLUME_RESOURCE_ID,
                                             disk_id)
        disk_name = url_params.get(VOLUME_NAME)
        self.compute_client.disks.delete(self.resource_group, disk_name).wait()

    def update_disk_tags(self, disk_id, tags):
        url_params = azure_helpers.parse_url(VOLUME_RESOURCE_ID,
                                             disk_id)
        disk_name = url_params.get(VOLUME_NAME)
        return self.compute_client.disks.update(
            self.resource_group,
            disk_name,
            {'tags': tags},
            raw=True
        )

    def list_snapshots(self):
        return self.compute_client.snapshots. \
            list_by_resource_group(self.resource_group)

    def get_snapshot(self, snapshot_id):
        url_params = azure_helpers.parse_url(SNAPSHOT_RESOURCE_ID,
                                             snapshot_id)
        snapshot_name = url_params.get(SNAPSHOT_NAME)
        return self.compute_client.snapshots.get(self.resource_group,
                                                 snapshot_name)

    def create_snapshot(self, snapshot_name, params):
        return self.compute_client.snapshots.create_or_update(
            self.resource_group,
            snapshot_name,
            params
        ).result()

    def delete_snapshot(self, snapshot_id):
        url_params = azure_helpers.parse_url(SNAPSHOT_RESOURCE_ID,
                                             snapshot_id)
        snapshot_name = url_params.get(SNAPSHOT_NAME)
        self.compute_client.snapshots.delete(self.resource_group,
                                             snapshot_name).wait()

    def update_snapshot_tags(self, snapshot_id, tags):
        url_params = azure_helpers.parse_url(SNAPSHOT_RESOURCE_ID,
                                             snapshot_id)
        snapshot_name = url_params.get(SNAPSHOT_NAME)
        return self.compute_client.snapshots.update(
            self.resource_group,
            snapshot_name,
            {'tags': tags},
            raw=True
        )

    def is_gallery_image(self, image_id):
        url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
                                             image_id)
        # If it is a gallery image, it will always have an offer
        return 'offer' in url_params

    def create_image(self, name, params):
        return self.compute_client.images. \
            create_or_update(self.resource_group, name,
                             params).result()

    def delete_image(self, image_id):
        url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
                                             image_id)
        if not self.is_gallery_image(image_id):
            name = url_params.get(IMAGE_NAME)
            self.compute_client.images.delete(self.resource_group, name).wait()

    def list_images(self):
        azure_images = list(self.compute_client.images.
                            list_by_resource_group(self.resource_group))
        return azure_images

    def list_gallery_refs(self):
        return gallery_image_references

    def get_image(self, image_id):
        url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
                                             image_id)
        if self.is_gallery_image(image_id):
            return GalleryImageReference(publisher=url_params['publisher'],
                                         offer=url_params['offer'],
                                         sku=url_params['sku'],
                                         version=url_params['version'])
        else:
            name = url_params.get(IMAGE_NAME)
            return self.compute_client.images.get(self.resource_group, name)

    def update_image_tags(self, image_id, tags):
        url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
                                             image_id)
        if self.is_gallery_image(image_id):
            return True
        else:
            name = url_params.get(IMAGE_NAME)
            return self.compute_client.images. \
                create_or_update(self.resource_group, name,
                                 {
                                     'tags': tags,
                                     'location': self.region_name
                                 }).result()

    def list_vm_types(self):
        return self.compute_client.virtual_machine_sizes. \
            list(self.region_name)

    def list_networks(self):
        return self.network_management_client.virtual_networks.list(
            self.resource_group)

    def get_network(self, network_id):
        url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID,
                                             network_id)
        network_name = url_params.get(NETWORK_NAME)
        return self.network_management_client.virtual_networks.get(
            self.resource_group, network_name)

    def create_network(self, name, params):
        return self.network_management_client.virtual_networks. \
            create_or_update(self.resource_group,
                             name,
                             parameters=params).result()

    def delete_network(self, network_id):
        url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
        network_name = url_params.get(NETWORK_NAME)
        return self.network_management_client.virtual_networks. \
            delete(self.resource_group, network_name).wait()

    def update_network_tags(self, network_id, tags):
        url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
        network_name = url_params.get(NETWORK_NAME)
        return self.network_management_client.virtual_networks. \
            create_or_update(self.resource_group,
                             network_name, tags).result()

    def get_network_id_for_subnet(self, subnet_id):
        url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID, subnet_id)
        network_id = NETWORK_RESOURCE_ID[0]
        for key, val in url_params.items():
            network_id = network_id.replace("{" + key + "}", val)
        return network_id

    def list_subnets(self, network_id):
        url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
        network_name = url_params.get(NETWORK_NAME)
        return self.network_management_client.subnets. \
            list(self.resource_group, network_name)

    def get_subnet(self, subnet_id):
        url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
                                             subnet_id)
        network_name = url_params.get(NETWORK_NAME)
        subnet_name = url_params.get(SUBNET_NAME)
        return self.network_management_client.subnets. \
            get(self.resource_group, network_name, subnet_name)

    def create_subnet(self, network_id, subnet_name, params):
        url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
        network_name = url_params.get(NETWORK_NAME)
        result_create = self.network_management_client \
            .subnets.create_or_update(
                self.resource_group,
                network_name,
                subnet_name,
                params
            )
        subnet_info = result_create.result()

        return subnet_info

    def __if_subnet_in_use(e):
        # return True if the CloudError exception is due to subnet being in use
        if isinstance(e, CloudError):
            if e.error.error == "InUseSubnetCannotBeDeleted":
                return True
        return False

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception(__if_subnet_in_use),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def delete_subnet(self, subnet_id):
        url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
                                             subnet_id)
        network_name = url_params.get(NETWORK_NAME)
        subnet_name = url_params.get(SUBNET_NAME)

        try:
            result_delete = self.network_management_client \
                .subnets.delete(
                    self.resource_group,
                    network_name,
                    subnet_name
                )
            result_delete.wait()
        except CloudError as cloud_error:
            log.exception(cloud_error.message)
            raise cloud_error

    def create_floating_ip(self, public_ip_name, public_ip_parameters):
        return self.network_management_client.public_ip_addresses. \
            create_or_update(self.resource_group,
                             public_ip_name,
                             public_ip_parameters).result()

    def get_floating_ip(self, public_ip_id):
        url_params = azure_helpers.parse_url(PUBLIC_IP_RESOURCE_ID,
                                             public_ip_id)
        public_ip_name = url_params.get(PUBLIC_IP_NAME)
        return self.network_management_client. \
            public_ip_addresses.get(self.resource_group, public_ip_name)

    def delete_floating_ip(self, public_ip_id):
        url_params = azure_helpers.parse_url(PUBLIC_IP_RESOURCE_ID,
                                             public_ip_id)
        public_ip_name = url_params.get(PUBLIC_IP_NAME)
        self.network_management_client. \
            public_ip_addresses.delete(self.resource_group,
                                       public_ip_name).wait()

    def update_fip_tags(self, fip_id, tags):
        url_params = azure_helpers.parse_url(PUBLIC_IP_RESOURCE_ID,
                                             fip_id)
        fip_name = url_params.get(PUBLIC_IP_NAME)
        self.network_management_client.public_ip_addresses. \
            create_or_update(self.resource_group,
                             fip_name, tags).result()

    def list_floating_ips(self):
        return self.network_management_client.public_ip_addresses.list(
            self.resource_group)

    def list_vm(self):
        return self.compute_client.virtual_machines.list(
            self.resource_group
        )

    def restart_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME)
        return self.compute_client.virtual_machines.restart(
            self.resource_group, vm_name).wait()

    def delete_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME)
        return self.compute_client.virtual_machines.delete(
            self.resource_group, vm_name).wait()

    def get_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME)
        return self.compute_client.virtual_machines.get(
            self.resource_group,
            vm_name,
            expand='instanceView'
        )

    def create_vm(self, vm_name, params):
        return self.compute_client.virtual_machines. \
            create_or_update(self.resource_group,
                             vm_name, params).result()

    def update_vm(self, vm_id, params):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME)
        return self.compute_client.virtual_machines. \
            create_or_update(self.resource_group,
                             vm_name, params, raw=True)

    def deallocate_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME)
        self.compute_client. \
            virtual_machines.deallocate(self.resource_group,
                                        vm_name).wait()

    def generalize_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME)
        self.compute_client.virtual_machines. \
            generalize(self.resource_group, vm_name)

    def start_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME)
        self.compute_client.virtual_machines. \
            start(self.resource_group,
                  vm_name).wait()

    def update_vm_tags(self, vm_id, tags):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME)
        self.compute_client.virtual_machines. \
            create_or_update(self.resource_group,
                             vm_name, tags).result()

    def delete_nic(self, nic_id):
        nic_params = azure_helpers.\
            parse_url(NETWORK_INTERFACE_RESOURCE_ID, nic_id)
        nic_name = nic_params.get(NETWORK_INTERFACE_NAME)
        self.network_management_client. \
            network_interfaces.delete(self.resource_group,
                                      nic_name).wait()

    def get_nic(self, nic_id):
        nic_params = azure_helpers.\
            parse_url(NETWORK_INTERFACE_RESOURCE_ID, nic_id)
        nic_name = nic_params.get(NETWORK_INTERFACE_NAME)
        return self.network_management_client. \
            network_interfaces.get(self.resource_group, nic_name)

    def update_nic(self, nic_id, params):
        nic_params = azure_helpers.\
            parse_url(NETWORK_INTERFACE_RESOURCE_ID, nic_id)
        nic_name = nic_params.get(NETWORK_INTERFACE_NAME)
        async_nic_creation = self.network_management_client. \
            network_interfaces.create_or_update(
                self.resource_group,
                nic_name,
                params
            )
        nic_info = async_nic_creation.result()
        return nic_info

    def create_nic(self, nic_name, params):
        return self.network_management_client. \
            network_interfaces.create_or_update(
                self.resource_group,
                nic_name,
                params
            ).result()

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

    def list_public_keys(self, partition_key, limit=None, marker=None):
        entities = self.table_service. \
            query_entities(self.public_key_storage_table_name,
                           "PartitionKey eq '{0}'".format(partition_key),
                           marker=marker, num_results=limit)
        return (entities.items, entities.next_marker)

    def delete_route_table(self, route_table_name):
        self.network_management_client. \
            route_tables.delete(self.resource_group, route_table_name
                                ).wait()

    def attach_subnet_to_route_table(self, subnet_id, route_table_id):
        url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
                                             subnet_id)
        network_name = url_params.get(NETWORK_NAME)
        subnet_name = url_params.get(SUBNET_NAME)

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

    def detach_subnet_to_route_table(self, subnet_id, route_table_id):
        url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
                                             subnet_id)
        network_name = url_params.get(NETWORK_NAME)
        subnet_name = url_params.get(SUBNET_NAME)

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
        url_params = azure_helpers.parse_url(ROUTER_RESOURCE_ID,
                                             router_id)
        router_name = url_params.get(ROUTER_NAME)
        return self.network_management_client. \
            route_tables.get(self.resource_group, router_name)

    def create_route_table(self, route_table_name, params):
        return self.network_management_client. \
            route_tables.create_or_update(
             self.resource_group,
             route_table_name, params).result()

    def update_route_table_tags(self, route_table_name, tags):
        self.network_management_client.route_tables. \
            create_or_update(self.resource_group,
                             route_table_name, tags).result()
