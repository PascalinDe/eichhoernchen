#    This file is part of Eichhörnchen 1.2.
#    Copyright (C) 2020  Carine Dengler
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
:synopsis: Curses utils.
"""


# standard library imports
import os
import unicodedata
import curses
import curses.panel

# third party imports
# library specific imports


def get_window_pos(max_y, max_x):
    """Get secondary window position.

    :param int max_y: maximum y position
    :param int max_x: maximum x position

    :returns: number of lines, number of columns and y, x position
    :rtype: int, int, int and int
    """
    nlines = max_y//2
    ncols = max_x//2
    begin_y = (max_y-nlines)//2
    begin_x = (max_x-ncols)//2
    return nlines, ncols, begin_y, begin_x


def resize_panel(max_y, max_x):
    """Resize secondary panel.

    :param int max_y: maximum y position
    :param int max_x: maximum x postition
    """
    panel = curses.panel.bottom_panel()
    window = panel.window()
    nlines, ncols, begin_y, begin_x = get_window_pos(max_y, max_x)
    window.resize(nlines, ncols)
    panel.move(begin_y, begin_x)


def readline(window, boxed=False, prompt="", x=-1, y=-1):
    """Read line.

    :param bool boxed: a box is drawn around the edges of the window
    :param window: window

    :returns: line
    :rtype: str
    """
    if x >= 0:
        if y < 0:
            y, _ = window.getyx()
    elif y >= 0:
        _, x = window.getyx()
    else:
        y, x = window.getyx()
    window.move(y, x)
    _, min_x = window.getyx()
    _, max_x = window.getmaxyx()
    if boxed:
        min_x += 1
        x += 1
        max_x -= 1
    if prompt:
        window.addstr(y, x, prompt)
    min_x += len(prompt)
    i = 0
    buffer = []
    while True:
        y, x = window.getyx()
        char = window.get_wch()
        if char == curses.KEY_RESIZE:
            max_y, max_x = window.getmaxyx()
            resize_panel(max_y, max_x)
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
                if i < len(buffer):
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
        if boxed:
            window.box()
    return "".join(buffer).strip()


def writeline(window, y, x, multi_part_line):
    """Write multi-part line.

    :param window: window
    :param int y: y
    :param int x: x
    :param tuple multi_part_line: multi-part line
    """
    for line, attr in multi_part_line:
        window.addstr(y, x, line, attr)
        x += len(line)


def mk_panel(nlines, ncols, begin_y, begin_x):
    """Make panel.

    :param int nlines: number of lines
    :param int ncols: number of columns
    :param int begin_y: y position of window
    :param int begin_x: x position of window

    :returns: panel
    :rtype: panel
    """
    window = curses.newwin(nlines, ncols, begin_y, begin_x)
    init(window)
    panel = curses.panel.new_panel(window)
    return panel


def mv_front():
    """Move background window to front.

    :returns: window
    :rtype: window
    """
    panel = curses.panel.bottom_panel()
    window = panel.window()
    panel.top()
    curses.panel.update_panels()
    curses.doupdate()
    return window


def mv_back():
    """Move foreground window to back."""
    panel = curses.panel.top_panel()
    panel.bottom()
    curses.panel.update_panels()
    curses.doupdate()


def display_choices(choices):
    """Display choices.

    :param list choices: choices

    :returns: choice
    :rtype: int
    """
    if len(choices) == 1:
        return 0
    window = mv_front()
    window.clear()
    window.box()
    y, _ = window.getyx()
    y += 1
    x = 1
    max_y, max_x = window.getmaxyx()
    window.addstr(y, x, f"Pick choice 1...{len(choices)}.")
    if y < max_y-1:
        y += 1
    else:
        window.scroll()
    for i, choice in enumerate(choices, start=1):
        window.addstr(y, x, f"{i}: {choice}")
        y, _ = window.getyx()
        if y < max_y-1:
            y += 1
        else:
            window.scroll()
    char = ""
    while char not in (str(i) for i in range(1, len(choices)+1)):
        char = window.get_wch()
    window.clear()
    mv_back()
    return int(char)-1


def init_color():
    """Initialize colours."""
    curses.init_pair(1, 2, -1)      # name
    curses.init_pair(2, 8, -1)      # tags
    curses.init_pair(3, 5, -1)      # time span
    curses.init_pair(4, 11, -1)     # total
    curses.init_pair(5, 9, -1)      # error


def init(window):
    """Initialize shell.

    :param window window: window
    """
    window.clear()
    window.idlok(True)
    window.keypad(True)
    window.scrollok(True)
