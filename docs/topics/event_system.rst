Working with the CloudBridge Event System
=========================================
In order to provide more comprehensive logging and standardize CloudBridge
function, we have adopted an Event Dispatcher middleware layer. In short,
each event has a corresponding list of dispatchers called in priority order.
For the time being, only a listening subscription model is implemented, thus
each event has a series of subscribed methods accepting the same parameters,
that get run in priority order along the main function call.
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
currently two supported types: `SUBSCRIPTION, and RESULT_SUBSCRIPTION.
Handlers of SUBSCRIPTION type are simple listeners, who intercept the main
function arguments but do not modify them. They are independent of any
previous or future handler, and have no return value. Their associated
callback function expects the exact same parameters as the main function.
Handlers of RESULT_SUBSCRIPTION type are similar to SUBSCRIPTION handlers,
but have access to the last non-null return value from any previous handler.
They are similarly listeners, intercepting arguments without modifying them
and do not return any value. Their associated callback will however be
called with an additional keyword parameter named 'callback_result' holding
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
| Pre-Logger             | 20000    |
+------------------------+----------+
| Main Function Call     | 25000    |
+------------------------+----------+
| Post-Logger            | 30000    |
+------------------------+----------+

The Pre- and Post- loggers represent universal loggers respectively keeping
track of the event called and its parameters before the call, and the returned
value after the call. The main function call represents the core function,
which is not subscribed permanently, but rather called directly with the event.

Example
-------

Below is an example of the way in which the Event System works for a simple
getter.

.. code-block:: python

    def _get(object_id):
        # get the object
        return obj

    def _pre_log(object_id):
        print("I am calling 'get' with object_id: {}".format(object_id))

    def _post_log(callback_result, object_id):
        print("Returned object {} for a 'get' request with object_id: {}"
        .format(callback_result, object_id))

    event_name = "service.get"

    provider.events.subscribe(event_name, priority=20000, callback=_pre_log)
    provider.events.subscribe(event_name, priority=30000, callback=_post_log)

    # Public get function
    def get(object_id):
        provider.events.interceptable_call(event_name, priority=25000,
                                           callback=_get,
                                           object_id=object_id)

In the above example, calling the public `get` function will be the
equivalent of calling the below function:

.. code-block:: python

    def get(object_id):
        _pre_log(object_id)
        result = _get(object_id)
        _post_log(callback_result=result, object_id)
        return result

