.PHONY: install test check clean

install:
	pip install -e .
	pip install pytest

test:
	python -m pytest tests -v

check: test

clean:
	rm -rf build dist *.egg-info .pytest_cache

all: check
