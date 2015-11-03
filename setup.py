from setuptools import setup, find_packages

base_reqs = ['bunch>=1.00', 'six>=1.9.0', 'retrying', 'enum34']
openstack_reqs = ['python-keystoneclient',
                  'python-novaclient', 'python-cinderclient',
                  'python-swiftclient']
aws_reqs = ['boto']
full_reqs = base_reqs + aws_reqs + openstack_reqs
dev_reqs = ['tox'] + full_reqs

setup(name='cloudbridge',
      version=0.1,
      description='A simple layer of abstraction over multiple cloud'
      'providers.',
      author='Galaxy and GVL Projects',
      author_email='support@genome.edu.au',
      url='http://cloudbridge.readthedocs.org/',
      install_requires=base_reqs,
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
