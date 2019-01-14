Working with the CloudBridge Event System
=========================================
In order to provide more comprehensive logging and standardize CloudBridge
functions, we have adopted a middleware layer to handle event calls. In short,
each event has a corresponding list of dispatchers called in priority order.
For the time being, only a listening subscription model is implemented, thus
each event has a series of subscribed methods accepting the same parameters,
that get run in priority order along with the main function call.
This Event System allows both developers and users to easily add
intermediary functions by event name, without having to modify the
pre-existing code, thus improving the library's flexibility.

Event Handler
-------------
Each function attached to an event has a corresponding handler. This handler
has a type, a callback function, and a link to the next handler. When
invoked, the handler will call its callback function and, when available,
invoke the next handler in the linked list of handlers.

Handler Types
-------------
Each Event Handler has a type, which determines how it's invoked. There are
currently two supported types: `SUBSCRIPTION`, and `RESULT_SUBSCRIPTION`.
Handlers of `SUBSCRIPTION` type are simple listeners, who intercept the main
function arguments but do not modify them. They are independent of any
previous or future handler, and have no return value. Their associated
callback function expects the exact same parameters as the main function.
Handlers of `RESULT_SUBSCRIPTION` type are similar to `SUBSCRIPTION` handlers,
but have access to the last non-null return value from any previous handler.
They are similarly listeners, intercepting arguments without modifying them
and do not return any value. Their associated callback will however be
called with an additional keyword parameter named `callback_result` holding
the last non-null return value from any previous handler. The callback
function thus needs to accept such a parameter.

Event Dispatcher
----------------
A single event dispatcher is initialized with the provider, and will hold
the entirety of the handlers for all events. This dispatcher handles new
subscriptions and event calls. When an event is called, the dispatcher will
link each handler to the next one in line, then invoke the first handler,
thus triggering the chain of handlers.

Priorities
----------
As previously mentioned, dispatchers will be invoked in order of priority.
These priorities are assigned at subscription time, and must be unique.
Below are the default priorities used across events:

+------------------------+----------+
| Handler                | Priority |
+------------------------+----------+
| Pre-Logger             | 2000     |
+------------------------+----------+
| Main Function Call     | 2500     |
+------------------------+----------+
| Post-Logger            | 3000     |
+------------------------+----------+

The Pre- and Post- loggers represent universal loggers respectively keeping
track of the event called and its parameters before the call, and the returned
value after the call. The main function call represents the core function,
which is not subscribed permanently, but rather called directly with the event.

Example
-------

Below is an example of the way in which the Event System works for a simple
getter, from the CloudBridge developer perspective as well as the final user
perspective.

.. code-block:: python

    ## Provider Specific code
    class MyFirstProviderService(BaseService):

        def __init__(self, provider):
            super(MyFirstProviderService, self).__init__(provider)

        def _get(self, obj_id):
            # do the getting
            resource = ...
            return MyFirstProviderResource(resource)

    class MySecondProviderService(BaseService):

        def __init__(self, provider):
            super(MySecondProviderService, self).__init__(provider)

        def _get(self, obj_id):
            # do the getting
            resource = ...
            return MySecondProviderResource(resource)

    ## Base code
    class BaseService(ProviderService):
        def __init__(self, provider):
            super(Service, self).__init__(provider)
            self._service_event_name = "provider.service"

        def _init_get(self):

            def _get_pre_log(obj_id):
                log.debug("Getting {} object with the id: {}".format(
                    self.provider.name, bucket_id))

            def _get_post_log(callback_result, obj_id):
                log.debug("Returned object: {}".format(callback_result))

            self.subscribe_event("get", 2000, _get_pre_log)
            self.subscribe_event("get", 3000, _get_post_log,
                                 result_callback=True)

            self.mark_initialized("get")

        # Public get function
        def get(self, obj_id):
            """
            Returns an object given its ID. Returns ``None`` if the object
            does not exist.
            """
            if not self.check_initialized("get"):
                self._init_get()
            return self.call_event("get", priority=2500,
                                   main_call=self._get,
                                   obj_id=obj_id)

Thus, adding a new provider only requires adding the Service class with a
protected class accepting the same parameters, and the logging and public
method signature will remain the same, as the code will not be re-written
for each provider.
Additionally, if a developer needs to add additional logging for a
particular service, beyond the default logging for all services, they can do
so in the event initialisation function, and it will be applied to all
providers. For example:

.. code-block:: python

    ## Base code
    class BaseService(ProviderService):
        def __init__(self, provider):
            super(Service, self).__init__(provider)
            self._service_event_name = "provider.service"

        def _init_get(self):

            def _get_pre_log(obj_id):
                log.debug("Getting {} object with the id: {}".format(
                    self.provider.name, bucket_id))

            def _get_post_log(callback_result, obj_id):
                log.debug("Returned object: {}".format(callback_result))

            def _special_none_log(callback_result, obj_id):
                if not callback_result:
                    log.debug("There is no object with id '{}'".format(obj_id))

            self.subscribe_event("get", 2000, _get_pre_log)
            self.subscribe_event("get", 3000, _get_post_log,
                                 result_callback=True)
            self.subscribe_event("get", 2750, _special_none_log,
                                 result_callback=True)

            self.mark_initialized("get")

       # Public get function
        def get(self, obj_id):
            """
            Returns an object given its ID. Returns ``None`` if the object
            does not exist.
            """
            if not self.check_initialized("get"):
                self._init_get()
            return self.call_event("get", priority=2500,
                                   main_call=self._get,
                                   obj_id=obj_id)


From a user's perspective, the Event System is invisible unless the user
wishes to extend the chain of handlers with their own code. Continuing with
the service example from above:

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    provider = CloudProviderFactory().create_provider(ProviderList.FIRST, {})
    id = 'thisIsAnID'
    obj = provider.service.get(id)

However, if they wish to add their own logging interface, for example, they
can do so without modifying CloudBridge code:


.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    provider = CloudProviderFactory().create_provider(ProviderList.FIRST, {})

    ## I don't want to setup a logger, just want to print some messages for
    ## debugging
    def print_id(obj_id):
        print(obj_id)

    provider.service.subscribe_event("get", priority=2250, callback=print_id)

    id1 = 'thisIsAnID'
    id2 = 'thisIsAnID2'

    ## The subscribed print function will get called every time the get
    ## method is invoked
    obj1 = provider.service.get(id1)
    ## thisIsAnID
    obj2 = provider.service.get(id2)
    ## thisIsAnID2


