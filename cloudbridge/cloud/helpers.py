"""
Helper functions
"""
import itertools
from cloudbridge.cloud.base import BaseResultList


def to_result_list(provider, objects, limit, marker):
    """
    Converts a list of objects to a ResultList, applying paging based on limit
    and marker. This method is only intended for use by cloud operations which
    do not natively support paging, since it's somewhat inefficient.
    """
    limit = limit or provider.config.result_limit
    total_size = len(objects)
    if marker:
        from_marker = itertools.dropwhile(
            lambda obj: not obj.id == marker, objects)
        # skip one past the marker
        next(from_marker, None)
        objects = list(from_marker)
    is_truncated = len(objects) > limit
    results = list(itertools.islice(objects, limit))
    return BaseResultList(is_truncated,
                          results[-1].id if is_truncated else None,
                          True, total=total_size,
                          data=results)
