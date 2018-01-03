#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='dao-deploy',
    version='0.01',
    description='DaoCloud Service 2.0 deploy tools',
    author='DaoCloud',
    author_email='hypo.chen@daocloud.io',
    url='http://www.daocloud.io',
    packages=find_packages(),
    install_requires=['requests'],
)
