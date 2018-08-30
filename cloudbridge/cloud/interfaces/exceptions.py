"""
Specification for exceptions raised by a provider
"""


class CloudBridgeBaseException(Exception):
    """
    Base class for all CloudBridge exceptions
    """
    pass


class WaitStateException(CloudBridgeBaseException):
    """
    Marker interface for object wait exceptions.
    Thrown when a timeout or errors occurs waiting for an object does not reach
    the expected state within a specified time limit.
    """
    pass


class InvalidConfigurationException(CloudBridgeBaseException):
    """
    Marker interface for invalid launch configurations.
    Thrown when a combination of parameters in a LaunchConfig
    object results in an illegal state.
    """
    pass


class ProviderInternalException(CloudBridgeBaseException):
    """
    Marker interface for provider specific errors.
    Thrown when CloudBridge encounters an error internal to a
    provider.
    """
    pass


class ProviderConnectionException(CloudBridgeBaseException):
    """
    Marker interface for connection errors to a cloud provider.
    Thrown when CloudBridge is unable to connect with a provider,
    for example, when credentials are incorrect, or connection
    settings are invalid.
    """
    pass


class InvalidNameException(CloudBridgeBaseException):
    """
    Marker interface for any attempt to set an invalid name on
    a CloudBridge resource. An example would be setting uppercase
    letters, which are not allowed in a resource name.
    """

    def __init__(self, msg):
        super(InvalidNameException, self).__init__(msg)


class InvalidLabelException(InvalidNameException):
    """
    Marker interface for any attempt to set an invalid label on
    a CloudBridge resource. An example would be setting uppercase
    letters, which are not allowed in a resource label.
    InvalidLabelExceptions inherit from, and are a special case
    of InvalidNameExceptions. At present, these restrictions are
    identical.
    """

    def __init__(self, msg):
        super(InvalidLabelException, self).__init__(msg)


class InvalidValueException(CloudBridgeBaseException):
    """
    Marker interface for any attempt to set an invalid value on a CloudBridge
    resource.An example would be setting an unrecognised value for the
    direction of a firewall rule other than TrafficDirection.INBOUND or
    TrafficDirection.OUTBOUND.
    """
    def __init__(self, param, value):
        super(InvalidValueException, self).__init__(
            "Param %s has been given an unrecognised value %s" %
            (param, value))


class DuplicateResourceException(CloudBridgeBaseException):
    """
    Marker interface for any attempt to create a CloudBridge resource that
    already exists. For example, creating a KeyPair with the same name will
    result in a DuplicateResourceException.
    """
    pass
