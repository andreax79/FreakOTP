#!/usr/bin/env python3

from pathlib import Path
from setuptools import setup, find_packages
from freakotp.cli import __version__

requires = Path(__file__).parent / 'requirements.txt'
install_requires = [line.rstrip() for line in requires.read_text().split("\n") if line.strip()]

description = 'FreakOTP is a command line two-factor authentication application.'

setup(
    name='freakotp',
    version=__version__,
    description=description,
    long_description=description,
    url='https://github.com/andreax79/FreakOTP',
    author='Andrea Bonomi',
    author_email='andrea.bonomi@gmail.com',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: Public Domain',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    zip_safe=True,
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup', 'examples']),
    keywords='otp freeotp cli',
    py_modules=['freakotp'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'freakotp=freakotp:main',
        ],
    },
    test_suite='tests',
    tests_require=['pytest'],
)
