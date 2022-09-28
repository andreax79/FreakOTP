SHELL=/bin/bash -e

help:
	@echo - make black ------ Format code
	@echo - make clean ------ Clean virtual environment
	@echo - make coverage --- Run tests coverage
	@echo - make lint ------- Run lint
	@echo - make test ------- Run test
	@echo - make venv ------- Create virtual environment

black:
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
	python3 -m virtualenv .
	. bin/activate; pip install -Ur requirements.txt
	. bin/activate; pip install -Ur requirements-dev.txt
