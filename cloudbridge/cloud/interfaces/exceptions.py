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


class ProviderConnectionException(CloudBridgeBaseException):
    """
    Marker interface for connection errors to a cloud provider.
    Thrown when cloudbridge is unable to connect with a provider,
    for example, when credentials are incorrect, or connection
    settings are invalid.
    """
    pass


class InvalidNameException(CloudBridgeBaseException):
    """
    Marker interface for any attempt to set an invalid name on
    a cloudbridge resource.An example would be setting uppercase
    letters, which are not allowed in a resource name.
    """

    def __init__(self, msg):
        super(InvalidNameException, self).__init__(msg)
