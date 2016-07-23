.PHONY: docs

# test commands and arguments
tcommand = PYTHONPATH=. py.test -x
tmessy = -svv
targs = --cov-report term-missing --cov sqlbag

init: apt pip

apt:
	sudo apt-get install python-dev python3-dev libyaml-dev libmariadbclient-dev

pip:
	pip install -r requirements-dev.txt

pipupgrade:
	pip install --upgrade pip
	pip install --upgrade -r requirements-dev.txt

pipreqs:
	pip install -r requirements.txt

pipeditable:
	pip install -e .

tox:
	tox tests

test:
	$(tcommand) $(targs) tests

stest:
	$(tcommand) $(tmessy) $(targs) tests

clean:
	git clean -fXd
	find . -name \*.pyc -delete


fmt:
	yapf --recursive --in-place sqlbag
	yapf --recursive --in-place tests


lint:
	flake8 sqlbag
	flake8 tests


docs:
	cd docs && make clean && make html

opendocs:
	BROWSER=firefox python -c 'import os;import webbrowser;webbrowser.open_new_tab("file://" + os.getcwd() + "/docs/_build/html/index.html")'


tidy: clean fmt lint


all: clean fmt lint tox
