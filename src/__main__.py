#    Eichhörnchen 2.2
#    Copyright (C) 2018-2021  Carine Dengler
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
:synopsis: Main function.
"""


# standard library imports
import curses
import logging
import argparse

# third party imports

# library specific imports
import src.config
import src.curses.shell

from src import __version__, description


def main():
    """Main function."""
    prog = "eichhoernchen"
    logging.basicConfig(
        filename=f"/tmp/{prog}.log",
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        level=logging.DEBUG,
    )
    logger = logging.getLogger(main.__name__)
    parser = argparse.ArgumentParser(
        prog=prog,
        description=description,
    )
    parser.add_argument("-c", "--config", help="path to config file to load")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    try:
        curses.wrapper(
            src.curses.shell.launch,
            src.config.load_config(path=parser.parse_args().config),
        )
    except Exception as exception:
        logger.exception(exception)
        raise SystemExit("an unexpected error occurred")


main()
