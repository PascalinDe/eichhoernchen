#    This file is part of Eichhörnchen 2.1.
#    Copyright (C) 2019  Carine Dengler
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
import json
import time
import os
import os.path
import curses
import curses.panel

# third party imports
# library specific imports
from src.interpreter import Interpreter, InterpreterError

from src.output_formatter import pprint_prompt
from src.cutils import (
    initialize_colour,
    mk_panel,
    ResizeError,
    WindowManager,
)


def _loop(stdscr, config):
    """Loop through user interaction.

    :param window stdscr: initial window object
    :param dict config: configuration

    :raises: SystemExit when Control+C is pressed
    """
    panel = mk_panel(*stdscr.getmaxyx(), 0, 0)
    window = panel.window()
    window_mgr = WindowManager(window, banner=True)
    interpreter = Interpreter(
        os.path.join(config["database"]["path"], config["database"]["dbname"]),
        {k: json.loads(v) for k, v in config["aliases"].items()}
        if "aliases" in config
        else {},
    )
    while True:
        try:
            y, _ = window.getyx()
            window_mgr.writeline(
                y, 0, pprint_prompt(task=interpreter.timer.task), move=False
            )
            try:
                line = window_mgr.readline(scroll=True)
            except ResizeError:
                window_mgr.reinitialize()
                continue
            if not line:
                window_mgr.mv_down_or_scroll_down()
                continue
            try:
                output = interpreter.interpret_line(line)
            except (InterpreterError, Warning) as exception:
                window_mgr.mv_down_or_scroll_down()
                window_mgr.writeline(
                    *window_mgr.window.getyx(),
                    ((str(exception), curses.color_pair(5)),)
                )
            else:
                window_mgr.mv_down_or_scroll_down()
                window_mgr.writelines(*window_mgr.window.getyx(), output)
        except KeyboardInterrupt:
            window_mgr.mv_down_or_scroll_down()
            window_mgr.writeline(
                *window_mgr.window.getyx(), (("Goodbye!", curses.color_pair(0)),)
            )
            window.refresh()
            time.sleep(0.5)
            raise SystemExit


def launch(stdscr, config):
    """Launch shell.

    :param window stdscr: initial window object
    :param dict config: configuration
    """
    curses.start_color()
    curses.raw()
    curses.use_default_colors()
    initialize_colour()
    _loop(stdscr, config)
