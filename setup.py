#    This file is part of Eichhörnchen 2.2.
#    Copyright (C) 2018-2021  Carine Dengler
#
#    Eichhörnchen is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


# standard library imports
from setuptools import setup

# third party imports
# library specific imports


__version__ = "2.2"


with open("README.md") as fp:
    long_description = fp.read()


setup(
    name="eichhoernchen",
    version=__version__,
    description="Lightweight curses-based time tracking tool.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Carine Dengler",
    author_email="eichhoernchen@pascalin.de",
    url="https://github.com/pascalinde/eichhoernchen",
    packages=["src"],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={"console_scripts": ["eichhoernchen = src.__main__:main"]},
)
