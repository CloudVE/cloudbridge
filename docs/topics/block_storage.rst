Working with block storage
==========================
To add persistent storage to your cloud environments, you would use block
storage devices, namely volumes and volume snapshots. A volume is attached to
an instance and mounted as a file system for use by an application. A volume
snapshot is a point-in-time snapshot of a volume that can be shared with other
cloud users. Before a snapshot can be used, it is necessary to create a volume
from it.

Volume storage
--------------
Operations, such as creating a new volume and listing the existing ones, are
performed via the :class:`.VolumeService`.

.. code-block:: python

    vol = provider.block_store.volumes.create('Cloudbridge-vol', 1, 'us-east-1a')
    vol.wait_till_ready()
    provider.block_store.volumes.list()
