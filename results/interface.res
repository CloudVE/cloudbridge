cloudbridge.test.test_interface.CloudInterfaceTestCase


Test output
 ......
----------------------------------------------------------------------
Ran 6 tests in 3.860s

OK

Wrote profile results to run_tests.py.lprof
Timer unit: 1e-06 s

Total time: 0.6384 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: __init__ at line 160

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   160                                               @profile
   161                                               def __init__(self, config):
   162         2          7.0      3.5      0.0          self._config = config
   163         2          5.0      2.5      0.0          self.subscription_id = str(config.get('azure_subscription_id'))
   164         2          1.0      0.5      0.0          self._credentials = ServicePrincipalCredentials(
   165         2          1.0      0.5      0.0              client_id=config.get('azure_client_id'),
   166         2          2.0      1.0      0.0              secret=config.get('azure_secret'),
   167         2     638344.0 319172.0    100.0              tenant=config.get('azure_tenant')
   168                                                   )
   169                                           
   170         2          6.0      3.0      0.0          self._access_token = config.get('azure_access_token')
   171         2          2.0      1.0      0.0          self._resource_client = None
   172         2          2.0      1.0      0.0          self._storage_client = None
   173         2          2.0      1.0      0.0          self._network_management_client = None
   174         2          2.0      1.0      0.0          self._subscription_client = None
   175         2          2.0      1.0      0.0          self._compute_client = None
   176         2          2.0      1.0      0.0          self._access_key_result = None
   177         2          3.0      1.5      0.0          self._block_blob_service = None
   178         2          1.0      0.5      0.0          self._table_service = None
   179         2          1.0      0.5      0.0          self._storage_account = None
   180                                           
   181         2         17.0      8.5      0.0          log.debug("azure subscription : %s", self.subscription_id)

Total time: 0.373592 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: access_key_result at line 183

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   183                                               @property
   184                                               @tenacity.retry(stop=tenacity.stop_after_attempt(5), reraise=True)
   185                                               @profile
   186                                               def access_key_result(self):
   187         1          1.0      1.0      0.0          if not self._access_key_result:
   188         1          3.0      3.0      0.0              storage_account = self.storage_account
   189                                           
   190         1     153188.0 153188.0     41.0              if self.get_storage_account(storage_account).\
   191         1          2.0      2.0      0.0                      provisioning_state.value != 'Succeeded':
   192                                                           log.debug(
   193                                                               "Storage account %s is not in Succeeded state yet. ",
   194                                                               storage_account)
   195                                                           raise WaitStateException(
   196                                                               "Waited too long for storage account: {0} to "
   197                                                               "become ready.".format(
   198                                                                   storage_account,
   199                                                                   self.get_storage_account(storage_account).
   200                                                                   provisioning_state))
   201                                           
   202         1        212.0    212.0      0.1              self._access_key_result = self.storage_client.storage_accounts. \
   203         1     220184.0 220184.0     58.9                  list_keys(self.resource_group, storage_account)
   204         1          2.0      2.0      0.0          return self._access_key_result

Total time: 4e-06 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: resource_group at line 206

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   206                                               @property
   207                                               @profile
   208                                               def resource_group(self):
   209         3          4.0      1.3    100.0          return self._config.get('azure_resource_group')

Total time: 4e-06 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: storage_account at line 211

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   211                                               @property
   212                                               @profile
   213                                               def storage_account(self):
   214         3          4.0      1.3    100.0          return self._config.get('azure_storage_account')

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: region_name at line 216

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   216                                               @property
   217                                               @profile
   218                                               def region_name(self):
   219                                                   return self._config.get('azure_region_name')

Total time: 3e-06 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: public_key_storage_table_name at line 221

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   221                                               @property
   222                                               @profile
   223                                               def public_key_storage_table_name(self):
   224         2          3.0      1.5    100.0          return self._config.get('azure_public_key_storage_table_name')

Total time: 0.006364 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: storage_client at line 226

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   226                                               @property
   227                                               @profile
   228                                               def storage_client(self):
   229         3          5.0      1.7      0.1          if not self._storage_client:
   230                                                       self._storage_client = \
   231         1          1.0      1.0      0.0                  StorageManagementClient(self._credentials,
   232         1       6354.0   6354.0     99.8                                          self.subscription_id)
   233         3          4.0      1.3      0.1          return self._storage_client

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: subscription_client at line 235

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   235                                               @property
   236                                               @profile
   237                                               def subscription_client(self):
   238                                                   if not self._subscription_client:
   239                                                       self._subscription_client = SubscriptionClient(self._credentials)
   240                                                   return self._subscription_client

