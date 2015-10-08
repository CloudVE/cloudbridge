from setuptools import setup, find_packages


setup(name='cloudbridge',
      version=0.1,
      description='A simple layer of abstraction over multiple cloud'
      'providers.',
      author='Galaxy and GVL Projects',
      author_email='support@genome.edu.au',
      url='http://cloudbridge.readthedocs.org/',
      install_requires=['bunch>=1.00', 'six>=1.9.0',
                        'python-keystoneclient', 'python-novaclient',
                        'python-cinderclient', 'boto'],
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
