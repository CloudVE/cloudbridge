Deferred Modernization Work
===========================

The packaging migration (setup.py → pyproject.toml, drop six, refresh docs)
landed in commits ``7df4a94``..``HEAD``. The items below were identified
during that sweep but deliberately left out because each is large enough
to warrant its own focused PR.

Mechanical Python idiom updates
-------------------------------

Each of these is a near-mechanical refactor with a wide diff. Best done
one-at-a-time so reviewers can read each change as a single transformation.

* **Drop explicit ``object`` base class.** ``class Foo(object):`` →
  ``class Foo:``. No behavior change in Py3.
* **Modernize ``super()`` calls.** ``super(ClassName, self).method(...)`` →
  ``super().method(...)``. The arguments are required only in Py2.
* **Adopt f-strings.** ``"x={0}".format(x)`` and ``"x=%s" % x`` →
  ``f"x={x}"``. Skip for logging calls — those should keep ``%s``
  formatting so the logger can short-circuit when the level is disabled.
* **Switch typing imports to builtins.** ``List[X]`` / ``Dict[K, V]`` /
  ``Optional[X]`` → ``list[X]`` / ``dict[K, V]`` / ``X | None`` once a
  Python 3.10+ floor is acceptable (we already require 3.13, so this is
  safe today).

Lint and tooling
----------------

* **Fix the ~23 pre-existing flake8 import-order errors.** Run
  ``tox -e lint`` to see the list. Mostly ``I100``/``I201``/``I202``
  under ``cloudbridge/providers/azure``, ``gcp``, and ``openstack``.
* **Consider replacing flake8 + flake8-import-order with ruff.** Ruff
  reads ``pyproject.toml``, runs ~100× faster, and covers import
  ordering (``I``) plus most flake8 plugins out of the box.
* **Consider adding mypy / pyright in CI.** The codebase has no type
  hints today; this would be a meaningful uplift, not a one-PR task.

Repository hygiene
------------------

* **Untracked local-dev artifacts at the repo root** — ``azure.txt``,
  ``openstack.txt``, ``docs2/``, ``script_test.py``, ``openstack.log``.
  Each likely belongs in ``.gitignore`` or in a developer's untracked
  workspace; investigate before either committing or deleting.
