#!/usr/bin/env python

from distutils.core import setup
import os

setup(
    name='pi_k8s_fitches_chore_redis',
    version="0.0.1",
    description="Library for interfacing with chores in Redis",
    package_dir = {'': 'lib'},
    long_description="Library for interfacing with chores in Redis",
    author="Gaffer Fitch",
    author_email="gaffer.fitch@gmail.com",
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6'
    ]
)