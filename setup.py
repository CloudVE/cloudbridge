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

base_reqs = ['bunch>=1.0.1', 'six>=1.10.0', 'retrying>=1.3.3']
openstack_reqs = ['python-novaclient>=2.33.0',
                  'python-glanceclient',
                  'python-cinderclient>=1.4.0',
                  'python-swiftclient>=2.6.0',
                  'python-neutronclient>=3.1.0',
                  'python-keystoneclient>=2.0.0']
aws_reqs = ['boto>=2.38.0']
full_reqs = base_reqs + aws_reqs + openstack_reqs
dev_reqs = (['tox>=2.1.1', 'moto>=0.4.20', 'sphinx>=1.3.1'] + full_reqs)

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
          'full': full_reqs,
          'dev': dev_reqs
      },
      packages=find_packages(),
      license='MIT',
      classifiers=[
          'Development Status :: 3 - Alpha',
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
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy'],
      test_suite="test"
      )
