from abc import ABCMeta, abstractmethod


class EventDispatcher(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def observe(self, event_name, priority, callback):
        """
        Register a callback to be invoked when a given event occurs. `observe`
        will allow you to listen to events as they occur, but not modify the
        event chain or its parameters. If you need to modify an event, use
        the `intercept` method. `observe` is a simplified case of `intercept`,
        and receives a simpler list of parameters in its callback.

        :type event_name: str
        :param event_name: The name of the event to which you are subscribing
            the callback function. Accepts wildcard parameters.

        :type priority: int
        :param priority: The priority that this handler should be given.
            When the event is emitted, all handlers will be run in order of
            priority.

        :type callback: function
        :param callback: The callback function that should be called with
            the parameters given at when the even is emitted.
        """
        pass

    @abstractmethod
    def intercept(self, event_name, priority, callback):
        """
        Register a callback to be invoked when a given event occurs. Intercept
        will allow you to both observe events and modify the event chain and
        its parameters. If you only want to observe an event, use the `observe`
        method. Intercept and `observe` only differ in what parameters the
        callback receives, with intercept receiving additional parameters to
        allow controlling the event chain.

        :type event_name: str
        :param event_name: The name of the event to which you are subscribing
            the callback function. Accepts wildcard parameters.

        :type priority: int
        :param priority: The priority that this handler should be given.
            When the event is emitted, all handlers will be run in order of
            priority.

        :type callback: function
        :param callback: The callback function that should be called with
            the parameters given at when the even is emitted.
        """
        pass

    @abstractmethod
    def call(self, event_name, priority, callback, **kwargs):
        """
        Raises an event while registering a given callback

        :type event_name: str
        :param event_name: The name of the event to which you are subscribing
            the callback function. Accepts wildcard parameters.

        :type priority: int
        :param priority: The priority that this handler should be given.
            When the event is emitted, all handlers will be run in order of
            priority.

        :type callback: function
        :param callback: The callback function that should be called with
            the parameters given at when the even is emitted.
        """
        pass
