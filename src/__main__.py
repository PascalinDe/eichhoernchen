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

from pathlib import Path

# third party imports

# library specific imports
import src.config

from src import METADATA
from src.curses import get_panel, loop, WindowManager
from src.interpreter.interpreter import Interpreter


def _config(config):
    """Configuration file to load.

    :param str config: path to configuration file to load

    :returns: config
    :rtype: path to configuration file to load
    """
    if not Path(config).is_file():
        raise argparse.ArgumentTypeError(f"No such file {config}")
    return config


def launch(stdscr, config):
    """Launch shell.

    :param window stdscr: whole screen
    :param dict config: configuration
    """
    interpreter = Interpreter(config)
    window = get_panel(*stdscr.getmaxyx(), 0, 0).window()
    window_mgr = WindowManager(
        window,
        banner="Welcome to Eichhörnchen.\tType help or ? to list commands.",
        commands=(),
        tags=interpreter.timer.tags,
    )
    curses.start_color()
    curses.raw()
    curses.use_default_colors()
    for color_pair in (
        (1, 2, -1),  # name
        (2, 8, -1),  # tags
        (3, 5, -1),  # time span
        (4, 11, -1),  # total runtime
        (5, 9, -1),  # error message
    ):
        curses.init_pair(*color_pair)
    loop(interpreter, window_mgr)


def main():
    """Main function."""
    logging.basicConfig(
        filename=f"/tmp/{METADATA['name']}.log",
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        level=logging.DEBUG,
    )
    logger = logging.getLogger(main.__name__)
    parser = argparse.ArgumentParser(
        prog=METADATA["name"],
        description=METADATA["description"],
    )
    parser.add_argument(
        "-c",
        "--config",
        type=_config,
        help="path to configuration file to load",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {METADATA['version']}",
        help="print %(prog)s version",
    )
    try:
        curses.wrapper(
            launch,
            src.config.load_config(path=parser.parse_args().config),
        )
    except Exception as exception:
        logger.exception(exception)
        raise SystemExit("an unexpected error occurred")


main()
