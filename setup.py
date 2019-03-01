#!/usr/bin/env python3

import os
import os.path
import codecs
from setuptools import setup
from freakotp import __version__

d = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(d, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = 'freakotp',
    version = __version__,
    description = 'FreakOTP is a command line two-factor authentication application. Tokens can be imported from FreeOTP.',
    long_description = long_description,
    url = 'https://github.com/andreax79/FreakOTP',
    author = 'Andrea Bonomi',
    author_email = 'andrea.bonomi@gmail.com',
    license = 'MIT',
    classifiers = [
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: Public Domain',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        ],
    zip_safe=True,
    include_package_data=True,
    keywords = 'otp freeotp cli',
    py_modules=[ 'freakotp' ],
    install_requires = [],
    entry_points = {
        'console_scripts': [
            'freakotp=freakotp:main',
            ],
        }
    )
