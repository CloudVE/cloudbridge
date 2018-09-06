Release Process
~~~~~~~~~~~~~~~

1. Increment version number in ``cloudbridge/__init__.py`` as per
   `semver rules <https://semver.org/>_.

2. Freeze all library dependencies in ``setup.py``. The version numbers can be
   a range with the upper limit being the latest known working version, and the
   lowest being the last known working version.

3. Run all ``tox`` tests.

4. Add release notes to ``CHANGELOG.rst``. Also add last commit hash to
   changelog. List of commits can be obtained using
   ``git shortlog <last release hash>..HEAD``

5. Release to PyPi
   (make sure you have run `pip install wheel`)

.. code-block:: bash

   python setup.py sdist upload
   python setup.py bdist_wheel upload

6. Tag release and make a GitHub release.

.. code-block:: bash

   git tag -a v1.0.0 -m "Release 1.0.0"
   git push --tags

7. Increment version number in ``cloudbridge/__init__.py`` to ``version-dev``
   to indicate the development cycle, commit, and push the changes.
