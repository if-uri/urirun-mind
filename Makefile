.PHONY: install test doctor-test doctor-health check clean

PY ?= python

install:
	pip install -e .
	pip install pytest

doctor-test:
	$(PY) -m pytest tests -v

doctor-health:
	$(PY) -c "import urirun_mind"

test: doctor-test

check: test

clean:
	rm -rf build dist *.egg-info .pytest_cache

all: check
