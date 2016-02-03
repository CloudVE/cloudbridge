Design Goals
~~~~~~~~~~~~

1. Create a cloud abstraction layer which minimises or eliminates the need for
   cloud specific special casing (i.e., Not require clients to write
   ``if EC2 do x else if OPENSTACK do y``.)

2. Have a suite of conformance tests which are comprehensive enough that goal
   1 can be achieved. This would also mean that clients need not manually test
   against each provider to make sure their application is compatible.

3. Opt for a minimum set of features that a cloud provider will support,
   instead of  a lowest common denominator approach. This means that reasonably
   mature clouds like Amazon and OpenStack are used as the benchmark against
   which functionality & features are determined. Therefore, there is a
   definite expectation that the cloud infrastructure will support a compute
   service with support for images and snapshots and various machine sizes.
   The cloud infrastructure will very likely support block storage, although
   this is currently optional. It may optionally support object storage.

4. Make the CloudBridge layer as thin as possible without compromising goal 1.
   By wrapping the cloud provider's native SDK and doing the minimal work
   necessary to adapt the interface, we can achieve greater development speed
   and reliability since the native provider SDK is most likely to have both
   properties.