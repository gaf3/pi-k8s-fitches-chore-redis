#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name="pi-k8s-fitches-chore-redis",
    version="0.2",
    packages=["pi_k8s_fitches"],
    package_dir={'pi_k8s_fitches':'lib'},
    install_requires=[
        "redis==2.10.6"
    ]
)