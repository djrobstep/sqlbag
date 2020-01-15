.PHONY: docs

# test commands and arguments
tcommand = PYTHONPATH=. py.test -x
tmessy = -svv
targs = --cov-report term-missing --cov sqlbag

init: apt pip

apt:
	sudo apt-get install python-dev python3-dev libyaml-dev libmariadbclient-dev

pip:
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt

tox:
	tox tests

test:
	$(tcommand) $(targs) tests

stest:
	$(tcommand) $(tmessy) $(targs) tests

fmt:
	isort -rc .
	black .

clean:
	find . -name \*.pyc -delete
	rm -rf .cache
	rm -rf build dist

lint:
	flake8 sqlbag
	flake8 tests

tidy: clean lint

all: clean lint tox

publish:
	python setup.py sdist bdist_wheel --universal
	twine upload dist/*
