Release Process
~~~~~~~~~~~~~~~~~

CloudBridge is published to PyPI automatically by the `deploy workflow
<https://github.com/CloudVE/cloudbridge/blob/main/.github/workflows/deploy.yaml>`_
using PyPI `trusted publishing <https://docs.pypi.org/trusted-publishers/>`_
(OIDC). There is no stored API token and no manual ``twine upload`` step. Two
events drive the workflow:

* **Pushing a tag** (e.g. ``v4.1.0``) builds the distributions and publishes
  them to **TestPyPI** (already-uploaded files are skipped).
* **Publishing a GitHub Release** for that tag publishes the distributions to
  **production PyPI**.

Because the ``release`` event reads the workflow definition from the commit the
tag points to, always create the tag on a commit that already contains the
current ``deploy.yaml``.

1. Make sure all tests pass on the `GitHub Actions workflows
   <https://github.com/CloudVE/cloudbridge/actions>`_.

2. Increment the version number in ``cloudbridge/__init__.py`` as per
   `semver rules <https://semver.org/>`_.

3. Freeze all library dependencies in ``pyproject.toml`` and commit.
   The version numbers can be a range with the upper limit being the latest
   known working version, and the lowest being the last known working version.

   In general, our strategy is to make provider sdk libraries fixed within
   relatively known compatibility ranges, so that we reduce the chances of
   breakage. If someone uses CloudBridge, presumably, they do not use the SDKs
   directly. For all other general purpose libraries, our strategy is to make
   compatibility as broad and unrestricted as possible.

4. Add release notes to ``CHANGELOG.rst``. Also add the last commit hash to the
   changelog. The list of commits can be obtained using
   ``git shortlog <last release hash>..HEAD``.

5. Commit the version bump and changelog, and push to ``main``.

.. code-block:: bash

   git commit -am "Release 4.1.0"
   git push origin main

6. Tag the release commit and push the tag. This triggers the deploy workflow,
   which publishes to TestPyPI. Optionally verify the staged release at
   https://test.pypi.org/project/cloudbridge/ before continuing.

.. code-block:: bash

   git tag -a v4.1.0 -m "Release 4.1.0"
   git push origin v4.1.0

7. Create a GitHub Release for the tag. Publishing the release triggers the
   deploy workflow, which publishes to production PyPI. Confirm the upload at
   https://pypi.org/project/cloudbridge/.

.. code-block:: bash

   gh release create v4.1.0 --title "4.1.0" --notes-file <release-notes>
