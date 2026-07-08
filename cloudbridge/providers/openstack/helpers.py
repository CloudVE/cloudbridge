"""
Helper functions
"""
from __future__ import annotations

import itertools
import logging as log
from typing import Any
from typing import Sequence

from cloudbridge.base.resources import ServerPagedResultList
from cloudbridge.interfaces.provider import CloudProvider


def os_result_limit(provider: CloudProvider,
                    requested_limit: int | None = None) -> int:
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


def to_server_paged_list(provider: CloudProvider, objects: Sequence[Any],
                         limit: int | None = None) -> ServerPagedResultList[Any]:
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
    results: ServerPagedResultList[Any] = ServerPagedResultList(is_truncated,
                                                                next_token,
                                                                False)
    for obj in itertools.islice(objects, limit):
        results.append(obj)
    return results
