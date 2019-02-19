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
performed via the :class:`.VolumeService`. To start, let's create a 1GB volume.

.. code-block:: python

    vol = provider.storage.volumes.create('cloudbridge-vol', 1)
    vol.wait_till_ready()
    provider.storage.volumes.list()

Next, let's attach the volume to a running instance as device ``/dev/sdh``:

    vol.attach('i-dbf37022', '/dev/sdh')
    vol.refresh()
    vol.state
    # 'in-use'

Once attached, from within the instance, it is necessary to create a file
system on the new volume and mount it.

Once you wish to detach a volume from an instance, it is necessary to unmount
the file system from within the instance and detach it. The volume can then be
attached to a different instance with all the data on it preserved.

.. code-block:: python

    vol.detach()
    vol.refresh()
    vol.state
    # 'available'

Snapshot storage
----------------
A volume snapshot it created from an existing volume. Note that it may take a
long time for a snapshot to become ready, particularly on AWS.

.. code-block:: python

    snap = vol.create_snapshot('cloudbridge-snap',
                               'A demo snapshot created via CloudBridge.')
    snap.wait_till_ready()
    snap.state
    # 'available'

In order to make use of a snapshot, it is necessary to create a volume from it::

    vol = provider.storage.volumes.create(
        'cloudbridge-snap-vol', 1, 'us-east-1e', snapshot=snap)

The newly created volume behaves just like any other volume and can be attached
to an instance for use.
