"""
A utility class with convenience classes.
"""


class Bunch(object):
    """
    A convenience class to allow dict keys to be represented as object fields.

    The end result is that this allows a dict to be to be represented the same
    as a database class, thus the two become interchangeable as a data source.
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        """
        Return the contents of the dict in a printable representation
        """
        return str(self.__dict__)

    def get(self, key, default=None):
        """
        Returns a value for the given key, if found or `'default` otherwise.
        """
        return self.__dict__.get(key, default)
