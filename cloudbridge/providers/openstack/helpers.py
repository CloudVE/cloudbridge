"""
Helper functions
"""
from __future__ import annotations

import itertools
import logging as log
import secrets
from typing import Any
from typing import Sequence
from urllib.parse import quote
from urllib.parse import urlparse

from swiftclient.utils import generate_temp_url

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


# cloudbridge 4.4 and earlier set this key on every account they signed a
# temporary URL for. It is published, so anyone could sign URLs for such an
# account: never sign with it, and replace it.
_PUBLISHED_TEMP_URL_KEY = "cloudbridge-tmp-url-key"


def temp_url_key(swift: Any) -> str:
    """
    The key to sign the account's temporary URLs with: the one its operator
    set, else one set here at random and kept for later URLs.
    """
    account = swift.head_account()
    key = account.get('x-account-meta-temp-url-key')
    if key and key != _PUBLISHED_TEMP_URL_KEY:
        return key
    if not key and account.get('x-account-meta-temp-url-key-2'):
        return account['x-account-meta-temp-url-key-2']
    # Swift has no conditional write for account metadata: of two processes
    # setting a key at once, the URLs of the one overwritten stop working.
    key = secrets.token_hex(32)
    swift.post_account(headers={'x-account-meta-temp-url-key': key})
    return key


def temp_url(swift: Any, container: str, object_name: str, expires_in: int,
             method: str) -> str:
    """
    A temporary URL for ``method`` on an object, which need not exist.
    """
    key = temp_url_key(swift)
    # Reading the account authenticated the connection, which then knows the
    # storage URL, from Keystone or as configured.
    storage_url = urlparse(swift.url)
    path = "/".join([storage_url.path, container, object_name])
    # Swift checks the signature against the path unescaped.
    query = generate_temp_url(path, expires_in, key, method).split('?', 1)[1]
    return "{0}://{1}{2}?{3}".format(storage_url.scheme, storage_url.netloc,
                                     quote(path), query)
