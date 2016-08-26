#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
from setuptools import setup, find_packages


def setup_package():
    setup(name='httsleep',
          description='A python library for polling HTTP endpoints - batteries included!',
          author='Aengus Walton',
          author_email='ventolin@gmail.com',
          url='https://github.com/kopf/httsleep',
          packages=find_packages(exclude=['tests', 'test']),
          classifiers=[
              'Development Status :: 4 - Beta',
              'Programming Language :: Python',
              'Programming Language :: Python :: 2.7',
              'Programming Language :: Python :: 3.4',
              'Programming Language :: Python :: 3.5'
          ],
          zip_safe=False,
          include_package_data=True,
          setup_requires=['setuptools_scm'],
          install_requires=['requests', 'jsonpath-rw'],
          use_scm_version=True)


if __name__ == "__main__":
    setup_package()
