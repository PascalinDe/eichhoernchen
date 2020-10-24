#    Eichhörnchen 2.1
#    Copyright (C) 2018-2019  Carine Dengler
#
#    This program is free software: you can redistribute it and/or modify
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


"""
:synopsis: Eichhörnchen 2.0.
"""


# standard library imports
import curses
import argparse

# third party imports

# library specific imports
import src.config
import src.cshell

__version__ = "2.1"


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        prog="eichhoernchen", description="Lightweight curses-based time tracking tool."
    )
    parser.add_argument("-c", "--config", help="use this configuration file")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    config = src.config.load_config(path=parser.parse_args().config)
    try:
        curses.wrapper(src.cshell.launch, config)
    except Exception as exception:
        print(exception)


main()
