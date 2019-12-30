#    This file is part of Eichhörnchen 1.2.
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
import curses
import unicodedata
import os
import os.path

# third party imports
# library specific imports
import src.interpreter
import src.output_formatter

BANNER = "Welcome to Eichhörnchen.\tType help or ? to list commands."


def _readline(window):
    """Read line.

    :param window: window

    :returns: line
    :rtype: str
    """
    _, min_x = window.getyx()
    _, max_x = window.getmaxyx()
    i = 0
    buffer = []
    while True:
        y, x = window.getyx()
        char = window.get_wch()
        if char == curses.KEY_RESIZE:
            _, max_x = window.getmaxyx()
            continue
        if char in (curses.KEY_ENTER, os.linesep):
            break
        if char in (curses.KEY_DOWN, curses.KEY_UP):
            continue
        if char == curses.KEY_LEFT:
            if x > min_x:
                i -= 1
                window.move(y, x-1)
                continue
            if len(buffer) > 0 and i > 0:
                i -= 1
                window.insch(y, x, buffer[i])
                continue
        if char == curses.KEY_RIGHT:
            if x < max_x-1:
                i += 1
                window.move(y, x+1)
                continue
            if i < len(buffer)-1:
                window.delch(y, min_x)
                i += 1
                window.insch(y, x, buffer[i])
                continue
            if window.instr(y, x).decode(encoding="utf-8") == buffer[-1]:
                window.delch(y, min_x)
                i += 1
                window.move(y, x)
                continue
        if char in (curses.KEY_BACKSPACE, 8, 127):
            if x > min_x:
                i -= 1
                x -= 1
                buffer.pop(i)
                window.delch(y, x)
                if len(buffer) > max_x-(min_x+2) and i >= x-1:
                    window.insch(y, min_x, buffer[(i-x)+1])
                    window.move(y, x+1)
            continue
        if isinstance(char, int):
            continue
        if unicodedata.category(char).startswith("C"):
            continue
        buffer.insert(i, char)
        i += 1
        if x < max_x-1:
            x += 1
        else:
            window.delch(y, min_x)
            window.move(y, x-1)
        window.insch(char)
        window.move(y, x)
    return "".join(buffer).strip()


def _loop(window, config):
    """Loop through user interaction.

    :param window window: window
    :param dict config: configuration
    """
    y = 2
    max_y, max_x = window.getmaxyx()
    interpreter = src.interpreter.Interpreter(
        os.path.join(config["path"], config["database"])
    )
    while True:
        try:
            prompt = src.output_formatter.pprint_prompt(task=None)
            window.addnstr(y, 0, prompt, max_x)
            window.move(y, len(prompt)+1)
            line = _readline(window)
            if not line:
                if y < max_y-1:
                    y += 1
                else:
                    window.scroll()
                continue
            try:
                output = interpreter.interpret_line(line)
                for line in output:
                    if y < max_y-1:
                        y += 1
                    else:
                        window.scroll()
                    window.addnstr(y, 0, output, max_x)
            except Exception as exception:
                window.addnstr(y, 0, str(exception), max_x)
            finally:
                y, _ = window.getyx()
                if y < max_y-1:
                    y += 1
                else:
                    window.scroll()
        except KeyboardInterrupt:
            if y < max_y-1:
                y += 1
            else:
                window.scroll()
            window.addnstr(y, 0, "Goodbye!", max_x)
            window.refresh()
            time.sleep(0.5)
            raise SystemExit


def _init(window):
    """Initialize shell.

    :param window window: window
    """
    window.clear()
    window.idlok(True)
    window.keypad(True)
    window.scrollok(True)
    window.addstr(0, 0, BANNER)
    window.refresh()


def launch(window, config):
    """Launch shell.

    :param window window: window
    :param dict config: configuration
    """
    curses.start_color()
    curses.cbreak()
    _init(window)
    _loop(window, config)
