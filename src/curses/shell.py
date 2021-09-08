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


"""
:synopsis: Curses-based shell.
"""


# standard library imports
import curses
import curses.panel

# third party imports
# library specific imports
from src.interpreter.interpreter import Interpreter
from src.curses import get_panel, WindowManager, loop


def launch(stdscr, config):
    """Launch shell.

    :param window stdscr: initial window object
    :param dict config: configuration
    """
    interpreter = Interpreter(config)
    panel = get_panel(*stdscr.getmaxyx(), 0, 0)
    window = panel.window()
    window_mgr = WindowManager(
        window,
        banner="Welcome to Eichhörnchen.\tType help or ? to list commands.",
        commands=(*interpreter.aliases.keys(), *interpreter.subcommands.keys()),
        tags=interpreter.timer.tags,
    )
    curses.start_color()
    curses.raw()
    curses.use_default_colors()
    for colour_pair in (
        (1, 2, -1),  # name
        (2, 8, -1),  # tag(s)
        (3, 5, -1),  # time span
        (4, 11, -1),  # total
        (5, 9, -1),  # error
    ):
        curses.init_pair(*colour_pair)
    loop(interpreter, window_mgr)
