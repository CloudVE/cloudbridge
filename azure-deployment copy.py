'''
This script will initialize needed components and create the specified number
of instances, along with a master ssh key for all instances and a personal
ssh keypair for each instance. The public portion of the instance-specific
keypair is already added to the authorized_keys file in each instance.
The script will store all public and private portions of keys as files in a
keys/ directory, as well as create a CSV file containing all the information.

This script can be run from command-line as follows:
python3 demo-instances.py -n [num-instances]
Additional parameters include:
-s [int] : number to start at for naming instances (counting from 0 by default)
-p prefix : specify a new prefix for all components and instances
'''

from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList
from cloudbridge.cloud.interfaces import resources
import os
import subprocess
import random
import string
import time

az_config = {
    'azure_subscription_id': '9a279bc4-b3cd-4dd4-bfcc-cf410de575aa',  # Subscriptions -> Subscription ID
    'azure_tenant': 'dfb75138-3e98-4887-8263-6988a5717064',  # Azure Active Dir -> Properties -> Directory ID
    'azure_client_id': '1e84fe7d-0551-4528-960e-a056220de6e5',  # App registrations -> App -> App ID
    'azure_secret': 'zXwXnCmcjJCHwx9l6k5/LCG3MG8TMtqpJIscci1gsuU=',  # App registrations -> App -> Keys -> Value (cb-app app)
    'azure_resource_group': 'cloudbridge',
    'azure_vm_default_user': 'cbuser'
}

VM_SPECS = {
    'publisher': 'Canonical',
    'offer': 'UbuntuServer',
    'sku': '16.04.0-LTS',
    'version': 'latest',
}

prefix = 'alex-test2-'

# Ubuntu 16.04.03 @ Jetstream
image_id = 'Canonical/UbuntuServer/16.04.0-LTS/latest'

# The universal private key will be created in a file with this name
kp_name = prefix + 'masterkey'
kp_file = kp_name + '.pem'

# Connecting to provider and generating keypair for all instances
prov = CloudProviderFactory().create_provider(ProviderList.AZURE, az_config)

kp_find = prov.security.key_pairs.find(name=kp_name)
if len(kp_find) > 0:
    kp = kp_find[0]

else:
    kp = prov.security.key_pairs.create(kp_name)

    # Some software (eg: paramiko) require that RSA be specified
    key_contents = kp.material
    if 'RSA PRIVATE' not in key_contents:
        key_contents = key_contents.replace('PRIVATE KEY', 'RSA PRIVATE KEY')

    # Writing private portion of key to .pem file
    with open(kp_file, 'w') as f:
        f.write(key_contents)
    os.chmod(kp_file, 0o400)

# Getting already existing network or creating a new one
net_name = prefix + 'network'
net_find = prov.networking.networks.find(name=net_name)
if len(net_find) > 0:
    net = net_find[0]
else:
    net = prov.networking.networks.create(
        name=net_name, cidr_block='10.0.0.0/16')

# Getting already existing subnet or creating a new one
sn_name = prefix + 'subnet'
sn_find = prov.networking.subnets.find(name=sn_name)
if len(sn_find) > 0:
    sn = sn_find[0]
else:
    sn = net.create_subnet(name=sn_name, cidr_block='10.0.0.0/25')

# Getting already existing router or creating a new one
router_name = prefix + 'router'
router_find = prov.networking.routers.find(name=router_name)
if len(router_find) > 0:
    router = router_find[0]
else:
    router = prov.networking.routers.create(network=net, name=router_name)
    router.attach_subnet(sn)

gateway = net.gateways.get_or_create_inet_gateway(prefix + 'gateway')
router.attach_gateway(gateway)

# Getting already existing firewall or creating a new one
fw_name = prefix + 'firewall'
fw_find = prov.security.vm_firewalls.find(name=fw_name)
if len(fw_find) > 0:
    fw = fw_find[0]
else:
    fw = prov.security.vm_firewalls.create(fw_name, 'Instances for demo', net.id)
    # Opening up the appropriate ports
    fw.rules.create(resources.TrafficDirection.INBOUND, 'tcp', 220, 220, '0.0.0.0/0')
    fw.rules.create(resources.TrafficDirection.INBOUND, 'tcp', 21, 21, '0.0.0.0/0')
    fw.rules.create(resources.TrafficDirection.INBOUND, 'tcp', 22, 22, '0.0.0.0/0')
    fw.rules.create(resources.TrafficDirection.INBOUND, 'tcp', 80, 80, '0.0.0.0/0')
    fw.rules.create(resources.TrafficDirection.INBOUND, 'tcp', 8080, 8080, '0.0.0.0/0')
    fw.rules.create(resources.TrafficDirection.INBOUND, 'tcp', 30000, 30100, '0.0.0.0/0')

# Get m1.small VM type (hardcoded), and print to make sure it is the desired one
vm_type = sorted([t for t in prov.compute.vm_types
                 if t.vcpus >= 2 and t.ram >= 4],
                 key=lambda x: x.vcpus*x.ram)[0]

print('VM Type used: ')
print(vm_type)


def create_instances(n):
    '''
    Creates the indicated number of instances after initialization.
    '''
    inst_names = []
    inst_ids = []
    inst_ips = []

    for i in range(n):
        print('\nCreating Instance #' + str(i))
        curr_name = prefix + str(i)
        inst = prov.compute.instances.create(
            name=curr_name, image=image_id, vm_type=vm_type,
            subnet=sn, key_pair=kp, vm_firewalls=[fw])
        inst.wait_till_ready()  # This is a blocking call

        # Track instances for immediate clean-up if requested
        inst_names.append(curr_name)
        inst_ids.append(inst.id)

        # Get an available or create a floating IP, then attach it and print
        # the public ip
        fip = None
        for each_fip in gateway.floating_ips.list():
            if not each_fip.in_use:
                fip = each_fip
                break

        if fip is None:
            fip = gateway.floating_ips.create()

        inst.add_floating_ip(fip)
        inst.refresh()
        inst_ip = str(inst.public_ips[0])
        print('Instance Public IP: ' + inst_ip)

        inst_ips.append(inst_ip)

        print('Instance "' + curr_name + '"" created.')

    print(str(n) + ' instances were successfully created.')
    return inst_names, inst_ids, inst_ips


names, ids, ips = create_instances(1)
table = '{},{},{}\n'
with open('info.txt', 'a') as info:
    for i in range(len(names)):
        info.write(table.format(names[i], ids[i], ips[i]))
