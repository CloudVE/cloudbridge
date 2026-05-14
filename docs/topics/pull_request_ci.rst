Pull request CI and security gates
==================================
Two CI workflows run on pull requests, with different trust levels:

.. list-table::
   :header-rows: 1
   :widths: 25 25 20 30

   * - Workflow
     - Trigger
     - Runs on forks?
     - Secrets exposed
   * - ``Lint and mock tests`` (``integration.yaml``)
     - every PR / push
     - yes, always
     - none
   * - ``Cloud integration tests`` (``integration-cloud.yaml``)
     - ``safe-to-test`` label, push to ``main``, manual dispatch
     - only after maintainer approval
     - AWS / Azure / GCP / OpenStack

Fork PRs always get lint + mock feedback automatically. Cloud integration
tests are gated behind maintainer review because they run untrusted PR code
with access to live cloud credentials.


For maintainers: applying ``safe-to-test``
------------------------------------------
Cloud integration runs against PRs are gated by the ``safe-to-test`` label.
**Adding this label is equivalent to authorising arbitrary code execution
against our cloud accounts.** Before applying it on a PR from a fork, audit
the diff for anything that runs at install or test time:

* ``setup.py`` / ``setup.cfg`` / ``pyproject.toml`` — any new ``cmdclass``,
  ``entry_points``, post-install hooks, or ``extras_require`` entries that
  pull in unfamiliar packages?
* ``tox.ini`` — any new env definitions, ``commands`` overrides, or
  ``setenv`` injections?
* ``conftest.py`` and any ``__init__.py`` under ``tests/`` — these run on
  pytest startup before fixtures even decide to run.
* New files anywhere under ``.github/`` — workflow tampering.
* Any new test that does outbound network IO outside the expected cloud
  APIs (e.g., raw ``requests.post`` to an arbitrary URL).
* Any change under ``cloudbridge/`` that calls ``subprocess``, ``os.system``,
  ``eval``, ``exec``, or writes to disk outside the test working tree.

After labeling, the workflow queues and stops at the ``cloud-integration``
environment gate — you will get a second prompt to approve the actual run.
Treat that as a sanity check, not the primary defence; the label was the
real authorisation moment.

If the PR is updated after labeling, the label is automatically removed by
``pr-label-strip.yaml``. To re-test, re-audit the new diff before
re-applying.


One-time repo setup
-------------------
If you are setting up CI from scratch on a fork or new repo, these one-time
configurations are required:


``safe-to-test`` label
~~~~~~~~~~~~~~~~~~~~~~
Create the label in the repo's Issues → Labels page. Any colour. Restrict
label management to maintainers (default for org-owned repos).


``cloud-integration`` environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Repo Settings → Environments → New environment → name it
   ``cloud-integration``.
2. Under **Required reviewers**, add the maintainer team or users who are
   allowed to approve cloud-integration runs.
3. Under **Deployment branches**, select **Selected branches** and add
   ``main`` (the workflow only ever runs from base context).
4. The environment does not need any environment-scoped secrets — all
   secrets live at the repo level.


AWS OIDC role
~~~~~~~~~~~~~
See ``.github/aws/setup.sh``. The role's trust policy
(``.github/aws/trust-policy.json``) accepts two sub claims:

* ``repo:CloudVE/cloudbridge:ref:refs/heads/main`` — push-to-main runs.
* ``repo:CloudVE/cloudbridge:environment:cloud-integration`` — PR runs that
  reached the protected environment. Fork PRs that do not reach the
  environment cannot assume this role.

The repo secret ``AWS_OIDC_ROLE_ARN`` must be set to the role ARN printed by
``setup.sh``.
