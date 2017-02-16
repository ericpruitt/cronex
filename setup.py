try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import subprocess

# If pandoc is available, convert the markdown README to REstructured Text.
try:
    pandoc = subprocess.Popen(["pandoc", "-t", "rst", "README.md"],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    long_description, _ = pandoc.communicate()
except OSError:
    long_description = None

setup(
    name="cronex",
    version="0.1.1",
    description=("This module provides an easy to use interface for cron-like"
                 " task scheduling."),
    author="Eric Pruitt",
    author_email="eric.pruitt@gmail.com",
    url="https://github.com/ericpruitt/cronex",
    license="MIT",
    keywords=["cron", "scheduler", "triggers", "time", "quartz"],
    packages=["cronex"],
    long_description=long_description,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.4",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
    ],
)
