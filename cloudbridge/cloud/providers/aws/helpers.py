"""
Helper functions
"""


def to_filter(provider, limit, marker):
    """
    Creates an aws filter dict for limit and marker
    """
    params = {}
    params['MaxResults'] = limit or provider.config.result_limit
    if marker:
        params['NextToken'] = marker
    return params
