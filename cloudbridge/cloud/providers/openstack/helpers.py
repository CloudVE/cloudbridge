"""
Helper functions
"""
import itertools
from cloudbridge.cloud.base import BaseResultList


def to_result_list(provider, limit, list_func):
    """
    A convenience function for wrapping a list of openstack native objects in
    a BaseResultList. The list_func is called with a custom limit to fetch the
    initial list of objects. Thereafter, the return list is wrapped in a
    BaseResultList, enabling extra properties like
    `is_truncated` and `marker` to be accessed.
    """
    limit = limit or provider.config.result_limit
    # Fetch one more than the limit, so we can
    # detect whether is_truncated=True
    objects = list_func(limit + 1)
    is_truncated = len(objects) > limit
    next_token = objects[-2].id if is_truncated else None
    results = BaseResultList(is_truncated,
                             next_token,
                             False)
    for obj in itertools.islice(objects, limit):
        results.append(obj)
    return results
