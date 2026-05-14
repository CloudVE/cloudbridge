"""
CloudBridge provides a uniform interface to multiple IaaS cloud providers.
"""

import ast
import os
import re

from setuptools import find_packages, setup

# Cannot use "from cloudbridge import get_version" because that would try to
# import the six package which may not be installed yet.
reg = re.compile(r'__version__\s*=\s*(.+)')
with open(os.path.join('cloudbridge', '__init__.py')) as f:
    for line in f:
        m = reg.match(line)
        if m:
            version = ast.literal_eval(m.group(1))
            break

REQS_BASE = [
    'six>=1.11',
    'tenacity>=6.0',
    'deprecation>=2.0.7',
    'pyeventsystem<2'
]
REQS_AWS = [
    'boto3>=1.9.86,<2.0.0'
]
# Install azure>=3.0.0 package to find which of the azure libraries listed
# below are compatible with each other. List individual libraries instead
# of using the azure umbrella package to speed up installation.
REQS_AZURE = [
    # Minimums match SDK generation tested against the model-class
    # serialization fixes in cloudbridge/providers/azure/. Older SDKs may
    # work but are not covered by integration tests.
    'azure-identity>=1.20.0,<2.0.0',
    'azure-common>=1.1.28,<2.0.0',
    'azure-core>=1.30.0,<2.0.0',
    'azure-mgmt-devtestlabs>=9.0.0,<10.0.0',
    'azure-mgmt-resource>=23.0.0,<26.0.0',
    'azure-mgmt-subscription>=3.0.0,<4.0.0',
    'azure-mgmt-compute>=34.0.0,<39.0.0',
    'azure-mgmt-network>=28.0.0,<31.0.0',
    'azure-mgmt-storage>=22.0.0,<25.0.0',
    'azure-storage-blob>=12.20.0,<13.0.0',
    'azure-data-tables>=12.4.0,<13.0.0',
    'paramiko<6.0.0'
]
REQS_GCP = [
    'google-api-python-client>=2.0,<3.0.0'
]
REQS_OPENSTACK = [
    # Minimums match SDK generation tested against the OpenStack
    # provider fixes in cloudbridge/providers/openstack/. The previous
    # floors were circa-2018 and exposed Nova/Neutron APIs (e.g. the
    # add_floating_ip_to_server action) that are gone from any modern
    # OpenStack deployment.
    'openstacksdk>=3.0.0,<5.0.0',
    'python-novaclient>=17.0.0,<20.0',
    'python-swiftclient>=4.0.0,<5.0',
    'python-neutronclient>=11.0.0,<13.0',
    'python-keystoneclient>=4.0.0,<7.0'
]
REQS_FULL = REQS_AWS + REQS_GCP + REQS_OPENSTACK + REQS_AZURE
# httpretty is required with/for moto 1.0.0 or AWS tests fail
REQS_DEV = ([
    'tox>=4.0.0',
    'pytest',
    'moto[ec2,s3]>=5.0.0',
    'sphinx>=1.3.1',
    'pydevd',
    'flake8>=3.3.0',
    'flake8-import-order>=0.12'] + REQS_FULL
)

setup(
    name='cloudbridge',
    version=version,
    description='A simple layer of abstraction over multiple cloud providers.',
    long_description=__doc__,
    author='Galaxy and GVL Projects',
    author_email='help@genome.edu.au',
    url='http://cloudbridge.cloudve.org/',
    install_requires=REQS_BASE,
    extras_require={
        ':python_version<"3.3"': ['ipaddress'],
        'azure': REQS_AZURE,
        'gcp': REQS_GCP,
        'aws': REQS_AWS,
        'openstack': REQS_OPENSTACK,
        'full': REQS_FULL,
        'dev': REQS_DEV
    },
    packages=find_packages(),
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython'],
    test_suite="tests"
)
