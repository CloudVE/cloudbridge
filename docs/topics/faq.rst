FAQ
===

1. Using cloudbridge across zones

   Currently, each instance of a cloudbridge provider is designated to work within a
   particular zone, for reasons clarified here: :ref:`single-zone-provider`.

   To perform cross-zonal operations, we recommend cloning the provider into a different
   zone as in this example:

    .. code-block:: python

    all_instances = []
    for zone in provider.compute.regions.current.zones:
        new_provider = provider.clone(zone=zone)
        all_instances.append(list(new_provider.compute.instances))
    print(all_instances)


2. Cleaning up resources/left over resources

   The trickiest part about using cloud resources is the orderly cleanup of resources
   when they are no longer needed. Cleanup is often complicated, as cloud-providers
   may have delays in responding at certain times, and transient errors at other times.
   While cloudbridge does not designate a particular strategy to combat this,
   the `controller pattern`_ is a recommended mechanism for handling such scenarios:


   Cloudbridge provides some utilities that can aid in simpler scenarios, such as
   `wait_for`, the cleanup helper and retries.

   The following example demonstrates a scenario where an instance and its attached
   volume must be deleted.

    .. code-block:: python

    from cloudbridge.base import helpers as cb_helpers
    import tenacity

    def does_instance_or_volume_still_exist(inst, vol):
        return provider.compute.instances.get(inst.id) or
               provider.storage.volumes.get(vol.id)

    def detach_and_delete(inst, vol)
        with cb_helpers.cleanup_action(lambda: inst.delete()):
            vol.detach()
            vol.wait_for(
                [VolumeState.AVAILABLE],
                terminal_states=[VolumeState.ERROR, VolumeState.DELETED])
            vol.delete()
            self.wait_for([VolumeState.UNKNOWN, VolumeState.ERROR])

    def delete_my_instance_and_attached_volume(provider, instance, vol):
        retryer = tenacity.Retrying(
            stop=tenacity.stop_after_delay(300),
            retry=tenacity.retry_if_result(does_instance_or_volume_still_exist(instance, vol),
            wait=tenacity.wait_fixed(5))

        retryer(detach_and_delete, instance, vol)

    # invoke with the instance and vol you want to delete
    delete_my_instance_and_attached_volume(my_inst, my_vol)


   The code above attempts to first detach and then delete the volume.
   If an exception occurs, such as the volume not existing, the `cleanup_action` code
   ensures that the `inst.delete()` code runs regardless of the success or failure
   of the volume deletion operation. The tenacity.retryer wraps the entire operation
   so that the overall process will repeat till both the volume nor the instance no
   longer exist.


.. _controller pattern: https://kubernetes.io/docs/concepts/architecture/controller/#controller-pattern
