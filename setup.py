#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    findmodules
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='tddtags',
    version='0.1.1',
    description="Declare unit tests as tags within docstrings",
    long_description=readme + '\n\n' + history,
    author="Curtis Forrester",
    author_email='curtis@bredbeddle.net',
    url='https://github.com/curtisforrester/tddtags',
    packages=[
        'tddtags',
    ],
    package_dir={'tddtags':
                 'tddtags'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='tddtags',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