Total time: 0.025636 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: resource_client at line 242

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   242                                               @property
   243                                               @profile
   244                                               def resource_client(self):
   245         3          8.0      2.7      0.0          if not self._resource_client:
   246                                                       self._resource_client = \
   247         2          2.0      1.0      0.0                  ResourceManagementClient(self._credentials,
   248         2      25619.0  12809.5     99.9                                           self.subscription_id)
   249         3          7.0      2.3      0.0          return self._resource_client

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: compute_client at line 251

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   251                                               @property
   252                                               @profile
   253                                               def compute_client(self):
   254                                                   if not self._compute_client:
   255                                                       self._compute_client = \
   256                                                           ComputeManagementClient(self._credentials,
   257                                                                                   self.subscription_id)
   258                                                   return self._compute_client

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: network_management_client at line 260

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   260                                               @property
   261                                               @profile
   262                                               def network_management_client(self):
   263                                                   if not self._network_management_client:
   264                                                       self._network_management_client = NetworkManagementClient(
   265                                                           self._credentials, self.subscription_id)
   266                                                   return self._network_management_client

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: blob_service at line 268

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   268                                               @property
   269                                               @profile
   270                                               def blob_service(self):
   271                                                   self._get_or_create_storage_account()
   272                                                   if not self._block_blob_service:
   273                                                       if self._access_token:
   274                                                           token_credential = TokenCredential(self._access_token)
   275                                                           self._block_blob_service = BlockBlobService(
   276                                                               account_name=self.storage_account,
   277                                                               token_credential=token_credential)
   278                                                       else:
   279                                                           self._block_blob_service = BlockBlobService(
   280                                                               account_name=self.storage_account,
   281                                                               account_key=self.access_key_result.keys[0].value)
   282                                                   return self._block_blob_service

Total time: 1.07638 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: table_service at line 284

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   284                                               @property
   285                                               @profile
   286                                               def table_service(self):
   287         1     538972.0 538972.0     50.1          self._get_or_create_storage_account()
   288         1          1.0      1.0      0.0          if not self._table_service:
   289         1          4.0      4.0      0.0              self._table_service = TableService(
   290         1          7.0      7.0      0.0                  self.storage_account,
   291         1     374051.0 374051.0     34.8                  self.access_key_result.keys[0].value)
   292         1          1.0      1.0      0.0          if not self._table_service. \
   293         1     163345.0 163345.0     15.2                  exists(table_name=self.public_key_storage_table_name):
   294                                                       self._table_service.create_table(
   295                                                           self.public_key_storage_table_name)
   296         1          2.0      2.0      0.0          return self._table_service

