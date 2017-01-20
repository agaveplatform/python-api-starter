#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools.command.test import test as TestCommand

import os
import sys


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--ignore', 'build']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.md').read()
requires = [pkg for pkg in open('requirements.txt').readlines()]

setup(
    name='agaveflask',
    version='0.2.0',
    description='Common package for authoring Agave services in flask/Flask-RESTful',
    long_description=readme,
    author='Joe Stubbs',
    author_email='jstubbs@tacc.utexas.edu',
    url='https://bitbucket.org/agaveapi/agaveflask',
    packages=[
        'agaveflask',
    ],
    package_dir={'agaveflask': 'agaveflask'},
    data_files=[('', ['requirements.txt'], ['README.md'])],
    include_package_data=True,
    install_requires=requires,
    license="BSD",
    zip_safe=False,
    keywords='',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    cmdclass={'test': PyTest},
    tests_require=['pytest'],
    test_suite='tests',
)
