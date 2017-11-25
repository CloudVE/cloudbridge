"""
Standard tests for behaviour common across the whole of cloudbridge.
This includes:
   1. Checking that every resource has an id property
   2. Checking for object equality and repr
   3. Checking standard behaviour for list, iter, find, get, delete
"""
import test.helpers as helpers
import uuid

from cloudbridge.cloud.interfaces.exceptions \
    import InvalidNameException
from cloudbridge.cloud.interfaces.resources import ObjectLifeCycleMixin
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
            obj.name = "helloWorld"
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
        obj == objs_list[0] == objs_iter[0] == objs_find[0] == obj_get,
        "Objects returned by list: {0}, iter: {1}, find: {2} and get: {3} "
        " are not as expected: {4}" .format(objs_list[0].id, objs_iter[0].id,
                                            objs_find[0].id, obj_get.id,
                                            obj.id))

    test.assertTrue(
        obj.id == objs_list[0].id == objs_iter[0].id ==
        objs_find[0].id == obj_get.id,
        "Object Ids returned by list: {0}, iter: {1}, find: {2} and get: {3} "
        " are not as expected: {4}" .format(objs_list[0].id, objs_iter[0].id,
                                            objs_find[0].id, obj_get.id,
                                            obj.id))

    test.assertTrue(
        obj.name == objs_list[0].name == objs_iter[0].name ==
        objs_find[0].name == obj_get.name,
        "Names returned by list: {0}, iter: {1}, find: {2} and get: {3} "
        " are not as expected: {4}" .format(objs_list[0].id, objs_iter[0].id,
                                            objs_find[0].id, obj_get.id,
                                            obj.id))


def check_create(test, service, iface, name_prefix,
                 create_func, cleanup_func):

    # check create with invalid name
    with test.assertRaises(InvalidNameException):
        # spaces should raise an exception
        create_func("hello world")
    # check create with invalid name
    with test.assertRaises(InvalidNameException):
        # uppercase characters should raise an exception
        create_func("helloWorld")
    # setting special characters should raise an exception
    with test.assertRaises(InvalidNameException):
        create_func("hello.world:how_goes_it")
    # setting a length > 63 should result in an exception
    with test.assertRaises(InvalidNameException,
                           msg="Name of length > 64 should be disallowed"):
        create_func("a" * 64)


def check_crud(test, service, iface, name_prefix,
               create_func, cleanup_func, extra_test_func=None,
               custom_check_delete=None, skip_name_check=False):
    """
    Checks crud behaviour of a given cloudbridge service. The create_func will
    be used as a factory function to create a service object and the
    cleanup_func will be used to destroy the object. Once an object is created
    using the create_func, all other standard behavioural tests can be run
    against that object.

    :type  test: ``TestCase``
    :param test: The TestCase object to use

    :type  service: ``CloudService``
    :param service: The CloudService object under test. For example,
                    a VolumeService object.

    :type  iface: ``type``
    :param iface: The type to test behaviour against. This type must be a
                  subclass of ``CloudResource``.

    :type  name_prefix: ``str``
    :param name_prefix: The name to prefix all created objects with. This
                        function will generated a new name with the
                        specified name_prefix for each test object created
                        and pass that name into the create_func

    :type  create_func: ``func``
    :param create_func: The create_func must accept the name of the object to
                        create as a parameter and return the constructed
                        object.

    :type  cleanup_func: ``func``
    :param cleanup_func: The cleanup_func must accept the created object
                         and perform all cleanup tasks required to delete the
                         object.

    :type  extra_test_func: ``func``
    :param extra_test_func: This function will be called to perform additional
                            tests after object construction and initialization,
                            but before object cleanup. It will receive the
                            created object as a parameter.

    :type  custom_check_delete: ``func``
    :param custom_check_delete: If provided, this function will be called
                                instead of the standard check_delete function
                                to make sure that the object has been deleted.

    :type  skip_name_check: ``boolean``
    :param skip_name_check:  If True, the invalid name checking will be
                             skipped.
    """

    obj = None
    with helpers.cleanup_action(lambda: cleanup_func(obj)):
        if not skip_name_check:
            check_create(test, service, iface, name_prefix,
                         create_func, cleanup_func)
        name = "{0}-{1}".format(name_prefix, helpers.get_uuid())
        obj = create_func(name)
        if issubclass(iface, ObjectLifeCycleMixin):
            obj.wait_till_ready()
        check_standard_behaviour(test, service, obj)
        if extra_test_func:
            extra_test_func(obj)
    if custom_check_delete:
        custom_check_delete(obj)
    else:
        check_delete(test, service, obj)
