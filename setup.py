#!/usr/bin/env python

import io

from setuptools import setup, find_packages

with io.open('README.rst') as f:
    readme = f.read()

setup(
    name='sqlbag',
    version='0.1.1487916199',
    url='https://github.com/djrobstep/sqlbag',
    description='various snippets of SQL-related boilerplate',
    long_description=readme,
    author='Robert Lechte',
    author_email='robertlechte@gmail.com',
    install_requires=[
        'pathlib',
        'six',
        'sqlalchemy'
    ],
    zip_safe=False,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha'
    ],
    extras_require = {
        'pg': ['psycopg2'],
        'maria': ['pymysql']
    }
)
