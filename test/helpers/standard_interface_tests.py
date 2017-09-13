"""
Standard tests for behaviour common across the whole of cloudbridge.
This includes:
   1. Checking that every resource has an id property
   2. Checking for object equality and repr
   3. Checking standard behaviour for list, iter, find, get, delete
"""
import uuid

from cloudbridge.cloud.interfaces.exceptions \
    import InvalidNameException
from cloudbridge.cloud.interfaces.resources import ResultList


def check_repr(test, obj):
    test.assertTrue(
        obj.id in repr(obj),
        "repr(obj) for %s contain the object id so that the object"
        " can be reconstructed, but does not. eval(repr(obj)) == obj"
        % (type(obj).__name__,))


def check_json(test, obj):
    val = obj.to_json()
    test.assertEqual(val.get('id'), obj.id)
    test.assertEqual(val.get('name'), obj.name)


def check_obj_properties(test, obj):
    test.assertEqual(obj, obj, "Object should be equal to itself")
    test.assertFalse(obj != obj, "Object inequality should be false")
    check_obj_name(test, obj)


def check_list(test, service, obj):
    list_objs = service.list()
    test.assertIsInstance(list_objs, ResultList)
    all_records = list_objs
    while list_objs.is_truncated:
        list_objs = service.list(marker=list_objs.marker)
        all_records += list_objs
    match_objs = [o for o in all_records if o.id == obj.id]
    test.assertTrue(
        len(match_objs) == 1,
        "List objects for %s does not return the expected object id %s. Got %s"
        % (type(obj).__name__, obj.id, match_objs))
    return match_objs


def check_iter(test, service, obj):
    # check iteration
    iter_objs = list(service)
    iter_ids = [o.id for o in service]
    test.assertEqual(len(set(iter_ids)), len(iter_ids),
                     "Iteration should not return duplicates")
    match_objs = [o for o in iter_objs if o.id == obj.id]
    test.assertTrue(
        len(match_objs) == 1,
        "Iter objects for %s does not return the expected object id %s. Got %s"
        % (type(obj).__name__, obj.id, match_objs))
    return match_objs


def check_find(test, service, obj):
    # check find
    find_objs = service.find(name=obj.name)
    test.assertTrue(
        len(find_objs) == 1,
        "Find objects for %s does not return the expected object: %s. Got %s"
        % (type(obj).__name__, obj.name, find_objs))
    return find_objs


def check_find_non_existent(test, service):
    # check find
    find_objs = service.find(name="random_imagined_obj_name")
    test.assertTrue(
        len(find_objs) == 0,
        "Find non-existent object for %s returned unexpected objects: %s"
        % (type(service).__name__, find_objs))


def check_get(test, service, obj):
    get_obj = service.get(obj.id)
    print("Actual - " + str(obj.__dict__))
    print("Get - " + str(get_obj.__dict__))
    test.assertEqual(get_obj.name, obj.name)
    test.assertEqual(get_obj._provider, obj._provider)
    test.assertEqual(get_obj.id, obj.id)
    test.assertEqual(get_obj.state, obj.state)
    test.assertEqual(get_obj, obj)
    test.assertIsInstance(get_obj, type(obj))
    return get_obj


def check_get_non_existent(test, service):
    # check get
    get_objs = service.get(str(uuid.uuid4()))
    test.assertIsNone(
        get_objs,
        "Get non-existent object for %s returned unexpected objects: %s"
        % (type(service).__name__, get_objs))


def check_delete(test, service, obj, perform_delete=False):
    if perform_delete:
        obj.delete()

    objs = service.list()
    found_objs = [o for o in objs if o.id == obj.id]
    test.assertTrue(
        len(found_objs) == 0,
        "Object %s in service %s should have been deleted but still exists."
        % (found_objs, type(service).__name__))


def check_obj_name(test, obj):
    """
    Cloudbridge identifiers must be 1-63 characters long, and comply with
    RFC1035. In addition, identifiers should contain only lowercase letters,
    numeric characters, underscores, and dashes. International
    characters are allowed.
    """

    # if name has a setter, make sure invalid values cannot be set
    name_property = getattr(type(obj), 'name', None)
    if isinstance(name_property, property) and name_property.fset:
        # setting letters, numbers and international characters should succeed
        # TODO: Unicode characters trip up Moto. Add following: \u0D85\u0200
        VALID_NAME = u"hello_world-123"
        original_name = obj.name
        obj.name = VALID_NAME
        # setting spaces should raise an exception
        with test.assertRaises(InvalidNameException):
            obj.name = "hello world"
        # setting upper case characters should raise an exception
        with test.assertRaises(InvalidNameException):
            obj.name = "hello World"
        # setting special characters should raise an exception
        with test.assertRaises(InvalidNameException):
            obj.name = "hello.world:how_goes_it"
        # setting a length > 63 should result in an exception
        with test.assertRaises(InvalidNameException,
                               msg="Name of length > 64 should be disallowed"):
            obj.name = "a" * 64
        # refreshing should yield the last successfully set name
        obj.refresh()
        test.assertEqual(obj.name, VALID_NAME)
        obj.name = original_name
    pass


def check_standard_behaviour(test, service, obj):
    """
    Checks standard behaviour in a given cloudbridge resource
    of a given service.
    """
    check_repr(test, obj)
    check_json(test, obj)
    check_obj_properties(test, obj)
    objs_list = check_list(test, service, obj)
    objs_iter = check_iter(test, service, obj)
    objs_find = check_find(test, service, obj)
    check_find_non_existent(test, service)
    obj_get = check_get(test, service, obj)
    check_get_non_existent(test, service)

    test.assertTrue(
        obj.state == objs_list[0].state == objs_iter[0].state ==
        objs_find[0].state == obj_get.state,
        "Object Ids returned by list: {0}, iter: {1}, find: {2} and get: {3} "
        " are not as expected: {4}".format(objs_list[0].id, objs_iter[0].id,
                                           objs_find[0].id, obj_get.id,
                                           obj.id))

    test.assertTrue(
        obj._provider == objs_list[0]._provider == objs_iter[0]._provider ==
        objs_find[0]._provider == obj_get._provider,
        "Object Ids returned by list: {0}, iter: {1}, find: {2} and get: {3} "
        " are not as expected: {4}".format(objs_list[0].id, objs_iter[0].id,
                                           objs_find[0].id, obj_get.id,
                                           obj.id))


    test.assertTrue(
        obj.id == objs_list[0].id == objs_iter[0].id ==
        objs_find[0].id == obj_get.id,
        "Object Ids returned by list: {0}, iter: {1}, find: {2} and get: {3} "
        " are not as expected: {4}".format(objs_list[0].id, objs_iter[0].id,
                                           objs_find[0].id, obj_get.id,
                                           obj.id))

    test.assertTrue(
        obj.name == objs_list[0].name == objs_iter[0].name ==
        objs_find[0].name == obj_get.name,
        "Names returned by list: {0}, iter: {1}, find: {2} and get: {3} "
        " are not as expected: {4}".format(objs_list[0].id, objs_iter[0].id,
                                           objs_find[0].id, obj_get.id,
                                           obj.id))

    test.assertTrue(
        obj == objs_list[0] == objs_iter[0] == objs_find[0] == obj_get,
        "Objects returned by list: {0}, iter: {1}, find: {2} and get: {3} "
        " are not as expected: {4}".format(objs_list[0].id, objs_iter[0].id,
                                           objs_find[0].id, obj_get.id,
                                           obj.id))
