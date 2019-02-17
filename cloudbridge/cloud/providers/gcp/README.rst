CloudBridge support for `Google Cloud Platform`_. Compute is provided by `Google
Compute Engine`_ (GCP). Object storage is provided by `Google Cloud Storage`_
(GCP).

Security Groups
~~~~~~~~~~~~~~~
CloudBridge API lets you control incoming traffic to VM instances by creating
VM firewalls, adding rules to VM firewalls, and then assigning instances to VM
firewalls.

GCP does this a little bit differently. GCP lets you assign `tags`_ to VM
instances. Tags, then, can be used for networking purposes. In particular, you
can create `firewall rules`_ to control incoming traffic to instances having a
specific tag. So, to add GCP support to CloudBridge, we simulate VM firewalls by
tags.

To make this more clear, let us consider the example of adding a rule to a
VM firewall. When you add a VM firewall rule from the CloudBridge API to a VM
firewall ``vmf``, what really happens is that a firewall with one rule is
created whose ``targetTags`` is ``[vmf]``. This makes sure that the rule
applies to all instances that have ``vmf`` as a tag (in CloudBridge language
instances belonging to the VM firewall ``vmf``).

**Note**: This implementation does not take advantage of the full power of GCP
firewall format and only creates firewalls with one rule and only can find or
list firewalls with one rule. This should be OK as long as all firewalls are
created through the CloudBridge API.

.. _`Google Cloud Platform`: https://cloud.google.com/
.. _`Google compute platform`: https://cloud.google.com/compute/docs
.. _`Google Cloud Storage`: https://cloud.google.com/storage/docs
.. _`tags`: https://cloud.google.com/compute/docs/reference/latest/instances/
   setTags
.. _`firewall rules`: https://cloud.google.com/compute/docs/
   networking#firewall_rules