Total time: 0.706347 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_resource_group at line 298

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   298                                               @profile
   299                                               def get_resource_group(self, name):
   300         3     706347.0 235449.0    100.0          return self.resource_client.resource_groups.get(name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_resource_group at line 302

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   302                                               @profile
   303                                               def create_resource_group(self, name, parameters):
   304                                                   return self.resource_client.resource_groups. \
   305                                                       create_or_update(name, parameters)

Total time: 0.691958 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_storage_account at line 307

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   307                                               @profile
   308                                               def get_storage_account(self, storage_account):
   309         2     261869.0 130934.5     37.8          return self.storage_client.storage_accounts. \
   310         2     430089.0 215044.5     62.2              get_properties(self.resource_group, storage_account)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_storage_account at line 312

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   312                                               @profile
   313                                               def create_storage_account(self, name, params):
   314                                                   return self.storage_client.storage_accounts. \
   315                                                       create(self.resource_group, name.lower(), params).result()

Total time: 0.538814 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: _get_or_create_storage_account at line 319

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   319                                               @tenacity.retry(stop=tenacity.stop_after_attempt(2),
   320                                                               retry=tenacity.retry_if_exception_type(CloudError),
   321                                                               reraise=True)
   322                                               @profile
   323                                               def _get_or_create_storage_account(self):
   324         1          1.0      1.0      0.0          if self._storage_account:
   325                                                       return self._storage_account
   326                                                   else:
   327         1          1.0      1.0      0.0              try:
   328                                                           self._storage_account = \
   329         1     538812.0 538812.0    100.0                      self.get_storage_account(self.storage_account)
   330                                                       except CloudError as cloud_error:
   331                                                           if cloud_error.error.error == "ResourceNotFound":
   332                                                               storage_account_params = {
   333                                                                   'sku': {
   334                                                                       'name': 'Standard_LRS'
   335                                                                   },
   336                                                                   'kind': 'storage',
   337                                                                   'location': self.region_name,
   338                                                               }
   339                                                               try:
   340                                                                   self._storage_account = \
   341                                                                       self.create_storage_account(self.storage_account,
   342                                                                                                   storage_account_params)
   343                                                               except CloudError as cloud_error2:  # pragma: no cover
   344                                                                   if cloud_error2.error.error == "AuthorizationFailed":
   345                                                                       mess = 'The following error was returned by ' \
   346                                                                              'Azure:\n%s\n\nThis is likely because the' \
   347                                                                              ' Role associated with the provided ' \
   348                                                                              'credentials does not allow for Storage ' \
   349                                                                              'Account creation.\nA Storage Account is ' \
   350                                                                              'necessary in order to perform the ' \
   351                                                                              'desired operation. You must either ' \
   352                                                                              'provide an existing Storage Account name' \
   353                                                                              ' as part of the configuration, or ' \
   354                                                                              'elevate the associated Role.\nFor more ' \
   355                                                                              'information on roles, see: https://docs.' \
   356                                                                              'microsoft.com/en-us/azure/role-based-' \
   357                                                                              'access-control/overview\n' % cloud_error2
   358                                                                       raise ProviderConnectionException(mess)
   359                                           
   360                                                                   elif cloud_error2.error.error == \
   361                                                                           "StorageAccountAlreadyTaken":
   362                                                                       mess = 'The following error was ' \
   363                                                                              'returned by Azure:\n%s\n\n' \
   364                                                                              'Note that Storage Account names must be ' \
   365                                                                              'unique across Azure (not just in your ' \
   366                                                                              'subscription).\nFor more information ' \
   367                                                                              'see https://docs.microsoft.com/en-us/' \
   368                                                                              'azure/azure-resource-manager/resource-' \
   369                                                                              'manager-storage-account-name-errors\n' \
   370                                                                              % cloud_error2
   371                                                                       raise InvalidLabelException(mess)
   372                                                                   else:
   373                                                                       raise cloud_error2
   374                                                           else:
   375                                                               raise cloud_error

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_locations at line 377

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   377                                               @profile
   378                                               def list_locations(self):
   379                                                   return self.subscription_client.subscriptions. \
   380                                                       list_locations(self.subscription_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_vm_firewall at line 382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   382                                               @profile
   383                                               def list_vm_firewall(self):
   384                                                   return self.network_management_client.network_security_groups. \
   385                                                       list(self.resource_group)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_vm_firewall at line 387

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   387                                               @profile
   388                                               def create_vm_firewall(self, name, parameters):
   389                                                   return self.network_management_client.network_security_groups. \
   390                                                       create_or_update(self.resource_group, name,
   391                                                                        parameters).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: update_vm_firewall_tags at line 393

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   393                                               @profile
   394                                               def update_vm_firewall_tags(self, fw_id, tags):
   395                                                   url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
   396                                                                                        fw_id)
   397                                                   name = url_params.get(VM_FIREWALL_NAME)
   398                                                   return self.network_management_client.network_security_groups. \
   399                                                       create_or_update(self.resource_group, name,
   400                                                                        {'tags': tags,
   401                                                                         'location': self.region_name}).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_vm_firewall at line 403

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   403                                               @profile
   404                                               def get_vm_firewall(self, fw_id):
   405                                                   url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
   406                                                                                        fw_id)
   407                                                   fw_name = url_params.get(VM_FIREWALL_NAME)
   408                                                   return self.network_management_client.network_security_groups. \
   409                                                       get(self.resource_group, fw_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_vm_firewall at line 411

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   411                                               @profile
   412                                               def delete_vm_firewall(self, fw_id):
   413                                                   url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
   414                                                                                        fw_id)
   415                                                   name = url_params.get(VM_FIREWALL_NAME)
   416                                                   self.network_management_client \
   417                                                       .network_security_groups.delete(self.resource_group, name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_vm_firewall_rule at line 419

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   419                                               @profile
   420                                               def create_vm_firewall_rule(self, fw_id,
   421                                                                           rule_name, parameters):
   422                                                   url_params = azure_helpers.parse_url(VM_FIREWALL_RESOURCE_ID,
   423                                                                                        fw_id)
   424                                                   vm_firewall_name = url_params.get(VM_FIREWALL_NAME)
   425                                                   return self.network_management_client.security_rules. \
   426                                                       create_or_update(self.resource_group, vm_firewall_name,
   427                                                                        rule_name, parameters).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_vm_firewall_rule at line 429

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   429                                               @profile
   430                                               def delete_vm_firewall_rule(self, fw_rule_id, vm_firewall):
   431                                                   url_params = azure_helpers.parse_url(VM_FIREWALL_RULE_RESOURCE_ID,
   432                                                                                        fw_rule_id)
   433                                                   name = url_params.get(VM_FIREWALL_RULE_NAME)
   434                                                   return self.network_management_client.security_rules. \
   435                                                       delete(self.resource_group, vm_firewall, name).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_containers at line 437

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   437                                               @profile
   438                                               def list_containers(self, prefix=None, limit=None, marker=None):
   439                                                   results = self.blob_service.list_containers(prefix=prefix,
   440                                                                                               num_results=limit,
   441                                                                                               marker=marker)
   442                                                   return (results.items, results.next_marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_container at line 444

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   444                                               @profile
   445                                               def create_container(self, container_name):
   446                                                   try:
   447                                                       self.blob_service.create_container(container_name,
   448                                                                                          fail_on_exist=True)
   449                                                   except AzureConflictHttpError as cloud_error:
   450                                                       if cloud_error.error_code == "ContainerAlreadyExists":
   451                                                           msg = "The given Bucket name '%s' already exists. Please " \
   452                                                                 "use the `get` or `find` method to get a reference to " \
   453                                                                 "an existing Bucket, or specify a new Bucket name to " \
   454                                                                 "create.\nNote that in Azure, Buckets are contained " \
   455                                                                 "in Storage Accounts." % container_name
   456                                                           raise DuplicateResourceException(msg)
   457                                           
   458                                                   return self.blob_service.get_container_properties(container_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_container at line 460

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   460                                               @profile
   461                                               def get_container(self, container_name):
   462                                                   return self.blob_service.get_container_properties(container_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_container at line 464

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   464                                               @profile
   465                                               def delete_container(self, container_name):
   466                                                   self.blob_service.delete_container(container_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_blobs at line 468

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   468                                               @profile
   469                                               def list_blobs(self, container_name, prefix=None):
   470                                                   return self.blob_service.list_blobs(container_name, prefix=prefix)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_blob at line 472

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   472                                               @profile
   473                                               def get_blob(self, container_name, blob_name):
   474                                                   return self.blob_service.get_blob_properties(container_name, blob_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_blob_from_text at line 476

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   476                                               @profile
   477                                               def create_blob_from_text(self, container_name, blob_name, text):
   478                                                   self.blob_service.create_blob_from_text(container_name,
   479                                                                                           blob_name, text)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_blob_from_file at line 481

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   481                                               @profile
   482                                               def create_blob_from_file(self, container_name, blob_name, file_path):
   483                                                   self.blob_service.create_blob_from_path(container_name,
   484                                                                                           blob_name, file_path)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_blob at line 486

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   486                                               @profile
   487                                               def delete_blob(self, container_name, blob_name):
   488                                                   self.blob_service.delete_blob(container_name, blob_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_blob_url at line 490

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   490                                               @profile
   491                                               def get_blob_url(self, container_name, blob_name, expiry_time):
   492                                                   expiry_date = datetime.datetime.utcnow() + datetime.timedelta(
   493                                                       seconds=expiry_time)
   494                                                   sas = self.blob_service.generate_blob_shared_access_signature(
   495                                                       container_name, blob_name, permission=BlobPermissions.READ,
   496                                                       expiry=expiry_date)
   497                                                   return self.blob_service.make_blob_url(container_name, blob_name,
   498                                                                                          sas_token=sas)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_blob_content at line 500

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   500                                               @profile
   501                                               def get_blob_content(self, container_name, blob_name):
   502                                                   out_stream = BytesIO()
   503                                                   self.blob_service.get_blob_to_stream(container_name,
   504                                                                                        blob_name, out_stream)
   505                                                   return out_stream

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_empty_disk at line 507

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   507                                               @profile
   508                                               def create_empty_disk(self, disk_name, params):
   509                                                   return self.compute_client.disks.create_or_update(
   510                                                       self.resource_group,
   511                                                       disk_name,
   512                                                       params
   513                                                   ).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_snapshot_disk at line 515

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   515                                               @profile
   516                                               def create_snapshot_disk(self, disk_name, params):
   517                                                   return self.compute_client.disks.create_or_update(
   518                                                       self.resource_group,
   519                                                       disk_name,
   520                                                       params
   521                                                   ).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_disk at line 523

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   523                                               @profile
   524                                               def get_disk(self, disk_id):
   525                                                   url_params = azure_helpers.parse_url(VOLUME_RESOURCE_ID,
   526                                                                                        disk_id)
   527                                                   disk_name = url_params.get(VOLUME_NAME)
   528                                                   return self.compute_client.disks.get(self.resource_group, disk_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_disks at line 530

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   530                                               @profile
   531                                               def list_disks(self):
   532                                                   return self.compute_client.disks. \
   533                                                       list_by_resource_group(self.resource_group)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_disk at line 535

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   535                                               @profile
   536                                               def delete_disk(self, disk_id):
   537                                                   url_params = azure_helpers.parse_url(VOLUME_RESOURCE_ID,
   538                                                                                        disk_id)
   539                                                   disk_name = url_params.get(VOLUME_NAME)
   540                                                   self.compute_client.disks.delete(self.resource_group, disk_name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: update_disk_tags at line 542

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   542                                               @profile
   543                                               def update_disk_tags(self, disk_id, tags):
   544                                                   url_params = azure_helpers.parse_url(VOLUME_RESOURCE_ID,
   545                                                                                        disk_id)
   546                                                   disk_name = url_params.get(VOLUME_NAME)
   547                                                   return self.compute_client.disks.update(
   548                                                       self.resource_group,
   549                                                       disk_name,
   550                                                       {'tags': tags},
   551                                                       raw=True
   552                                                   )

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_snapshots at line 554

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   554                                               @profile
   555                                               def list_snapshots(self):
   556                                                   return self.compute_client.snapshots. \
   557                                                       list_by_resource_group(self.resource_group)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_snapshot at line 559

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   559                                               @profile
   560                                               def get_snapshot(self, snapshot_id):
   561                                                   url_params = azure_helpers.parse_url(SNAPSHOT_RESOURCE_ID,
   562                                                                                        snapshot_id)
   563                                                   snapshot_name = url_params.get(SNAPSHOT_NAME)
   564                                                   return self.compute_client.snapshots.get(self.resource_group,
   565                                                                                            snapshot_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_snapshot at line 567

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   567                                               @profile
   568                                               def create_snapshot(self, snapshot_name, params):
   569                                                   return self.compute_client.snapshots.create_or_update(
   570                                                       self.resource_group,
   571                                                       snapshot_name,
   572                                                       params
   573                                                   ).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_snapshot at line 575

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   575                                               @profile
   576                                               def delete_snapshot(self, snapshot_id):
   577                                                   url_params = azure_helpers.parse_url(SNAPSHOT_RESOURCE_ID,
   578                                                                                        snapshot_id)
   579                                                   snapshot_name = url_params.get(SNAPSHOT_NAME)
   580                                                   self.compute_client.snapshots.delete(self.resource_group,
   581                                                                                        snapshot_name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: update_snapshot_tags at line 583

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   583                                               @profile
   584                                               def update_snapshot_tags(self, snapshot_id, tags):
   585                                                   url_params = azure_helpers.parse_url(SNAPSHOT_RESOURCE_ID,
   586                                                                                        snapshot_id)
   587                                                   snapshot_name = url_params.get(SNAPSHOT_NAME)
   588                                                   return self.compute_client.snapshots.update(
   589                                                       self.resource_group,
   590                                                       snapshot_name,
   591                                                       {'tags': tags},
   592                                                       raw=True
   593                                                   )

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: is_gallery_image at line 595

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   595                                               @profile
   596                                               def is_gallery_image(self, image_id):
   597                                                   url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
   598                                                                                        image_id)
   599                                                   # If it is a gallery image, it will always have an offer
   600                                                   return 'offer' in url_params

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_image at line 602

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   602                                               @profile
   603                                               def create_image(self, name, params):
   604                                                   return self.compute_client.images. \
   605                                                       create_or_update(self.resource_group, name,
   606                                                                        params).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_image at line 608

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   608                                               @profile
   609                                               def delete_image(self, image_id):
   610                                                   url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
   611                                                                                        image_id)
   612                                                   if not self.is_gallery_image(image_id):
   613                                                       name = url_params.get(IMAGE_NAME)
   614                                                       self.compute_client.images.delete(self.resource_group, name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_images at line 616

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   616                                               @profile
   617                                               def list_images(self):
   618                                                   azure_images = list(self.compute_client.images.
   619                                                                       list_by_resource_group(self.resource_group))
   620                                                   return azure_images

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_gallery_refs at line 622

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   622                                               @profile
   623                                               def list_gallery_refs(self):
   624                                                   return gallery_image_references

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_image at line 626

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   626                                               @profile
   627                                               def get_image(self, image_id):
   628                                                   url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
   629                                                                                        image_id)
   630                                                   if self.is_gallery_image(image_id):
   631                                                       return GalleryImageReference(publisher=url_params['publisher'],
   632                                                                                    offer=url_params['offer'],
   633                                                                                    sku=url_params['sku'],
   634                                                                                    version=url_params['version'])
   635                                                   else:
   636                                                       name = url_params.get(IMAGE_NAME)
   637                                                       return self.compute_client.images.get(self.resource_group, name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: update_image_tags at line 639

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   639                                               @profile
   640                                               def update_image_tags(self, image_id, tags):
   641                                                   url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
   642                                                                                        image_id)
   643                                                   if self.is_gallery_image(image_id):
   644                                                       return True
   645                                                   else:
   646                                                       name = url_params.get(IMAGE_NAME)
   647                                                       return self.compute_client.images. \
   648                                                           create_or_update(self.resource_group, name,
   649                                                                            {
   650                                                                                'tags': tags,
   651                                                                                'location': self.region_name
   652                                                                            }).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_vm_types at line 654

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   654                                               @profile
   655                                               def list_vm_types(self):
   656                                                   return self.compute_client.virtual_machine_sizes. \
   657                                                       list(self.region_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_networks at line 659

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   659                                               @profile
   660                                               def list_networks(self):
   661                                                   return self.network_management_client.virtual_networks.list(
   662                                                       self.resource_group)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_network at line 664

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   664                                               @profile
   665                                               def get_network(self, network_id):
   666                                                   url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID,
   667                                                                                        network_id)
   668                                                   network_name = url_params.get(NETWORK_NAME)
   669                                                   return self.network_management_client.virtual_networks.get(
   670                                                       self.resource_group, network_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_network at line 672

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   672                                               @profile
   673                                               def create_network(self, name, params):
   674                                                   return self.network_management_client.virtual_networks. \
   675                                                       create_or_update(self.resource_group,
   676                                                                        name,
   677                                                                        parameters=params).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_network at line 679

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   679                                               @profile
   680                                               def delete_network(self, network_id):
   681                                                   url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
   682                                                   network_name = url_params.get(NETWORK_NAME)
   683                                                   return self.network_management_client.virtual_networks. \
   684                                                       delete(self.resource_group, network_name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: update_network_tags at line 686

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   686                                               @profile
   687                                               def update_network_tags(self, network_id, tags):
   688                                                   url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
   689                                                   network_name = url_params.get(NETWORK_NAME)
   690                                                   return self.network_management_client.virtual_networks. \
   691                                                       create_or_update(self.resource_group,
   692                                                                        network_name, tags).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_network_id_for_subnet at line 694

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   694                                               @profile
   695                                               def get_network_id_for_subnet(self, subnet_id):
   696                                                   url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID, subnet_id)
   697                                                   network_id = NETWORK_RESOURCE_ID[0]
   698                                                   for key, val in url_params.items():
   699                                                       network_id = network_id.replace("{" + key + "}", val)
   700                                                   return network_id

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_subnets at line 702

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   702                                               @profile
   703                                               def list_subnets(self, network_id):
   704                                                   url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
   705                                                   network_name = url_params.get(NETWORK_NAME)
   706                                                   return self.network_management_client.subnets. \
   707                                                       list(self.resource_group, network_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_subnet at line 709

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   709                                               @profile
   710                                               def get_subnet(self, subnet_id):
   711                                                   url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
   712                                                                                        subnet_id)
   713                                                   network_name = url_params.get(NETWORK_NAME)
   714                                                   subnet_name = url_params.get(SUBNET_NAME)
   715                                                   return self.network_management_client.subnets. \
   716                                                       get(self.resource_group, network_name, subnet_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_subnet at line 718

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   718                                               @profile
   719                                               def create_subnet(self, network_id, subnet_name, params):
   720                                                   url_params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
   721                                                   network_name = url_params.get(NETWORK_NAME)
   722                                                   result_create = self.network_management_client \
   723                                                       .subnets.create_or_update(
   724                                                           self.resource_group,
   725                                                           network_name,
   726                                                           subnet_name,
   727                                                           params
   728                                                       )
   729                                                   subnet_info = result_create.result()
   730                                           
   731                                                   return subnet_info

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: __if_subnet_in_use at line 733

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   733                                               @profile
   734                                               def __if_subnet_in_use(e):
   735                                                   # return True if the CloudError exception is due to subnet being in use
   736                                                   if isinstance(e, CloudError):
   737                                                       if e.error.error == "InUseSubnetCannotBeDeleted":
   738                                                           return True
   739                                                   return False

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_subnet at line 741

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   741                                               @tenacity.retry(stop=tenacity.stop_after_attempt(5),
   742                                                               retry=tenacity.retry_if_exception(__if_subnet_in_use),
   743                                                               wait=tenacity.wait_fixed(5),
   744                                                               reraise=True)
   745                                               @profile
   746                                               def delete_subnet(self, subnet_id):
   747                                                   url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
   748                                                                                        subnet_id)
   749                                                   network_name = url_params.get(NETWORK_NAME)
   750                                                   subnet_name = url_params.get(SUBNET_NAME)
   751                                           
   752                                                   try:
   753                                                       result_delete = self.network_management_client \
   754                                                           .subnets.delete(
   755                                                               self.resource_group,
   756                                                               network_name,
   757                                                               subnet_name
   758                                                           )
   759                                                       result_delete.wait()
   760                                                   except CloudError as cloud_error:
   761                                                       log.exception(cloud_error.message)
   762                                                       raise cloud_error

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_floating_ip at line 764

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   764                                               @profile
   765                                               def create_floating_ip(self, public_ip_name, public_ip_parameters):
   766                                                   return self.network_management_client.public_ip_addresses. \
   767                                                       create_or_update(self.resource_group,
   768                                                                        public_ip_name,
   769                                                                        public_ip_parameters).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_floating_ip at line 771

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   771                                               @profile
   772                                               def get_floating_ip(self, public_ip_id):
   773                                                   url_params = azure_helpers.parse_url(PUBLIC_IP_RESOURCE_ID,
   774                                                                                        public_ip_id)
   775                                                   public_ip_name = url_params.get(PUBLIC_IP_NAME)
   776                                                   return self.network_management_client. \
   777                                                       public_ip_addresses.get(self.resource_group, public_ip_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_floating_ip at line 779

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   779                                               @profile
   780                                               def delete_floating_ip(self, public_ip_id):
   781                                                   url_params = azure_helpers.parse_url(PUBLIC_IP_RESOURCE_ID,
   782                                                                                        public_ip_id)
   783                                                   public_ip_name = url_params.get(PUBLIC_IP_NAME)
   784                                                   self.network_management_client. \
   785                                                       public_ip_addresses.delete(self.resource_group,
   786                                                                                  public_ip_name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: update_fip_tags at line 788

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   788                                               @profile
   789                                               def update_fip_tags(self, fip_id, tags):
   790                                                   url_params = azure_helpers.parse_url(PUBLIC_IP_RESOURCE_ID,
   791                                                                                        fip_id)
   792                                                   fip_name = url_params.get(PUBLIC_IP_NAME)
   793                                                   self.network_management_client.public_ip_addresses. \
   794                                                       create_or_update(self.resource_group,
   795                                                                        fip_name, tags).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_floating_ips at line 797

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   797                                               @profile
   798                                               def list_floating_ips(self):
   799                                                   return self.network_management_client.public_ip_addresses.list(
   800                                                       self.resource_group)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_vm at line 802

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   802                                               @profile
   803                                               def list_vm(self):
   804                                                   return self.compute_client.virtual_machines.list(
   805                                                       self.resource_group
   806                                                   )

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: restart_vm at line 808

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   808                                               @profile
   809                                               def restart_vm(self, vm_id):
   810                                                   url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
   811                                                                                        vm_id)
   812                                                   vm_name = url_params.get(VM_NAME)
   813                                                   return self.compute_client.virtual_machines.restart(
   814                                                       self.resource_group, vm_name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_vm at line 816

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   816                                               @profile
   817                                               def delete_vm(self, vm_id):
   818                                                   url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
   819                                                                                        vm_id)
   820                                                   vm_name = url_params.get(VM_NAME)
   821                                                   return self.compute_client.virtual_machines.delete(
   822                                                       self.resource_group, vm_name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_vm at line 824

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   824                                               @profile
   825                                               def get_vm(self, vm_id):
   826                                                   url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
   827                                                                                        vm_id)
   828                                                   vm_name = url_params.get(VM_NAME)
   829                                                   return self.compute_client.virtual_machines.get(
   830                                                       self.resource_group,
   831                                                       vm_name,
   832                                                       expand='instanceView'
   833                                                   )

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_vm at line 835

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   835                                               @profile
   836                                               def create_vm(self, vm_name, params):
   837                                                   return self.compute_client.virtual_machines. \
   838                                                       create_or_update(self.resource_group,
   839                                                                        vm_name, params).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: update_vm at line 841

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   841                                               @profile
   842                                               def update_vm(self, vm_id, params):
   843                                                   url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
   844                                                                                        vm_id)
   845                                                   vm_name = url_params.get(VM_NAME)
   846                                                   return self.compute_client.virtual_machines. \
   847                                                       create_or_update(self.resource_group,
   848                                                                        vm_name, params, raw=True)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: deallocate_vm at line 850

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   850                                               @profile
   851                                               def deallocate_vm(self, vm_id):
   852                                                   url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
   853                                                                                        vm_id)
   854                                                   vm_name = url_params.get(VM_NAME)
   855                                                   self.compute_client. \
   856                                                       virtual_machines.deallocate(self.resource_group,
   857                                                                                   vm_name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: generalize_vm at line 859

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   859                                               @profile
   860                                               def generalize_vm(self, vm_id):
   861                                                   url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
   862                                                                                        vm_id)
   863                                                   vm_name = url_params.get(VM_NAME)
   864                                                   self.compute_client.virtual_machines. \
   865                                                       generalize(self.resource_group, vm_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: start_vm at line 867

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   867                                               @profile
   868                                               def start_vm(self, vm_id):
   869                                                   url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
   870                                                                                        vm_id)
   871                                                   vm_name = url_params.get(VM_NAME)
   872                                                   self.compute_client.virtual_machines. \
   873                                                       start(self.resource_group,
   874                                                             vm_name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: update_vm_tags at line 876

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   876                                               @profile
   877                                               def update_vm_tags(self, vm_id, tags):
   878                                                   url_params = azure_helpers.parse_url(VM_RESOURCE_ID,
   879                                                                                        vm_id)
   880                                                   vm_name = url_params.get(VM_NAME)
   881                                                   self.compute_client.virtual_machines. \
   882                                                       create_or_update(self.resource_group,
   883                                                                        vm_name, tags).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_nic at line 885

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   885                                               @profile
   886                                               def delete_nic(self, nic_id):
   887                                                   nic_params = azure_helpers.\
   888                                                       parse_url(NETWORK_INTERFACE_RESOURCE_ID, nic_id)
   889                                                   nic_name = nic_params.get(NETWORK_INTERFACE_NAME)
   890                                                   self.network_management_client. \
   891                                                       network_interfaces.delete(self.resource_group,
   892                                                                                 nic_name).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_nic at line 894

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   894                                               @profile
   895                                               def get_nic(self, nic_id):
   896                                                   nic_params = azure_helpers.\
   897                                                       parse_url(NETWORK_INTERFACE_RESOURCE_ID, nic_id)
   898                                                   nic_name = nic_params.get(NETWORK_INTERFACE_NAME)
   899                                                   return self.network_management_client. \
   900                                                       network_interfaces.get(self.resource_group, nic_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: update_nic at line 902

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   902                                               @profile
   903                                               def update_nic(self, nic_id, params):
   904                                                   nic_params = azure_helpers.\
   905                                                       parse_url(NETWORK_INTERFACE_RESOURCE_ID, nic_id)
   906                                                   nic_name = nic_params.get(NETWORK_INTERFACE_NAME)
   907                                                   async_nic_creation = self.network_management_client. \
   908                                                       network_interfaces.create_or_update(
   909                                                           self.resource_group,
   910                                                           nic_name,
   911                                                           params
   912                                                       )
   913                                                   nic_info = async_nic_creation.result()
   914                                                   return nic_info

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_nic at line 916

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   916                                               @profile
   917                                               def create_nic(self, nic_name, params):
   918                                                   return self.network_management_client. \
   919                                                       network_interfaces.create_or_update(
   920                                                           self.resource_group,
   921                                                           nic_name,
   922                                                           params
   923                                                       ).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_public_key at line 925

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   925                                               @profile
   926                                               def create_public_key(self, entity):
   927                                                   return self.table_service. \
   928                                                       insert_or_replace_entity(self.public_key_storage_table_name,
   929                                                                                entity)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_public_key at line 931

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   931                                               @profile
   932                                               def get_public_key(self, name):
   933                                                   entities = self.table_service. \
   934                                                       query_entities(self.public_key_storage_table_name,
   935                                                                      "Name eq '{0}'".format(name), num_results=1)
   936                                           
   937                                                   return entities.items[0] if len(entities.items) > 0 else None

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_public_key at line 939

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   939                                               @profile
   940                                               def delete_public_key(self, entity):
   941                                                   self.table_service.delete_entity(self.public_key_storage_table_name,
   942                                                                                    entity.PartitionKey, entity.RowKey)

Total time: 1.13503 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_public_keys at line 944

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   944                                               @profile
   945                                               def list_public_keys(self, partition_key, limit=None, marker=None):
   946         1    1076407.0 1076407.0     94.8          entities = self.table_service. \
   947         1          8.0      8.0      0.0              query_entities(self.public_key_storage_table_name,
   948         1          2.0      2.0      0.0                             "PartitionKey eq '{0}'".format(partition_key),
   949         1      58613.0  58613.0      5.2                             marker=marker, num_results=limit)
   950         1          2.0      2.0      0.0          return (entities.items, entities.next_marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: delete_route_table at line 952

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   952                                               @profile
   953                                               def delete_route_table(self, route_table_name):
   954                                                   self.network_management_client. \
   955                                                       route_tables.delete(self.resource_group, route_table_name
   956                                                                           ).wait()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: attach_subnet_to_route_table at line 958

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   958                                               @profile
   959                                               def attach_subnet_to_route_table(self, subnet_id, route_table_id):
   960                                                   url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
   961                                                                                        subnet_id)
   962                                                   network_name = url_params.get(NETWORK_NAME)
   963                                                   subnet_name = url_params.get(SUBNET_NAME)
   964                                           
   965                                                   subnet_info = self.network_management_client.subnets.get(
   966                                                       self.resource_group,
   967                                                       network_name,
   968                                                       subnet_name
   969                                                   )
   970                                                   if subnet_info:
   971                                                       subnet_info.route_table = {
   972                                                           'id': route_table_id
   973                                                       }
   974                                           
   975                                                       result_create = self.network_management_client. \
   976                                                           subnets.create_or_update(
   977                                                            self.resource_group,
   978                                                            network_name,
   979                                                            subnet_name,
   980                                                            subnet_info)
   981                                                       subnet_info = result_create.result()
   982                                           
   983                                                   return subnet_info

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: detach_subnet_to_route_table at line 985

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   985                                               @profile
   986                                               def detach_subnet_to_route_table(self, subnet_id, route_table_id):
   987                                                   url_params = azure_helpers.parse_url(SUBNET_RESOURCE_ID,
   988                                                                                        subnet_id)
   989                                                   network_name = url_params.get(NETWORK_NAME)
   990                                                   subnet_name = url_params.get(SUBNET_NAME)
   991                                           
   992                                                   subnet_info = self.network_management_client.subnets.get(
   993                                                       self.resource_group,
   994                                                       network_name,
   995                                                       subnet_name
   996                                                   )
   997                                           
   998                                                   if subnet_info and subnet_info.route_table.id == route_table_id:
   999                                                       subnet_info.route_table = None
  1000                                           
  1001                                                       result_create = self.network_management_client. \
  1002                                                           subnets.create_or_update(
  1003                                                            self.resource_group,
  1004                                                            network_name,
  1005                                                            subnet_name,
  1006                                                            subnet_info)
  1007                                                       subnet_info = result_create.result()
  1008                                           
  1009                                                   return subnet_info

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: list_route_tables at line 1011

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1011                                               @profile
  1012                                               def list_route_tables(self):
  1013                                                   return self.network_management_client. \
  1014                                                       route_tables.list(self.resource_group)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: get_route_table at line 1016

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1016                                               @profile
  1017                                               def get_route_table(self, router_id):
  1018                                                   url_params = azure_helpers.parse_url(ROUTER_RESOURCE_ID,
  1019                                                                                        router_id)
  1020                                                   router_name = url_params.get(ROUTER_NAME)
  1021                                                   return self.network_management_client. \
  1022                                                       route_tables.get(self.resource_group, router_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: create_route_table at line 1024

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1024                                               @profile
  1025                                               def create_route_table(self, route_table_name, params):
  1026                                                   return self.network_management_client. \
  1027                                                       route_tables.create_or_update(
  1028                                                        self.resource_group,
  1029                                                        route_table_name, params).result()

Total time: 0 s
File: /Users/alex/Desktop/work/cb-profiled/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py
Function: update_route_table_tags at line 1031

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1031                                               @profile
  1032                                               def update_route_table_tags(self, route_table_name, tags):
  1033                                                   self.network_management_client.route_tables. \
  1034                                                       create_or_update(self.resource_group,
  1035                                                                        route_table_name, tags).result()

