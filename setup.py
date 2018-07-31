# -*- coding: utf-8 -*-
"""
smd setup script.
"""

import re

from setuptools import find_packages, setup

<<<<<<< HEAD
<<<<<<< HEAD
setuptools.setup(
    name="smd",
    # WARNING: careful with this, if smd imports stuff from install_requires:
    version=smd.__version__,
    author="adbenitez",
    author_email="asieldbenitez@gmail.com",
    description="Simple Manga Downloader",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://adbenitez.github.io/smd",
=======
=======
>>>>>>> 1.6.0
with open('README.rst', 'rt', encoding='utf8') as fh:
    README = fh.read()

with open('smd/__init__.py', 'rt', encoding='utf8') as fh:
    VERSION = re.search(r'__version__ = \'(.*?)\'', fh.read(), re.M).group(1)

setup(
    name='smd',
    version=VERSION,
    license='GPL3+',
    author='adbenitez',
    author_email='asieldbenitez@gmail.com',
    description='Simple Manga Downloader, a tool to search and download manga for offline reading',
    long_description=README,
    long_description_content_type='text/x-rst',
    url='https://adbenitez.github.io/smd',
<<<<<<< HEAD
>>>>>>> 1.6.0
=======
>>>>>>> 1.6.0
    classifiers=(
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
<<<<<<< HEAD
<<<<<<< HEAD
        "Development Status :: 5 - Production/Stable",
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
    keywords="manga downloader web scraping crawler spider internet desktop app",
    project_urls={
        # 'Documentation': 'comming soon',
=======
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Games/Entertainment',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Utilities'
    ),
    keywords='download manga downloader web scraping crawler spider internet desktop app offline reading',
    project_urls={
        'Documentation': 'http://smd.readthedocs.io',
>>>>>>> 1.6.0
=======
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Games/Entertainment',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Utilities'
    ),
    keywords='download manga downloader web scraping crawler spider internet desktop app offline reading',
    project_urls={
        'Documentation': 'http://smd.readthedocs.io',
>>>>>>> 1.6.0
        'Donate': 'http://liberapay.com/adbenitez',
        'Say Thanks!': 'http://mastodon.social/@adbenitez',
        'Source': 'https://github.com/adbenitez/smd',
        'Tracker': 'https://github.com/adbenitez/smd/issues',
    },
    packages=find_packages(exclude=('tests*', 'docs')),
    install_requires=['beautifulsoup4'],
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'smd=smd:main',
        ],
    },
    include_package_data=True,
    package_data={
        'smd': ['locale']
    }
)
