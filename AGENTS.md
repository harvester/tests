# AGENTS.md

Harvester test repo: pytest (`harvester_e2e_tests/`) and Robot Framework
(`harvester_robot_tests/`, see its README).

## Python
- flake8, max line length 99 (`tox.ini`). CI runs `tox -e pep8` on the whole repo,
  including `harvester_robot_tests/libs/`.

## Robot Framework
- Layers, never skip one: `tests/**/*.robot` -> `keywords/*.resource` ->
  `libs/keywords/*_keywords.py` -> `libs/<component>/*.py`.
- A `.robot` file only holds its local suite setup/teardown (incl. `Delete Suite
  Resources`). All other keywords belong in `keywords/*.resource` (review rule, PR #2949).
- Suite teardown deletes only the suite's own resources, never the global
  `Cleanup test resources` (breaks parallel runs under pabot).
- Use `Generate Unique Name` for resource names.
- Verify without a cluster: `robot --dryrun <suite>` from `harvester_robot_tests/`
  (use its `venv`).

More: `harvester_robot_tests/README.md`, `.github/COPILOT_INSTRUCTIONS.md`
