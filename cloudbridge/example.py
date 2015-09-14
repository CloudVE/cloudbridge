from cloudbridge.providers.interfaces import CloudProviderFactory
from cloudbridge.providers.interfaces import CloudProvider


ec2driver = CloudProviderFactory().get_interface_V1("EC2")
provider = ec2driver(access_key="", secret_key="", region="", port="", connection_path="")
instances = provider.Compute.list_instances()
regions = provider.Compute.list_regions()
images = provider.Images.list_images()
volumes = provider.Compute.list_volumes()

provider.Compute.launch_instance("my_instance", regions[0], images[0])