Resource Types and Dashboard Mapping
====================================

Cross-Platform Concepts
-----------------------

Given CloudBridge's goal to work uniformly across cloud providers, some
compromises were necessary in order to bridge the many differences between
providers' resources and features. Notably, in order to create a robust and
conceptually consistent cross-cloud library, resources were separated into
`labeled` and `unlabeled resources,` and were given three main properties:
`ID`, `name`, and `label`.
The `ID` corresponds to a unique identifier that can be reliably used to
reference a resource. Users can safely use an ID knowing that it will always
point to the same resource. All resources have an `ID` property, thus making
it the recommended oproperty for reliably identifying a resource.
The `label` property, conversely, is a modifiable value that does not need
to be unique. Unlike the name property, it is not used to identify a
particular resource, but rather label a resource for easier distinction.
Only labeled resources have the label property, and these resources require
a `label` parameter be set at creation time.
The `name` property corresponds to an unchangeable and unique designation for
a particular resource. This property is meant to be, in some ways, a more
human-readable identifier. Thus, when no conceptually comparable property
exists for a given resource in a particular provider, the ID is returned
instead, as is the case for all OpenStack and some AWS resources. Given the 
discrepancy between providers, using the `name` property is not advisable 
for cross-cloud usage of the library. Labeled resources will use the label
given at creation as a prefix to the set name, when this property is separable
from the ID as is the case in Azure and some AWS resources. Finally, unlabeled
resources will always support a `name`, and some unlabeled resources will require
a name parameter at creation. Below is a list of all resources classified by
whether they support a `label` property.

+-------------------+---------------------+
| Labeled Resources | Unlabeled Resources | 
+===================+=====================+
| Instance          | Key Pair            |
+-------------------+---------------------+
| MachineImage      | Bucket              |
+-------------------+---------------------+
| Network           | Bucket Object       |
+-------------------+---------------------+
| Subnet            | FloatingIP          |
+-------------------+---------------------+
| Router            | Internet Gateway    |
+-------------------+---------------------+
| Volume            | VMFirewall Rule     |
+-------------------+---------------------+
| Snapshot          |                     |
+-------------------+---------------------+
| VMFirewall        |                     |
+-------------------+---------------------+


Properties per Resource per Provider
------------------------------------
For each provider, we documented the mapping of CloudBridge resources and
properties to provider objects, as well as some useful dashboard navigation.
These sections will thus present summary tables delineating the different types of
CloudBridge resources, as well as present some design decisions made to
preserve consistency across providers:
-`Detailed Azure Mappings <azure_mapping.html>`_
-`Detailed AWS Mappings <aws_mapping.html>`_
-`Detailed OpenStack Mappings <os_mapping.html>`_
