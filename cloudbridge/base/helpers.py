import fnmatch
import functools
import logging
import os
import re
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from typing import TypeVar
from typing import cast
from typing import overload

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization as crypt_serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from deprecation import deprecated

import cloudbridge

from ..interfaces.exceptions import InvalidParamException

log = logging.getLogger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def generate_key_pair() -> tuple[str, str]:
    """
    This method generates a keypair and returns it as a tuple
    of (public, private) keys.
    The public key format is OpenSSH and private key format is PEM.
    """
    key_pair = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048)
    private_key = key_pair.private_bytes(
        crypt_serialization.Encoding.PEM,
        crypt_serialization.PrivateFormat.PKCS8,
        crypt_serialization.NoEncryption()).decode('utf-8')
    public_key = key_pair.public_key().public_bytes(
        crypt_serialization.Encoding.OpenSSH,
        crypt_serialization.PublicFormat.OpenSSH).decode('utf-8')
    return public_key, private_key


def filter_by(prop_name: str, kwargs: dict[str, Any],
              objs: list[T]) -> list[T]:
    """
    Utility method for filtering a list of objects by a property.
    If the given property has a non empty value in kwargs, then
    the list of objs is filtered by that value. Otherwise, the
    list of objs is returned as is.
    """
    prop_val = kwargs.pop(prop_name, None)
    if prop_val:
        if isinstance(prop_val, str):
            regex = fnmatch.translate(prop_val)
            results = [o for o in objs
                       if getattr(o, prop_name)
                       and re.search(regex, getattr(o, prop_name))]
        else:
            results = [o for o in objs
                       if getattr(o, prop_name) == prop_val]
        return results
    else:
        return objs


def generic_find(filter_names: list[str], kwargs: dict[str, Any],
                 objs: list[T]) -> list[T]:
    """
    Utility method for filtering a list of objects by a list of filters.
    """
    matches = objs
    for name in filter_names:
        matches = filter_by(name, kwargs, matches)

    # All kwargs should have been popped at this time.
    if len(kwargs) > 0:
        raise InvalidParamException(
            "Unrecognised parameters for search: %s. Supported attributes: %s"
            % (kwargs, filter_names))

    return matches


@contextmanager
def cleanup_action(cleanup_func: Callable[[], object]) -> Iterator[None]:
    """
    Context manager to carry out a given
    cleanup action after carrying out a set
    of tasks, or when an exception occurs.
    If any errors occur during the cleanup
    action, those are ignored, and the original
    traceback is preserved.

    :params func: This function is called if
    an exception occurs or at the end of the
    context block. If any exceptions raised
        by func are ignored.
    Usage:
        with cleanup_action(lambda e: print("Oops!")):
            do_something()
    """
    try:
        yield
    except Exception:
        try:
            cleanup_func()
        except Exception:
            log.exception("Error during exception cleanup: ")
        raise
    try:
        cleanup_func()
    except Exception:
        log.exception("Error during exception cleanup: ")


@overload
def get_env(varname: str) -> str | None:
    ...


@overload
def get_env(varname: str, default_value: T) -> str | T:
    ...


def get_env(varname: str, default_value: object = None) -> object:
    """
    Return the value of the environment variable or default_value.

    :type varname: ``str``
    :param varname: Name of the environment variable for which to check.

    :param default_value: Return this value is the env var is not found.
                          Defaults to ``None``.

    :return: Value of the supplied environment if found; value of
             ``default_value`` otherwise.
    """
    return os.environ.get(varname, default_value)


# Alias deprecation decorator, following:
# https://stackoverflow.com/questions/49802412/
# how-to-implement-deprecation-in-python-with-argument-alias
def deprecated_alias(**aliases: str) -> Callable[[F], F]:
    def deco(f: F) -> F:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            rename_kwargs(f.__name__, kwargs, aliases)
            return f(*args, **kwargs)
        return cast(F, wrapper)
    return deco


def rename_kwargs(func_name: str, kwargs: dict[str, Any],
                  aliases: dict[str, str]) -> None:
    for alias, new in aliases.items():
        if alias in kwargs:
            if new in kwargs:
                raise InvalidParamException(
                    '{} received both {} and {}'.format(func_name, alias, new))
            # Manually invoke the deprecated decorator with an empty lambda
            # to signal deprecation
            deprecated(deprecated_in='1.1',
                       removed_in='2.0',
                       current_version=cloudbridge.__version__,
                       details='{} is deprecated, use {} instead'.format(
                           alias, new))(lambda: None)()
            kwargs[new] = kwargs.pop(alias)


NON_ALPHA_NUM = re.compile(r"[^A-Za-z0-9]+")


def to_resource_name(value: str, replace_with: str = "-") -> str:
    """
    Converts a given string to a valid resource name by stripping
    all characters that are not alphanumeric.

    :param value: the value to strip
    :param replace_with: the value to replace mismatching characters with
    :return: a string with all mismatching characters removed.
    """
    val = re.sub(NON_ALPHA_NUM, replace_with, value)
    return val.strip("-")
