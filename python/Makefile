.PHONY: update test test-flake8 test-pytest clean publish

all:

update upgrade:
	python -m pip install --upgrade poetry
	poetry update

clean:
	@rm -rf trex_imager_readfile.egg-info build dist

test: test-flake8 test-pytest

test-flake8 flake8:
	poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	poetry run flake8 . --count --ignore=W391 --max-complexity=30 --max-line-length=127 --statistics
	
test-pytest pytest:
	poetry run pytest

publish:
	${MAKE} test
	poetry build
	poetry publish
	${MAKE} clean
