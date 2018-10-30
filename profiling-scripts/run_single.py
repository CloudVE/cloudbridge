import unittest
from io import StringIO
import argparse
import importlib

parser = argparse.ArgumentParser()
parser.add_argument("suite", help="the name of the test suite from which a "
                                  "class should be profiled",
                    type=str)

args = parser.parse_args()
if not args.suite:
    print("A test suite must be provided")
else:
    mod_name = "cloudbridge.test.test_{}_service".format(args.suite)
    case_name = "Cloud{}ServiceTestCase".format("".join([x.capitalize() for
                                                         x in
                                                         args.suite.split('_')]))
    case_name = case_name.replace("VmType", "VMType").replace("CloudCloud",
                                                              "Cloud")
    if "interface" in mod_name or "cycle" in mod_name or "cloud" in mod_name:
        mod_name = mod_name.replace("_service", "")
        case_name = case_name.replace("Service", "")
    print("{}.{}\n\n".format(mod_name, case_name))
    case = getattr(importlib.import_module(mod_name), case_name)

    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    result = runner.run(unittest.makeSuite(case))
    stream.seek(0)
    print('Test output\n', stream.read())
