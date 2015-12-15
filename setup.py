import ast
import os
import re
from setuptools import setup, find_packages

# Cannot use "from cloudbridge import get_version" because that would try to
# import the six package which may not be installed yet.
reg = re.compile(r'__version__\s*=\s*(.+)')
with open(os.path.join('cloudbridge', '__init__.py')) as f:
    for line in f:
        m = reg.match(line)
        if m:
            version = ast.literal_eval(m.group(1))
            break

base_reqs = ['bunch>=1.00', 'six>=1.9.0', 'retrying']
openstack_reqs = ['python-novaclient', 'python-glanceclient',
                  'python-cinderclient', 'python-swiftclient',
                  'python-neutronclient', 'python-keystoneclient>=2.0.0']
aws_reqs = ['boto']
full_reqs = base_reqs + aws_reqs + openstack_reqs
dev_reqs = ['httpretty==0.8.10', 'tox', 'moto>=0.4.18', 'sphinx'] + full_reqs

setup(name='cloudbridge',
      version=version,
      description='A simple layer of abstraction over multiple cloud'
      'providers.',
      author='Galaxy and GVL Projects',
      author_email='help@genome.edu.au',
      url='http://cloudbridge.readthedocs.org/',
      install_requires=full_reqs,
      extras_require={
          ':python_version=="2.7"': ['py2-ipaddress'],
          ':python_version=="3"': ['py2-ipaddress'],
          ':python_version=="3.1"': ['py2-ipaddress'],
          ':python_version=="3.2"': ['py2-ipaddress'],
          'full': full_reqs,
          'dev': dev_reqs
      },
      packages=find_packages(),
      license='MIT',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.0',
          'Programming Language :: Python :: 3.1',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy'],
      test_suite="test"
      )
