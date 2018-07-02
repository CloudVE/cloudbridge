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


  .. _63: https://github.com/CloudVE/cloudbridge/issues/63
