#    This file is part of Eichhörnchen 2.0.
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
import time
import os
import os.path
import curses
import curses.panel

# third party imports
# library specific imports
import src.interpreter
import src.output_formatter

from src.cutils import (get_window_pos, init, init_color, mk_panel, readline,
                        scroll_down, writeline)

BANNER = "Welcome to Eichhörnchen.\tType help or ? to list commands."


def _loop(stdscr, config):
    """Loop through user interaction.

    :param window stdscr: window
    :param dict config: configuration
    """
    max_y, max_x = stdscr.getmaxyx()
    nlines, ncols, begin_y, begin_x = get_window_pos(max_y, max_x)
    subpanel = mk_panel(nlines, ncols, begin_y, begin_x)    # noqa
    panel = mk_panel(max_y, max_x, 0, 0)
    window = panel.window()
    window.addstr(0, 0, BANNER)
    curses.panel.update_panels()
    curses.doupdate()
    y = 2
    max_y, max_x = window.getmaxyx()
    interpreter = src.interpreter.Interpreter(
        os.path.join(config["path"], config["database"])
    )
    upper_stack = []
    lower_stack = []
    while True:
        try:
            prompt = src.output_formatter.pprint_prompt(
                task=interpreter.timer.task
            )
            writeline(window, y, 0, prompt)
            line = readline(window, upper_stack, lower_stack, scroll=True)
            if not line:
                if y < max_y-1:
                    y += 1
                else:
                    scroll_down(window, upper_stack, lower_stack)
                continue
            try:
                output = interpreter.interpret_line(line)
                for line in output:
                    if y < max_y-1:
                        y += 1
                    else:
                        scroll_down(window, upper_stack, lower_stack)
                    writeline(window, y, 0, line)
            except Exception as exception:
                window.addstr(
                    y, 0, str(exception), curses.color_pair(5)
                )
            finally:
                y, _ = window.getyx()
                if y < max_y-1:
                    y += 1
                else:
                    scroll_down(window, upper_stack, lower_stack)
        except KeyboardInterrupt:
            if y < max_y-1:
                y += 1
            else:
                scroll_down(window, upper_stack, lower_stack)
            window.addstr(y, 0, "Goodbye!")
            window.refresh()
            time.sleep(0.5)
            raise SystemExit


def launch(window, config):
    """Launch shell.

    :param window window: window
    :param dict config: configuration
    """
    curses.start_color()
    curses.raw()
    curses.use_default_colors()
    init(window)
    init_color()
    _loop(window, config)
