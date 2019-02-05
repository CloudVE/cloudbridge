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

        :rtype: :class:`.EventHandler`
        :return:  An object of class EventHandler. The EventHandler will
        already be subscribed to the dispatcher, and need not be manually
        subscribed. The returned event handler can be used to unsubscribe
        from future events when required.
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

        :rtype: :class:`.EventHandler`
        :return:  An object of class EventHandler. The EventHandler will
        already be subscribed to the dispatcher, and need not be manually
        subscribed. The returned event handler can be used to unsubscribe
        from future events when required.
        """
        pass

    @abstractmethod
    def emit(self, sender, event_name, **kwargs):
        """
        Raises an event while registering a given callback

        :type event_name: str
        :param event_name: The name of the event which is being raised.

        :type sender: object
        :param sender: The object which is raising the event
        """
        pass

    @abstractmethod
    def subscribe(self, event_handler):
        """
        Register an event handler with this dispatcher. The observe and
        intercept methods will construct an event handler and subscribe it for
        you automatically, and therefore, there is usually no need to invoke
        subscribe directly unless you have a special type of event handler.

        :type event_handler: :class:`.EventHandler`
        :param event_handler: An object of class EventHandler.
        """
        pass

    @abstractmethod
    def unsubscribe(self, event_handler):
        """
        Unregister an event handler from this dispatcher. The event handler
        will no longer be notified on events.

        :type event_handler: :class:`.EventHandler`
        :param event_handler: An object of class EventHandler.
        """
        pass


class EventHandler(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def invoke(self, **kwargs):
        """
        Executes this event handler's callback
        """
        pass

    @abstractmethod
    def unsubscribe(self):
        """
        Unsubscribes from currently subscribed events.
        """
        pass

    @abstractmethod
    def dispatcher(self):
        """
        Get or sets the dispatcher currently associated with this event handler
        """
        pass
