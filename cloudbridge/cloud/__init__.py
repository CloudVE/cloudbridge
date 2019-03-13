import warnings
from os.path import join

warnings.warn(
    "The cloud package is deprecated and everything under it has been moved "
    "one level up. For example, instead of "
    "`from cloudbridge.cloud.factory import CloudProviderFactory` use "
    "`from cloudbridge.factory import CloudProviderFactory`. In future "
    "versions, the cloud package will be completely removed.",
    category=RuntimeWarning)
# Redirect package one level up for backward compatibility
__path__.insert(0, join(__path__[0], ".."))
