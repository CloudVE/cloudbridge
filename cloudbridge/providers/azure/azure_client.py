import datetime
import logging

import tenacity
from cloudbridge.interfaces.exceptions import (DuplicateResourceException,
                                               InvalidLabelException,
                                               ProviderConnectionException,
                                               WaitStateException)

from azure.core.credentials import AzureNamedKeyCredential
from azure.core.exceptions import (ClientAuthenticationError,
                                   HttpResponseError, ResourceExistsError,
                                   ResourceNotFoundError)
from azure.data.tables import TableServiceClient
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import (CreationData, Disk, DiskUpdate, Image,
                                       ImageUpdate, Snapshot, SnapshotUpdate,
                                       VirtualMachine, VirtualMachineUpdate)
from azure.mgmt.devtestlabs.models import GalleryImageReference
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.dns.models import Zone
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import (NetworkInterface,
                                       NetworkSecurityGroup, PublicIPAddress,
                                       RouteTable, SecurityRule, SubResource,
                                       Subnet, TagsObject, VirtualNetwork)
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import Sku, StorageAccountCreateParameters
from azure.mgmt.subscription import SubscriptionClient
from azure.storage.blob import (BlobBlock, BlobSasPermissions,
                                BlobServiceClient, generate_blob_sas)

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
        self._credentials = ClientSecretCredential(
            tenant_id=config.get('azure_tenant'),
            client_id=config.get('azure_client_id'),
            client_secret=config.get('azure_secret')
        )

        self._access_token = config.get('azure_access_token')
        self._resource_client = None
        self._storage_client = None
        self._network_management_client = None
        self._subscription_client = None
        self._compute_client = None
        self._dns_client = None
        self._access_key_result = None
        self._block_blob_service = None
        self._table_service_client = None
        self._public_key_table_client = None
        self._storage_account = None

        log.debug("azure subscription : %s", self.subscription_id)

    # Storage account creation transitions through Creating -> ResolvingDns
    # -> Succeeded. ResolvingDns alone is typically 30-60s for the public
    # blob endpoint; the original retry config (5 attempts, no wait) gave
    # up in ~100ms and surfaced as WaitStateException on any cold start.
    # Allow ~1.5 minutes total with a fixed backoff, and only retry on the
    # not-yet-ready signal so genuine errors fail fast.
    @property
    @tenacity.retry(
        stop=tenacity.stop.stop_after_attempt(9),
        wait=tenacity.wait_fixed(10),
        retry=tenacity.retry_if_exception_type(WaitStateException),
        reraise=True,
    )
    def access_key_result(self):
        if not self._access_key_result:
            storage_account = self.storage_account

            if self.get_storage_account(storage_account).\
                    provisioning_state != 'Succeeded':
                log.debug(
                    "Storage account %s is not in Succeeded state yet. ",
                    storage_account)
                raise WaitStateException(
                    "Waited too long for storage account: {0} to "
                    "become ready. It's currently in state: {1}".format(
                        storage_account,
                        self.get_storage_account(
                            storage_account).provisioning_state))

            self._access_key_result = self.storage_client.storage_accounts. \
                list_keys(self.resource_group, storage_account)
        return self._access_key_result

    @property
    def resource_group(self):
        return self._config.get('azure_resource_group')

    @property
    def networking_resource_group(self):
        return self._config.get('azure_networking_resource_group')

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
    def dns_client(self):
        if not self._dns_client:
            self._dns_client = DnsManagementClient(
                self._credentials, self.subscription_id)
        return self._dns_client

    @property
    def blob_service(self):
        self._get_or_create_storage_account()
        if not self._block_blob_service:
            if self._access_token:
                self._block_blob_service = BlobServiceClient(
                    account_url=f"https://{self.storage_account}.blob.core.windows.net/",
                    credential=self._access_token)
            else:
                self._block_blob_service = BlobServiceClient(
                    account_url=f"https://{self.storage_account}.blob.core.windows.net/",
                    credential=self._credentials)
        return self._block_blob_service

    @property
    def table_service(self):
        self._get_or_create_storage_account()
        if not self._table_service_client:
            credential = AzureNamedKeyCredential(
                self.storage_account,
                self.access_key_result.keys[0].value)
            self._table_service_client = TableServiceClient(
                endpoint=f"https://{self.storage_account}.table.core.windows.net/",
                credential=credential)
        if not self._public_key_table_client:
            self._public_key_table_client = \
                self._table_service_client.create_table_if_not_exists(
                    table_name=self.public_key_storage_table_name)
        return self._public_key_table_client

    def blob_client(self, container_name, blob_name):
        return self.blob_service.get_blob_client(container=container_name, blob=blob_name)

    def get_resource_group(self, name):
        return self.resource_client.resource_groups.get(name)

    def create_resource_group(self, name, parameters):
        return self.resource_client.resource_groups. \
            create_or_update(name, ResourceGroup(**parameters))

    def get_storage_account(self, storage_account):
        return self.storage_client.storage_accounts. \
            get_properties(self.resource_group, storage_account)

    def create_storage_account(self, name, params):
        return self.storage_client.storage_accounts. \
            begin_create(self.resource_group, name.lower(),
                         StorageAccountCreateParameters(**params)).result()

    # Create a storage account. To prevent a race condition, try
    # to get or create at least twice
    @tenacity.retry(stop=tenacity.stop.stop_after_attempt(2),
                    retry=tenacity.retry_if_exception_type(HttpResponseError),
                    reraise=True)
    def _get_or_create_storage_account(self):
        if self._storage_account:
            return self._storage_account
        else:
            try:
                self._storage_account = \
                    self.get_storage_account(self.storage_account)
            except ResourceNotFoundError:
                storage_account_params = {
                    'sku': Sku(name='Standard_LRS'),
                    'kind': 'storage',
                    'location': self.region_name,
                }
                try:
                    self._storage_account = \
                        self.create_storage_account(self.storage_account,
                                                    storage_account_params)
                except ClientAuthenticationError as auth_err:
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
                           'access-control/overview\n' % auth_err
                    raise ProviderConnectionException(mess)
                except ResourceExistsError as exists_err:
                    mess = 'The following error was ' \
                           'returned by Azure:\n%s\n\n' \
                           'Note that Storage Account names must be ' \
                           'unique across Azure (not just in your ' \
                           'subscription).\nFor more information ' \
                           'see https://docs.microsoft.com/en-us/' \
                           'azure/azure-resource-manager/resource-' \
                           'manager-storage-account-name-errors\n' \
                               % exists_err
                    raise InvalidLabelException(mess)

    def list_locations(self):
        return self.subscription_client.subscriptions. \
            list_locations(self.subscription_id)

    def list_vm_firewall(self):
        return self.network_management_client.network_security_groups. \
            list(self.resource_group)

    def create_vm_firewall(self, name, parameters):
        return self.network_management_client.network_security_groups. \
            begin_create_or_update(
                self.resource_group, name,
                NetworkSecurityGroup(**parameters)).result()

    def update_vm_firewall_tags(self, fw_id, tags):
        url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
                                             fw_id)
        name = url_params.get(VM_FIREWALL_NAME, "")
        return self.network_management_client.network_security_groups. \
            update_tags(self.resource_group, name, TagsObject(tags=tags))

    def get_vm_firewall(self, fw_id):
        url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
                                             fw_id)
        fw_name = url_params.get(VM_FIREWALL_NAME, "")
        return self.network_management_client.network_security_groups. \
            get(self.resource_group, fw_name)

    def delete_vm_firewall(self, fw_id):
        url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
                                             fw_id)
        name = url_params.get(VM_FIREWALL_NAME, "")
        self.network_management_client \
            .network_security_groups.begin_delete(self.resource_group, name).wait()

    def create_vm_firewall_rule(self, fw_id,
                                rule_name, parameters):
        url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
                                             fw_id)
        vm_firewall_name = url_params.get(VM_FIREWALL_NAME, "")
        # parameters may be either a raw dict (from VMFirewallRuleService) or
        # an existing SecurityRule model (when overriding default rules from
        # the firewall.default_security_rules list).
        rule = (parameters if isinstance(parameters, SecurityRule)
                else SecurityRule(**parameters))
        return self.network_management_client.security_rules. \
            begin_create_or_update(self.resource_group, vm_firewall_name,
                                   rule_name, rule).result()

    def delete_vm_firewall_rule(self, fw_rule_id, vm_firewall):
        url_params = azure_helpers.parse_url(VM_FIREWALL_RULE_RESOURCE_ID,
                                             fw_rule_id)
        name = url_params.get(VM_FIREWALL_RULE_NAME, "")
        return self.network_management_client.security_rules. \
            begin_delete(self.resource_group, vm_firewall, name).result()

    def list_containers(self, prefix=None, limit=None, marker=None):
        results = self.blob_service.list_containers(name_starts_with=prefix,
                                                    results_per_page=limit,
                                                    marker=marker)
        return results

    def create_container(self, container_name):
        try:
            return self.blob_service.create_container(container_name)
        except ResourceExistsError:
            msg = "The given Bucket name '%s' already exists. Please " \
                    "use the `get` or `find` method to get a reference to " \
                    "an existing Bucket, or specify a new Bucket name to " \
                    "create.\nNote that in Azure, Buckets are contained " \
                    "in Storage Accounts." % container_name
            raise DuplicateResourceException(msg)

    def get_container(self, container_name):
        return self.blob_service.get_container_client(container_name)

    def delete_container(self, container_name):
        self.blob_service.delete_container(container_name)

    def list_blobs(self, container_name, prefix=None, include=None):
        container_client = self.get_container(container_name)
        return container_client.list_blobs(name_starts_with=prefix, include=include)

    def upload_blob(self, container_name, blob_name, data, length=None,
                    max_concurrency=1):
        blob_client = self.blob_client(container_name, blob_name)
        blob_client.upload_blob(data=data, length=length, overwrite=True,
                                max_concurrency=max_concurrency)

    def stage_block(self, container_name, blob_name, block_id, data):
        blob_client = self.blob_client(container_name, blob_name)
        blob_client.stage_block(block_id, data)

    def commit_block_list(self, container_name, blob_name, block_ids):
        blob_client = self.blob_client(container_name, blob_name)
        block_list = [BlobBlock(block_id=block_id) for block_id in block_ids]
        blob_client.commit_block_list(block_list)

    def get_blob(self, container_name, blob_name):
        blob_client = self.blob_client(container_name, blob_name)
        return blob_client.get_blob_properties(container_name, blob_name)

    def delete_blob(self, container_name, blob_name, delete_snapshots="include"):
        blob_client = self.blob_client(container_name, blob_name)
        blob_client.delete_blob(delete_snapshots)

    def get_blob_url(self, container_name, blob_name, expiry_time, writable):
        now = datetime.datetime.utcnow()
        expiry = now + datetime.timedelta(
            seconds=expiry_time)
        blob_name = blob_name
        container_name = container_name.name
        delegation_key = self.blob_service.get_user_delegation_key(
            key_start_time=now, key_expiry_time=expiry
        )
        sas = generate_blob_sas(
            self.storage_account, container_name, blob_name,
            permission=BlobSasPermissions(read=True, write=writable), expiry=expiry,
            user_delegation_key=delegation_key
        )
        url = f"https://{self.storage_account}.blob.core.windows.net/{container_name}/{blob_name}?{sas}"
        return url

    def create_empty_disk(self, disk_name, params):
        return self.compute_client.disks.begin_create_or_update(
            self.resource_group,
            disk_name,
            Disk(**params)
        ).result()

    def create_snapshot_disk(self, disk_name, params):
        return self.compute_client.disks.begin_create_or_update(
            self.resource_group,
            disk_name,
            Disk(**params)
        ).result()

    def get_disk(self, disk_id):
        url_params = azure_helpers.parse_url(VOLUME_RESOURCE_ID,
                                             disk_id)
        disk_name = url_params.get(VOLUME_NAME, "")
        return self.compute_client.disks.get(self.resource_group, disk_name)

    def list_disks(self):
        return self.compute_client.disks. \
            list_by_resource_group(self.resource_group)

    def delete_disk(self, disk_id):
        url_params = azure_helpers.parse_url(VOLUME_RESOURCE_ID,
                                             disk_id)
        disk_name = url_params.get(VOLUME_NAME, "")
        self.compute_client.disks.begin_delete(self.resource_group, disk_name).wait()

    def update_disk_tags(self, disk_id, tags):
        url_params = azure_helpers.parse_url(VOLUME_RESOURCE_ID,
                                             disk_id)
        disk_name = url_params.get(VOLUME_NAME, "")
        return self.compute_client.disks.begin_update(
            self.resource_group,
            disk_name,
            DiskUpdate(tags=tags)
        ).wait()

    def list_snapshots(self):
        return self.compute_client.snapshots. \
            list_by_resource_group(self.resource_group)

    def get_snapshot(self, snapshot_id):
        url_params = azure_helpers.parse_url(SNAPSHOT_RESOURCE_ID,
                                             snapshot_id)
        snapshot_name = url_params.get(SNAPSHOT_NAME, "")
        return self.compute_client.snapshots.get(self.resource_group,
                                                 snapshot_name)

    def create_snapshot(self, snapshot_name, volume, tags):
        snapshot = self.compute_client.snapshots.begin_create_or_update(
            self.resource_group,
            snapshot_name,
            Snapshot(
                location=volume.location,
                creation_data=CreationData(
                    create_option='Copy',
                    source_uri=volume.id
                ),
                tags=tags
            )
        ).result()

        self.update_snapshot_tags(snapshot.id, tags)
        return snapshot

    def delete_snapshot(self, snapshot_id):
        url_params = azure_helpers.parse_url(SNAPSHOT_RESOURCE_ID,
                                             snapshot_id)
        snapshot_name = url_params.get(SNAPSHOT_NAME, "")
        self.compute_client.snapshots.begin_delete(self.resource_group,
                                                   snapshot_name).wait()

    def update_snapshot_tags(self, snapshot_id, tags):
        url_params = azure_helpers.parse_url(SNAPSHOT_RESOURCE_ID,
                                             snapshot_id)
        snapshot_name = url_params.get(SNAPSHOT_NAME, "")
        return self.compute_client.snapshots.begin_update(
            self.resource_group,
            snapshot_name,
            SnapshotUpdate(tags=tags)
        ).wait()

    def is_gallery_image(self, image_id):
        url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
                                             image_id)
        # If it is a gallery image, it will always have an offer
        return 'offer' in url_params

    def create_image(self, name, params):
        return self.compute_client.images. \
            begin_create_or_update(
                self.resource_group, name, Image(**params)).result()

    def delete_image(self, image_id):
        url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
                                             image_id)
        if not self.is_gallery_image(image_id):
            name = url_params.get(IMAGE_NAME, "")
            self.compute_client.images.begin_delete(self.resource_group, name).wait()

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
            name = url_params.get(IMAGE_NAME, "")
            return self.compute_client.images.get(self.resource_group, name)

    def update_image_tags(self, image_id, tags):
        url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
                                             image_id)
        if self.is_gallery_image(image_id):
            return True
        else:
            name = url_params.get(IMAGE_NAME, "")
            return self.compute_client.images.begin_update(
                self.resource_group, name,
                ImageUpdate(tags=tags)).result()

    def list_vm_types(self):
        return self.compute_client.virtual_machine_sizes. \
            list(self.region_name)

    def list_networks(self):
        return self.network_management_client.virtual_networks.list(
            self.networking_resource_group)

    def get_network(self, network_id):
        url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID,
                                             network_id)
        network_name = url_params.get(NETWORK_NAME, "")
        return self.network_management_client.virtual_networks.get(
            self.networking_resource_group, network_name)

    def create_network(self, name, params):
        return self.network_management_client.virtual_networks. \
            begin_create_or_update(
                self.networking_resource_group, name,
                parameters=VirtualNetwork(**params)).result()

    def delete_network(self, network_id):
        url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
        network_name = url_params.get(NETWORK_NAME, "")
        return self.network_management_client.virtual_networks. \
            begin_delete(self.networking_resource_group, network_name).wait()

    def update_network_tags(self, network_id, tags):
        url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
        network_name = url_params.get(NETWORK_NAME, "")
        return self.network_management_client.virtual_networks. \
            update_tags(self.networking_resource_group, network_name,
                        TagsObject(tags=tags))

    def get_network_id_for_subnet(self, subnet_id):
        url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID, subnet_id)
        network_id = NETWORK_RESOURCE_ID[0]
        for key, val in url_params.items():
            network_id = network_id.replace("{" + key + "}", val)
        return network_id

    def list_subnets(self, network_id):
        url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
        network_name = url_params.get(NETWORK_NAME, "")
        return self.network_management_client.subnets. \
            list(self.networking_resource_group, network_name)

    def get_subnet(self, subnet_id):
        url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
                                             subnet_id)
        network_name = url_params.get(NETWORK_NAME, "")
        subnet_name = url_params.get(SUBNET_NAME, "")
        return self.network_management_client.subnets. \
            get(self.networking_resource_group, network_name, subnet_name)

    def create_subnet(self, network_id, subnet_name, params):
        url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
        network_name = url_params.get(NETWORK_NAME, "")
        result_create = self.network_management_client \
            .subnets.begin_create_or_update(
                self.networking_resource_group,
                network_name,
                subnet_name,
                Subnet(**params)
            )
        subnet_info = result_create.result()

        return subnet_info

    def __if_subnet_in_use(e):
        # return True if the CloudError exception is due to subnet being in use
        if isinstance(e, HttpResponseError):
            if "InUseSubnetCannotBeDeleted" in e.message:
                return True
        return False

    @tenacity.retry(stop=tenacity.stop.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception(__if_subnet_in_use),
                    wait=tenacity.wait.wait_fixed(5),
                    reraise=True)
    def delete_subnet(self, subnet_id):
        url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
                                             subnet_id)
        network_name = url_params.get(NETWORK_NAME, "")
        subnet_name = url_params.get(SUBNET_NAME, "")

        try:
            result_delete = self.network_management_client \
                .subnets.begin_delete(
                    self.networking_resource_group,
                    network_name,
                    subnet_name
                )
            result_delete.wait()
        except HttpResponseError as cloud_error:
            log.exception(cloud_error.message)
            raise cloud_error

    def create_floating_ip(self, public_ip_name, public_ip_parameters):
        return self.network_management_client.public_ip_addresses. \
            begin_create_or_update(
                self.networking_resource_group,
                public_ip_name,
                PublicIPAddress(**public_ip_parameters)).result()

    def get_floating_ip(self, public_ip_id):
        url_params = azure_helpers.parse_url(PUBLIC_IP_RESOURCE_ID,
                                             public_ip_id)
        public_ip_name = url_params.get(PUBLIC_IP_NAME, "")
        return self.network_management_client. \
            public_ip_addresses.get(self.networking_resource_group, public_ip_name)

    def delete_floating_ip(self, public_ip_id):
        url_params = azure_helpers.parse_url(PUBLIC_IP_RESOURCE_ID,
                                             public_ip_id)
        public_ip_name = url_params.get(PUBLIC_IP_NAME, "")
        self.network_management_client. \
            public_ip_addresses.begin_delete(self.networking_resource_group,
                                             public_ip_name).wait()

    def update_fip_tags(self, fip_id, tags):
        url_params = azure_helpers.parse_url(PUBLIC_IP_RESOURCE_ID,
                                             fip_id)
        fip_name = url_params.get(PUBLIC_IP_NAME, "")
        self.network_management_client.public_ip_addresses. \
            update_tags(self.networking_resource_group, fip_name,
                        TagsObject(tags=tags))

    def list_floating_ips(self):
        return self.network_management_client.public_ip_addresses.list(
            self.networking_resource_group)

    def list_vm(self):
        return self.compute_client.virtual_machines.list(
            self.resource_group
        )

    def restart_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME, "")
        return self.compute_client.virtual_machines.begin_restart(
            self.resource_group, vm_name).wait()

    def stop_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME, "")
        self.compute_client.virtual_machines. \
            begin_power_off(self.resource_group, vm_name).wait()

    def delete_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME, "")
        return self.compute_client.virtual_machines.begin_delete(
            self.resource_group, vm_name).wait()

    def get_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME, "")
        return self.compute_client.virtual_machines.get(
            self.resource_group,
            vm_name,
            expand='instanceView'
        )

    def create_vm(self, vm_name, params):
        return self.compute_client.virtual_machines. \
            begin_create_or_update(
                self.resource_group, vm_name,
                VirtualMachine(**params)).result()

    def update_vm(self, vm_id, params):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME, "")
        return self.compute_client.virtual_machines. \
            begin_create_or_update(
                self.resource_group, vm_name,
                VirtualMachine(**params)).wait()

    def deallocate_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME, "")
        self.compute_client. \
            virtual_machines.begin_deallocate(self.resource_group, vm_name).wait()

    def generalize_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME, "")
        self.compute_client.virtual_machines. \
            generalize(self.resource_group, vm_name)

    def start_vm(self, vm_id):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME, "")
        self.compute_client.virtual_machines. \
            begin_start(self.resource_group, vm_name).wait()

    def update_vm_tags(self, vm_id, tags):
        url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
                                             vm_id)
        vm_name = url_params.get(VM_NAME, "")
        self.compute_client.virtual_machines.begin_update(
            self.resource_group, vm_name,
            VirtualMachineUpdate(tags=tags)).result()

    def delete_nic(self, nic_id):
        nic_params = azure_helpers.\
            parse_url(NETWORK_INTERFACE_RESOURCE_ID, nic_id)
        nic_name = nic_params.get(NETWORK_INTERFACE_NAME, "")
        self.network_management_client. \
            network_interfaces.begin_delete(self.resource_group, nic_name).wait()

    def get_nic(self, nic_id):
        nic_params = azure_helpers.\
            parse_url(NETWORK_INTERFACE_RESOURCE_ID, nic_id)
        nic_name = nic_params.get(NETWORK_INTERFACE_NAME, "")
        return self.network_management_client. \
            network_interfaces.get(self.resource_group, nic_name)

    def update_nic(self, nic_id, params):
        nic_params = azure_helpers.\
            parse_url(NETWORK_INTERFACE_RESOURCE_ID, nic_id)
        nic_name = nic_params.get(NETWORK_INTERFACE_NAME, "")
        # update_nic is called with the existing NIC model (from get_nic());
        # create_nic is called with a raw dict from services.py. Accept both.
        nic = (params if isinstance(params, NetworkInterface)
               else NetworkInterface(**params))
        async_nic_creation = self.network_management_client. \
            network_interfaces.begin_create_or_update(
                self.resource_group,
                nic_name,
                nic
            )
        nic_info = async_nic_creation.result()
        return nic_info

    def create_nic(self, nic_name, params):
        return self.network_management_client. \
            network_interfaces.begin_create_or_update(
                self.resource_group,
                nic_name,
                NetworkInterface(**params)
            ).result()

    def create_public_key(self, entity):
        return self.table_service.upsert_entity(entity)

    def get_public_key(self, name):
        entities = list(self.table_service.query_entities(
            query_filter="Name eq '{0}'".format(name),
            results_per_page=1))
        return entities[0] if entities else None

    def delete_public_key(self, entity):
        self.table_service.delete_entity(
            partition_key=entity['PartitionKey'],
            row_key=entity['RowKey'])

    def list_public_keys(self, partition_key, limit=None, marker=None):
        pager = self.table_service.query_entities(
            query_filter="PartitionKey eq '{0}'".format(partition_key),
            results_per_page=limit).by_page(continuation_token=marker)
        try:
            page = next(pager)
        except StopIteration:
            return ([], None)
        items = list(page)
        return (items, pager.continuation_token)

    def delete_route_table(self, route_table_name):
        self.network_management_client. \
            route_tables.begin_delete(self.resource_group,
                                      route_table_name).wait()

    def attach_subnet_to_route_table(self, subnet_id, route_table_id):
        url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
                                             subnet_id)
        network_name = url_params.get(NETWORK_NAME, "")
        subnet_name = url_params.get(SUBNET_NAME, "")

        subnet_info = self.network_management_client.subnets.get(
            self.resource_group,
            network_name,
            subnet_name
        )
        if subnet_info:
            subnet_info.route_table = SubResource(id=route_table_id)

            result_create = self.network_management_client. \
                subnets.begin_create_or_update(
                 self.resource_group,
                 network_name,
                 subnet_name,
                 subnet_info)  # type: ignore
            subnet_info = result_create.result()

        return subnet_info

    def detach_subnet_to_route_table(self, subnet_id, route_table_id):
        url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
                                             subnet_id)
        network_name = url_params.get(NETWORK_NAME, "")
        subnet_name = url_params.get(SUBNET_NAME, "")

        subnet_info = self.network_management_client.subnets.get(
            self.resource_group,
            network_name,
            subnet_name
        )

        if subnet_info and subnet_info.route_table.id == route_table_id:
            subnet_info.route_table = None

            result_create = self.network_management_client. \
                subnets.begin_create_or_update(
                 self.resource_group,
                 network_name,
                 subnet_name,
                 subnet_info)  # type: ignore
            subnet_info = result_create.result()

        return subnet_info

    def list_route_tables(self):
        return self.network_management_client. \
            route_tables.list(self.resource_group)

    def get_route_table(self, router_id):
        url_params = azure_helpers.parse_url(ROUTER_RESOURCE_ID,
                                             router_id)
        router_name = url_params.get(ROUTER_NAME, "")
        return self.network_management_client. \
            route_tables.get(self.resource_group, router_name)

    def create_route_table(self, route_table_name, params):
        return self.network_management_client. \
            route_tables.begin_create_or_update(
             self.resource_group,
             route_table_name, RouteTable(**params)).result()

    def update_route_table_tags(self, route_table_name, tags):
        self.network_management_client.route_tables.update_tags(
            self.resource_group, route_table_name,
            TagsObject(tags=tags))

    # DNS operations
    def get_dns_zone(self, zone_name):
        return self.dns_client.zones.get(self.resource_group, zone_name)

    def list_dns_zones(self):
        return list(self.dns_client.zones.list_by_resource_group(
            self.resource_group))

    def create_dns_zone(self, zone_name, params):
        return self.dns_client.zones.create_or_update(
            self.resource_group, zone_name, Zone(**params))

    def delete_dns_zone(self, zone_name):
        self.dns_client.zones.begin_delete(
            self.resource_group, zone_name).wait()

    def get_dns_record(self, zone_name, relative_record_name, record_type):
        return self.dns_client.record_sets.get(
            self.resource_group, zone_name, relative_record_name, record_type)

    def list_dns_records(self, zone_name):
        return list(self.dns_client.record_sets.list_all_by_dns_zone(
            self.resource_group, zone_name))

    def create_dns_record(self, zone_name, relative_record_name,
                          record_type, params):
        from azure.mgmt.dns.models import RecordSet
        return self.dns_client.record_sets.create_or_update(
            self.resource_group, zone_name, relative_record_name,
            record_type, RecordSet(**params))

    def delete_dns_record(self, zone_name, relative_record_name, record_type):
        self.dns_client.record_sets.delete(
            self.resource_group, zone_name, relative_record_name, record_type)
