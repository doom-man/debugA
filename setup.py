# -*- coding: UTF-8 -*-

import os
import sys

import setuptools

setuptools.setup(
    name="debugActivity",
    version="1.0.2",
    keywords="Android Debug Activity",
    description="use for jdb to debug android app",
    long_description_content_type="text/markdown",
    long_description=open(
        os.path.join(
            os.path.dirname(__file__),
            "readme.md"
        )
    ).read(),
    author="pareto",
    packages=setuptools.find_packages(),
    license="MIT",
    entry_points={
        'console_scripts': [
            'debugActivity = debugActivity.main:main'
        ]
    }
)

