PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
PYINSTALLER := $(VENV)/bin/pyinstaller

.PHONY: venv install run check build clean

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_PIP) install -r requirements-dev.txt

run:
	$(VENV_PYTHON) logitech_webcam_app.py

check:
	$(VENV_PYTHON) -m py_compile logitech_webcam_app.py

build:
	$(PYINSTALLER) --noconfirm webcam_app.spec

clean:
	rm -rf build dist __pycache__
