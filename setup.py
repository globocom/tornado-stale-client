#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of tornado-stale-client.
# https://github.com/globocom/tornado-stale-client

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2016, Globo.com <backstage@corp.globo.com>

from setuptools import find_packages, setup

setup(
    name='tornado-stale-client',
    version='0.1.3',
    description='An async http client for tornado with stale cache support',
    long_description='',
    keywords='tornado async http client redis stale cache',
    author='Globo.com',
    author_email='backstage@corp.globo.com',
    url='https://github.com/globocom/tornado-stale-client',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.4',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'tornado',
        'smart-sentinel>=0.2.0',
    ],
)
