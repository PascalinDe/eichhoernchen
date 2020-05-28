#    This file is part of Eichhörnchen 2.0.
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


def scroll_up(window, upper_stack, lower_stack, boxed=False):
    """Scroll up.

    :param window window: window
    :param list upper_stack: stack (upper window)
    :param list lower_stack: stack (lower window)
    """
    if not upper_stack:
        # top of the window
        return
    y, x = window.getyx()
    max_y, _ = window.getmaxyx()
    if boxed:
        min_y = 1
        max_y -= 1
        min_x = 1
    else:
        min_y = 0
        min_x = 0
    lower_stack.append(scrapeline(window, max_y-1))
    window.scroll(-1)
    writeline(window, min_y, 0, upper_stack.pop())
    window.move(max_y-1, min_x)


def scroll_down(window, upper_stack, lower_stack, boxed=False):
    """Scroll down.

    :param window window: window
    :param list upper_stack: stack (upper window)
    :param list lower_stack: stack (lower window)
    """
    y, x = window.getyx()
    max_y, _ = window.getmaxyx()
    if boxed:
        min_y = 1
        max_y -= 1
        min_x = 1
    else:
        min_y = 0
        min_x = 0
    upper_stack.append(scrapeline(window, min_y))
    window.scroll(1)
    if boxed:
        window.move(max_y-1, 0)
        window.deleteln()
    window.move(max_y-1, min_x)
    if not lower_stack:
        # bottom of the window
        return
    writeline(window, max_y-1, 0, lower_stack.pop())
    window.move(max_y-1, min_x)


def readline(
        window, upper_stack, lower_stack,
        boxed=False, prompt="", x=-1, y=-1, clear=False, scroll=False
):
    """Read line.

    :param bool boxed: a box is drawn around the edges of the window
    :param window: window
    :param bool clear: toggle clearing line on/off
    :param bool scroll: toggle scrolling on/off

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
        if boxed:
            window.box()
        max_y, max_x = window.getmaxyx()
        y, x = window.getyx()
        char = window.get_wch()
        if char == "\x03":
            raise KeyboardInterrupt
        if char in (curses.KEY_DOWN, curses.KEY_UP):
            if not scroll:
                continue
        if char == curses.KEY_DOWN:
            if y < max_y and lower_stack:
                scroll_down(window, upper_stack, lower_stack, boxed=boxed)
                if not lower_stack:
                    window.move(y, len(scrapeline(window, y)[0][0].strip()))
            continue
        if char == curses.KEY_UP:
            if y > 2 or len(upper_stack) > 1:
                scroll_up(window, upper_stack, lower_stack, boxed=boxed)
            continue
        if x == 0:
            continue
        if char in (curses.KEY_ENTER, os.linesep):
            break
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
            if window.instr(y, x, 1).decode(encoding="utf-8") == buffer[-1]:
                window.delch(y, min_x)
                i += 1
                window.delch(y, x)
                continue
        if char in (curses.KEY_BACKSPACE, 8, 127):
            if x > min_x:
                i -= 1
                x -= 1
                buffer.pop(i)
                if boxed:
                    window.delch(y, max_x-1)
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
    if clear:
        window.move(y, 1)
        window.clrtoeol()
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


def scrapeline(window, y):
    """Scrape multi-part line from the window.

    :param window: window
    :param int y: y

    :returns: multi-part line
    :rtype: tuple
    """
    _, max_x = window.getmaxyx()
    multi_part_line = []
    buffer = []
    current_attr = window.inch(y, 0) & curses.A_COLOR
    for x in range(max_x):
        ch = window.inch(y, x)
        attr = ch & curses.A_COLOR
        ch = ch & curses.A_CHARTEXT
        if current_attr != attr:
            multi_part_line.append(("".join(buffer), current_attr))
            buffer = []
            current_attr = attr
        buffer.append(chr(ch))
    buffer = buffer[:-1]
    if buffer:
        multi_part_line.append(("".join(buffer), attr))
    return multi_part_line


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
    lower_stack = []
    upper_stack = []
    window = mv_front()
    window.clear()
    window.box()
    y, _ = window.getyx()
    y += 1
    x = 1
    max_y, max_x = window.getmaxyx()
    max_y -= 1
    window.addstr(y, x, f"Pick choice 1...{len(choices)}.")
    if y < max_y-1:
        y += 1
    else:
        scroll_down(window, upper_stack, lower_stack, boxed=True)
    for i, choice in enumerate(choices, start=1):
        window.addstr(
            y, x, f"{i}: {''.join(x[0] for x in choice)}", curses.color_pair(0)
        )
        y, _ = window.getyx()
        if y < max_y-1:
            y += 1
        else:
            scroll_down(window, upper_stack, lower_stack, boxed=True)
    line = ""
    try:
        while line not in (str(i) for i in range(1, len(choices)+1)):
            line = readline(
                window, upper_stack, lower_stack,
                prompt=">", y=y, x=0, clear=True, boxed=True, scroll=True
            )
    except KeyboardInterrupt:
        return -1
    finally:
        window.clear()
        mv_back()
    return int(line)-1


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
