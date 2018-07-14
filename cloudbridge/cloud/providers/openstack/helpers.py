"""
Helper functions
"""
import itertools
import logging as log

from cloudbridge.cloud.base.resources import ServerPagedResultList


def os_result_limit(provider, requested_limit=None):
    """
    Calculates the limit for OpenStack.
    """
    limit = requested_limit or provider.config.default_result_limit
    # fetch one more than the limit to help with paging.
    # i.e. if length(objects) is one more than the limit,
    # we know that the object has another page of results,
    # so we always request one extra record.
    log.debug("Limit of OpenStack: %s Requested Limit: %s",
              limit, requested_limit)
    return limit + 1


def to_server_paged_list(provider, objects, limit=None):
    """
    A convenience function for wrapping a list of OpenStack native objects in
    a ServerPagedResultList. OpenStack
    initial list of objects. Thereafter, the return list is wrapped in a
    BaseResultList, enabling extra properties like
    `is_truncated` and `marker` to be accessed.
    """
    limit = limit or provider.config.default_result_limit
    is_truncated = len(objects) > limit
    next_token = objects[limit-1].id if is_truncated else None
    results = ServerPagedResultList(is_truncated,
                                    next_token,
                                    False)
    for obj in itertools.islice(objects, limit):
        results.append(obj)
    return results
