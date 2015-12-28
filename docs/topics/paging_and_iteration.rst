Paging and iteration
====================

Overview
--------
Most provider services have list() methods, and all list methods accept a limit
parameter which specifies the maximum number of results to return. If a limit
is not specified, cloudbridge will default to the global configuration variable
`default_result_limit`, which can be modified through the provider config.

Since the returned result list may have more records available, CloudBridge
will always return a :py:class:`ResultList` object to assist with paging through
additional results. A ResultList extends the standard :py:class:`list` and
the following example illustrates how to fetch additional records.

Example:

.. code-block:: python

    # get first page of results
    rl = provider.compute.instances.list(limit=50)
    for result in rl:
        print("Instance Data: {0}", result)
    if rl.supports_total:
        print("Total results: {0}".format(rl.total_results))
    else:
        print("Total records unknown,"
              "but has more data?: {0}."format(rl.is_truncated))

    # Page to next set of results
    if (rl.is_truncated)
        rl = provider.compute.instances.list(limit=100,
                                             marker=rl.marker)
"""

To ease development, CloudBridge also provides standard Python iterators that will page
the results in for you automatically. Therefore, when you need to iterate through all
available objects, the following shorthand is recommended:

Example:

.. code-block:: python

    # Iterate through all results
    for instance in provider.compute.instances:
        print("Instance Data: {0}", instance)
"""
