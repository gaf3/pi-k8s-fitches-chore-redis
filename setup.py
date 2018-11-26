#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name="pi_k8s_fitches.chore_redis",
    version="0.1",
    packages=["pi_k8s_fitches.chores_redis"],
    package_dir={'pi_k8s_fitches':'lib'},
    install_requires=[
        "redis==2.10.6"
    ]
)