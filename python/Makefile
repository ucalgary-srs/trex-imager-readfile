.PHONY: install update test test-linting test-ruff test-pycodestyle test-pytest clean publish

all:

poetry:
	python -m pip install poetry

install: poetry
	poetry install

update upgrade:
	python -m pip install --upgrade poetry
	poetry update

clean:
	@rm -rf trex_imager_readfile.egg-info build dist

test: test-linting

test-linting: test-ruff test-pycodestyle

test-ruff ruff:
	@printf "Running ruff tests\n+++++++++++++++++++++++++++\n"
	ruff check --respect-gitignore trex_imager_readfile
	ruff check --respect-gitignore tests
	ruff check --respect-gitignore tools
	@printf "\n\n"

test-pycodestyle:
	@printf "Running pycodestyle tests\n+++++++++++++++++++++++++++\n"
	pycodestyle --config=.pycodestyle trex_imager_readfile
	pycodestyle --config=.pycodestyle tests
	pycodestyle --config=.pycodestyle tools
	@printf "\n\n"
	
test-pytest pytest:
	pytest -n 2 --maxfail=1

publish:
	${MAKE} test
	poetry build
	poetry publish
	${MAKE} clean
