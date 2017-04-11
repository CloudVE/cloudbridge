Release Process
~~~~~~~~~~~~~~~

1. Increment version number in cloudbridge/__init__.py as per semver rules.

2. Freeze all library dependencies in setup.py. The version numbers can be a range
   with the upper limit being the latest known working version, and the lowest being
   the last known working version. 

3. Run all tox tests.

4. Add release notes to CHANGELOG.rst. Also add last commit hash to changelog.

5. Release to PyPi

.. code-block:: bash

   python setup.py sdist upload
   python setup.py bdist_wheel upload

6. Tag release and make github release.