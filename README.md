# Aioniser

A tool for triggering things in cycles.



## Dev setup

Install a venv; then...

```
PYENV_VERSION=3.9.6 python -m venv .venv && source .venv/bin/activate
pip install -U pip setuptools
pip install pip-tools
pip-sync requirements.txt requirements-dev.txt
pip install -e .
pre-commit install --install-hooks
```
