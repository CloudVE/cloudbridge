Design decisions
~~~~~~~~~~~~~~~~

This document captures outcomes and, in some cases, the through process behind
some of the design decisions that took place while architecting CloudBridge.
It is intended as a reference.

- **Require zone parameter when creating a default subnet.**

  Placement zone is required because it is an explicit application decision,
  even though ideally *default* would not require input. Before requiring it,
  the implementations would create a subnet in each availability zone and return
  the first one in the list. This could potentially return different values over
  time. Another factor influencing the decision was the example of creating a
  volume followed by creating an instance with presumably the two needing to be
  in the same zone. By requiring the zone across the board, it is less likely to
  lead to a miss match. (Related to 63_.)

- **Name property updates will result in cloud-dependent code.**

  Some providers (e.g., GCE, Azure) do not allow names of resources to be
  changed after a resource has been created. Similarly, AWS does not allow VM
  firewall (i.e., security group) names to be changed. Providers seem to be
  gravitating toward use of tags (or labels) to support arbitrary naming and
  name changes. Yet, OpenStack for example, does not have a concept of resource
  tags so CloudBridge cannot rely solely on tags. Further, tags do not need to
  be unique across multiple resources, while names do (at least for some
  resources, such as vmfirewalls within a private network). Overall, consistency
  is challenging to achieve with resource renaming. With that, CloudBridge will
  support resource renaming to the best extent possible and balance between the
  use of resource name property and resource tags. However, because of the
  inconsistency of rename functionality across the providers, using the rename
  capabilities within CloudBridge will lead to cloud-dependent code. (Related to
  131_.)

  .. _63: https://github.com/CloudVE/cloudbridge/issues/63
  .. _131: https://github.com/CloudVE/cloudbridge/issues/131
