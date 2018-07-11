# -*- coding: utf-8 -*-
import setuptools

import smd

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="smd",
    # careful with this, if smd imports stuff from install_requires:
    version=smd.__version__,
    author="adbenitez",
    author_email="asieldbenitez@gmail.com",
    description="Simple Manga Downloader",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adbenitez/smd",
    classifiers=(
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities"
    ),
    keywords="manga downloader crawler desktop app internet web",
    project_urls={
        # 'Documentation': 'https://github.com/adbenitez/smd',
        'Funding': 'http://liberapay.com/adbenitez',
        'Say Thanks!': 'http://mastodon.social/@adbenitez',
        'Source': 'https://github.com/adbenitez/smd',
        'Tracker': 'https://github.com/adbenitez/smd/issues',
    },
    packages=setuptools.find_packages(),
    install_requires=['beautifulsoup4'],
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'smd=smd:main',
        ],
    },
)
