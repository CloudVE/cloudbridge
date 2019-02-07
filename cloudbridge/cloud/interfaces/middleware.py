from abc import ABCMeta, abstractmethod


class Middleware(object):
    """
    Provides a mechanism for grouping related event handlers together, to
    provide logically cohesive middleware. The middleware class allows event
    handlers to subscribe to events through the install method, and unsubscribe
    through the uninstall method. This allows event handlers to be added and
    removed as a group. The event handler implementations will also typically
    live inside the middleware class. For example, LoggingMiddleware may
    register multiple event handlers to log data before and after calls.
    ResourceTrackingMiddleware may track all objects that are created or
    deleted.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def install(self, provider):
        """
        Use this method to subscribe all event handlers that are part of this
        middleware. The install method will be called when the middleware is
        first added to a MiddleWareManager.

        :type provider: :class:`.Provider`
        :param provider: The provider that this middleware belongs to
        """
        pass

    @abstractmethod
    def uninstall(self, provider):
        """
        Use this method to unsubscribe all event handlers for this middleware.
        """
        pass


class MiddlewareManager(object):
    """
    Provides a mechanism for tracking a list of installed middleware
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def add(self, middleware):
        """
        Use this method to add middleware to this middleware manager.

        :type middleware: :class:`.Middleware`
        :param middleware: The middleware implementation
        """
        pass

    @abstractmethod
    def remove(self, middleware):
        """
        Use this method to remove this middleware from the middleware manager.
        """
        pass
