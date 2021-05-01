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
import json
import time
import os
import os.path
import curses
import curses.panel

# third party imports
# library specific imports
from src.interpreter.main_interpreter import Interpreter
from src.interpreter.interpreter_mixin import InterpreterError
from src.output_formatter import pprint_prompt
from src.curses.utils import get_panel, ResizeError, WindowManager


def _loop(stdscr, config):
    """Loop through user interaction.

    :param window stdscr: initial window object
    :param dict config: configuration

    :raises: SystemExit when Control+C is pressed
    """
    aliases = (
        {k: json.loads(v) for k, v in config["aliases"].items()}
        if "aliases" in config
        else {}
    )
    interpreter = Interpreter(
        os.path.join(config["database"]["path"], config["database"]["dbname"]), aliases
    )
    panel = get_panel(*stdscr.getmaxyx(), 0, 0)
    window = panel.window()
    window_mgr = WindowManager(
        window,
        banner="Welcome to Eichhörnchen.\tType help or ? to list commands.",
        commands=(*aliases.keys(), *interpreter.subcommands.keys()),
    )
    history = []
    while True:
        try:
            try:
                line = window_mgr.readline(
                    history,
                    prompt=pprint_prompt(task=interpreter.timer.task),
                    scroll=True,
                )
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
                history.append(line)
        except (EOFError, KeyboardInterrupt):
            if interpreter.timer.task.name:
                interpreter.timer.stop()
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
    for colour_pair in (
        (1, 2, -1),  # name
        (2, 8, -1),  # tag(s)
        (3, 5, -1),  # time span
        (4, 11, -1),  # total
        (5, 9, -1),  # error
    ):
        curses.init_pair(*colour_pair)
    _loop(stdscr, config)
