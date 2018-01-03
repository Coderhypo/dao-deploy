#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='dao-deploy',
    version='0.0.2',
    description='DaoCloud Service 2.0 deploy tools',
    author='DaoCloud',
    author_email='hypo.chen@daocloud.io',
    url='http://www.daocloud.io',
    packages=find_packages(),
    install_requires=['requests'],
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)

