# Agent rules (Codex)

- Do not modify tests to “pass” when dependencies are missing.
- If an import fails, fix dependency installation / declarations (requirements, pyproject, setup), not tests.
- CI must stay strict: no conditional skipping for missing core deps.
- Tests must run from a clean environment without doing network installs during the test phase.
- If dependencies change, update the environment setup / lockfiles accordingly.
