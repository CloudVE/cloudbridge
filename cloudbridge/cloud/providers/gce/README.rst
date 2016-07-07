CloudBridge support for Google compute engine and cloud storage.

Security Groups
~~~~~~~~~~~~~~~
CloudBridge API lets you control incoming traffic to VM instances by creating
security groups, adding rules to security groups, and then assigning instances
to security groups.

GCE does this a little bit differently. GCE lets you assign `tags`_ to VM
instances. Tags, then, can be used for networking purposes. In particular, you
can create `firewall rules`_ to control incoming traffic to instances having a
specific tag. So, to add GCE support to CloudBridge, we simulate security groups
by tags.

To make this more clear, let us consider the example of adding a rule to a
security group. When you add a security group rule from the CloudBridge API to a
security group ``sg``, what really happens, when the cloud provider is GCE, is
that a firewall with one rule is created whose ``targetTags`` is ``[sg]``. This
makes sure that the rule applies to all instances that have ``sg`` as a tag (in
CloudBridge language instances belonging to the security group ``sg``).

**Note**: This implementation does not take advantage of the full power of GCE
firewall format and only creates firewalls with one rule and only sees firewalls
with one rule.  This should be OK as long as all firewalls are created through
the CloudBridge API.

.. _`tags`: https://cloud.google.com/compute/docs/reference/latest/instances/
   setTags
.. _`firewall rules`: https://cloud.google.com/compute/docs/
   networking#firewall_rules
