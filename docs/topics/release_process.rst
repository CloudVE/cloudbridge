Release Process
~~~~~~~~~~~~~~~

1. Make sure `all tests pass <https://travis-ci.org/CloudVE/cloudbridge>`_.

2. Increment version number in ``cloudbridge/__init__.py`` as per
   `semver rules <https://semver.org/>`_.

3. Freeze all library dependencies in ``setup.py`` and commit.
   The version numbers can be a range with the upper limit being the latest
   known working version, and the lowest being the last known working version.

   In general, our strategy is to make provider sdk libraries fixed within
   relatively known compatibility ranges, so that we reduce the chances of
   breakage. If someone uses CloudBridge, presumably, they do not use the SDKs
   directly. For all other libraries, especially, general purpose libraries
   (e.g. ``six``), our strategy is to make compatibility as broad and
   unrestricted as possible.

4. Add release notes to ``CHANGELOG.rst``. Also add last commit hash to
   changelog. List of commits can be obtained using
   ``git shortlog <last release hash>..HEAD``

5. Release to PyPi.
   (make sure you have run `pip install wheel`)
   First, test release with PyPI staging server as described in:
   https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/

   Once tested, run:

.. code-block:: bash

   # remove stale files or wheel might package them
   rm -r build dist
   python setup.py sdist upload
   python setup.py bdist_wheel upload

6. Tag release and make a GitHub release.

.. code-block:: bash

   git tag -a v1.0.0 -m "Release 1.0.0"
   git push --tags

7. Increment version number in ``cloudbridge/__init__.py`` to ``version-dev``
   to indicate the development cycle, commit, and push the changes.
