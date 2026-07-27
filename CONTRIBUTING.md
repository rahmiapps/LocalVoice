# Contributing to LocalVoice

Thank you for helping improve LocalVoice.

## Before opening an issue

- Search existing issues first.
- Use the latest available version.
- Include the operating system, LocalVoice version and exact reproduction steps.
- Remove personal text, audio and paths from screenshots or logs.

## Development setup

1. Fork and clone the repository.
2. Use Python 3.12.
3. Create a virtual environment.
4. Install runtime and build dependencies.
5. Run the test suite before submitting a pull request.

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-build.txt
python -m pytest
```

Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-build.txt
python -m pytest
```

## Pull requests

- Keep changes focused.
- Add or update tests for behavior changes.
- Update translations when adding user-visible text.
- Do not add cloud telemetry, paid APIs, advertising or mandatory accounts.
- Do not commit model files, build outputs, user data, secrets or virtual environments.
- Explain security and privacy implications where relevant.

## Coding style

- Prefer clear, typed Python.
- Handle platform-specific behavior explicitly.
- Keep all normal dictation paths offline.
- Avoid silent fallbacks that change privacy or language behavior.
