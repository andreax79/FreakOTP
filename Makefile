SHELL=/bin/bash -e

help:
	@echo - make black ----------- Format code
	@echo - make isort ----------- Sort imports
	@echo - make clean ----------- Clean virtual environment
	@echo - make coverage -------- Run tests coverage
	@echo - make lint ------------ Run lint
	@echo - make readme-preview -- Readme preview
	@echo - make test ------------ Run test
	@echo - make venv ------------ Create virtual environment

isort:
	isort --profile black freakotp freakotp.py tests setup.py

black: isort
	black -S freakotp freakotp.py tests setup.py

clean:
	-rm -rf build dist
	-rm -rf *.egg-info
	-rm -rf bin lib share pyvenv.cfg

coverage:
	pytest --cov --cov-report=term-missing

lint:
	flake8 freakotp.py freakotp tests

test:
	pytest

typecheck:
	mypy --strict --no-warn-unused-ignores freakotp

venv:
	python3 -m virtualenv . || python3 -m venv .
	. bin/activate; pip install -Ur requirements.txt
	. bin/activate; pip install -Ur requirements-dev.txt

readme-preview:
	@. bin/activate; grip 0.0.0.0:8080
