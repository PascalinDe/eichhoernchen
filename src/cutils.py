#    This file is part of Eichhörnchen 2.1.
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

from difflib import SequenceMatcher
from collections import defaultdict

# third party imports
# library specific imports


BANNER = "Welcome to Eichhörnchen.\tType help or ? to list commands."


class ResizeError(Exception):
    """Raised when window has been resized."""

    pass


class WindowManager:
    """Window manager.

    :ivar window window: window
    :ivar list upper_stack: stack (upper window)
    :ivar list lower_stack: stack (lower window)
    :ivar bool box: whether a border is drawn around the edges
    :ivar tuple commands: valid commands
    """

    def __init__(self, window, box=False, banner=False, commands=tuple()):
        """Initialize window manager.

        :param window window: window
        :param bool box: toggle drawing a border around the edges on/off
        :param bool banner: toggle adding a banner on/off
        :param tuple commands: valid commands
        """
        self.window = window
        self.box = box
        self.banner = banner
        self.commands = commands
        self.reinitialize()
        self.window.idlok(True)
        self.window.keypad(True)
        self.window.scrollok(True)

    def reinitialize(self):
        """Reinitialize window."""
        self.window.clear()
        self.upper_stack = []
        self.lower_stack = []
        y, x = 0, 0
        if self.box:
            self.window.box()
            y += 1
        if self.banner:
            self.window.addstr(y, x, BANNER)
            y, _ = self.window.getyx()
            self.window.move(y + 2, 0)

    def readline(self, history, y=-1, prompt=tuple(), scroll=False, clear=False):
        """Read line.

        :param list history: command history
        :param int y: y position
        :param tuple prompt: prompt
        :param bool scroll: toggle scrolling on/off
        :param bool clear: toggle clearing line on/off

        :returns: line
        :rtype: str
        """
        _, x = self.window.getyx()
        if y < 0:
            y, _ = self.window.getyx()
        self.window.move(y, x)
        if self.box:
            x += 1
        min_x = x
        if prompt:
            self.writeline(y, x, prompt, move=False)
            min_x += len(prompt[0][0])
        buffer = []
        i = 0
        history_up = history.copy()
        history_down = []
        command = ""
        while True:
            if self.box:
                self.window.box()
            max_y, max_x = self.window.getmaxyx()
            y, x = self.window.getyx()
            ch = self.window.get_wch()
            if ch == curses.KEY_RESIZE:
                raise ResizeError
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x04":
                raise EOFError
            if ch == "\x09":
                if " " in buffer:
                    continue
                y, _ = self.window.getyx()
                z = len(buffer)
                self.completeline(buffer)
                multi_part_line = (*prompt, ("".join(buffer), curses.color_pair(0)))
                if z == len(buffer):
                    y, _ = self.window.getyx()
                else:
                    i = len(buffer)
                    self.window.move(y, 0)
                    self.window.clrtoeol()
                self.writeline(y, 0, multi_part_line, move=False)
                continue
            if ch in (curses.KEY_DOWN, curses.KEY_UP):
                old_length = len(command)
                if ch == curses.KEY_DOWN:
                    if not history_down:
                        continue
                    history_up.append(command)
                    command = history_down.pop()
                if ch == curses.KEY_UP:
                    if not history_up:
                        continue
                    history_down.append(command)
                    command = history_up.pop()
                length = sum(len(part[0]) for part in prompt)
                if length + old_length > max_x:
                    self.window.move(y, 0)
                    self.window.clrtoeol()
                    y = y - 1
                buffer = list(command)
                self.window.move(y, 0)
                self.window.clrtoeol()
                self.writeline(y, 0, prompt, move=False)
                self.writeline(
                    y, length, (("".join(buffer), curses.color_pair(0)),), move=False
                )
                continue
            if isinstance(ch, int) and curses.keyname(ch) in (b"kDN5", b"kUP5"):
                if not scroll:
                    continue
            if isinstance(ch, int) and curses.keyname(ch) == b"kDN5":
                if y < max_y and self.lower_stack:
                    self.scroll_down()
                    if not self.lower_stack:
                        self.window.move(y, len(self.scrapeline(y)[0][0].strip()))
                continue
            if isinstance(ch, int) and curses.keyname(ch) == b"kUP5":
                if y > 2 or len(self.upper_stack) > 1:
                    self.scroll_up()
                continue
            if x == 0:
                while y < max_y and self.lower_stack:
                    self.scroll_down()
                    y, _ = self.window.getyx()
                x = len(self.scrapeline(y)[0][0].strip())
                self.window.move(y, x)
            if ch in (curses.KEY_ENTER, os.linesep):
                break
            if ch == curses.KEY_LEFT:
                if x > min_x:
                    i -= 1
                    self.window.move(y, x - 1)
                    continue
                if len(buffer) > 0 and i > 0:
                    i -= 1
                    self.window.insstr(y, x, buffer[i])
                    continue
            if ch == curses.KEY_RIGHT:
                if x < max_x - 1:
                    if i < len(buffer):
                        i += 1
                        self.window.move(y, x + 1)
                    continue
                if i < len(buffer) - 1:
                    self.window.delch(y, min_x)
                    i += 1
                    self.window.insstr(y, x, buffer[i])
                    continue
                if self.window.instr(y, x, 1).decode(encoding="utf-8") == buffer[-1]:
                    self.window.delch(y, min_x)
                    i += 1
                    self.window.delch(y, x)
                    continue
            if ch in (curses.KEY_BACKSPACE, 8, 127):
                if x > min_x:
                    i -= 1
                    x -= 1
                    buffer.pop(i)
                    if self.box:
                        self.window.delch(y, max_x - 1)
                    self.window.delch(y, x)
                    if len(buffer) > max_x - (min_x + 2) and i >= x - 1:
                        self.window.insstr(y, min_x, buffer[(i - x) + 1])
                        self.window.move(y, x + 1)
                continue
            if isinstance(ch, int):
                continue
            if unicodedata.category(ch).startswith("C"):
                continue
            buffer.insert(i, ch)
            i += 1
            if x < max_x - 1:
                x += 1
            else:
                self.window.delch(y, min_x)
                self.window.move(y, x - 1)
            self.window.insstr(ch)
            self.window.move(y, x)
        if clear:
            self.window.move(y, 1)
            self.window.clrtoeol()
        if self.box:
            self.window.box()
        return "".join(buffer).strip()

    def writeline(self, y, x, multi_part_line, move=True):
        """Write multi-part line.

        :param int y: y position
        :param int x: x position
        :param tuple multi_part_line: multi-part line
        :param bool move: toggle moving cursor down on/off
        """
        for line, attr in multi_part_line:
            self.window.addstr(y, x, line, attr)
            x += len(line)
        if move:
            self.mv_down_or_scroll_down()

    def writelines(self, y, x, multi_part_lines, move=True):
        """Write multi_part lines.

        :param int y: y position
        :param int x: x position
        :param tuple multi_part_lines: multi-part lines
        :param bool move: toggle moving cursor down on/off
        """
        for multi_part_line in multi_part_lines:
            self.writeline(y, x, multi_part_line, move=move)
            y, _ = self.window.getyx()

    def scrapeline(self, y):
        """Scrape multi-part line.

        :param int y: y position

        :returns: multi-part line
        :rtype: tuple
        """
        _, max_x = self.window.getmaxyx()
        buffer = []
        multi_part_line = []
        current_attr = self.window.inch(y, 0) & curses.A_COLOR
        for x in range(max_x):
            ch = self.window.inch(y, x)
            attr = ch & curses.A_COLOR
            ch = chr(ch & curses.A_CHARTEXT)
            if current_attr != attr:
                multi_part_line.append(("".join(buffer), current_attr))
                buffer = []
                current_attr = attr
            buffer.append(ch)
        buffer = buffer[:-1]
        if buffer:
            multi_part_line.append(("".join(buffer), attr))
        return multi_part_line

    def completeline(self, buffer):
        """Complete line.

        :param list buffer: buffer
        """
        if not buffer:
            commands = self.commands
        else:
            matchers = defaultdict(list)
            for command in self.commands:
                matcher = SequenceMatcher(
                    None, "".join(buffer), command
                ).find_longest_match(0, len(buffer))
                if matcher.b > 0:
                    continue
                if matcher.size < len(buffer):
                    continue
                matchers[matcher.size].append(command)
            commands = sorted(matchers.items(), key=lambda x: x[0], reverse=True)[0][1]
            if len(commands) == 1:
                buffer.clear()
                buffer += [*commands[0]]
                return
        y, x = self.window.getyx()
        y += 1
        self.writelines(
            y, x, tuple(((command, curses.color_pair(0)),) for command in commands)
        )

    def scroll_up(self):
        """Scroll up."""
        if not self.upper_stack:
            # top of the window
            return
        max_y, _ = self.window.getmaxyx()
        if self.box:
            min_y = 1
            min_x = 1
            max_y -= 1
        else:
            min_y = 0
            min_x = 0
        self.lower_stack.append(self.scrapeline(max_y - 1))
        self.window.scroll(-1)
        self.writeline(min_y, 0, self.upper_stack.pop())
        self.window.move(max_y - 1, min_x)

    def scroll_down(self):
        """Scroll down."""
        max_y, _ = self.window.getmaxyx()
        if self.box:
            min_y = 1
            min_x = 1
            max_y -= 1
        else:
            min_y = 0
            min_x = 0
        self.upper_stack.append(self.scrapeline(min_y))
        self.window.scroll(1)
        if self.box:
            self.window.move(max_y - 1, 0)
            self.window.deleteln()
        self.window.move(max_y - 1, min_x)
        if not self.lower_stack:
            # bottom of the window
            return
        self.writeline(max_y - 1, 0, self.lower_stack.pop(), move=False)
        self.window.move(max_y - 1, min_x)

    def mv_down_or_scroll_down(self):
        """Move cursor down or scroll down."""
        y, _ = self.window.getyx()
        max_y, _ = self.window.getmaxyx()
        if self.box:
            max_y -= 1
        if y < max_y - 1:
            self.window.move(y + 1, 0)
        else:
            self.scroll_down()


def mk_menu(items):
    """Make menu.

    :param list items: items

    :returns: item
    :rtype: int
    """
    if len(items) == 1:
        return 0
    while True:
        panel = mk_panel(*get_menu_dims(*curses.panel.top_panel().window().getmaxyx()))
        window = panel.window()
        window_mgr = WindowManager(window, box=True)
        y, x = window.getyx()
        multi_part_lines = (
            ((f"Pick choice 1...{len(items)}.", curses.color_pair(0)),),
            *tuple(
                ((f"{i}: {item}", curses.color_pair(0)),)
                for i, item in enumerate(items, start=1)
            ),
        )
        window_mgr.writelines(y + 1, x + 1, multi_part_lines)
        y, _ = window_mgr.window.getyx()
        line = ""
        try:
            while line not in (str(i) for i in range(1, len(items) + 1)):
                line = window_mgr.readline(
                    [],
                    y=y,
                    prompt=((">", curses.color_pair(0)),),
                    scroll=True,
                    clear=True,
                )
        except EOFError:
            return -1
        except ResizeError:
            panel.bottom()
            window_mgr.reinitialize()
            continue
        else:
            break
        finally:
            del panel
            curses.panel.update_panels()
    return int(line) - 1


def readline(prompt=tuple()):
    """Read line.

    :param tuple prompt: prompt

    :returns: line
    :rtype: str
    """
    while True:
        try:
            panel = mk_panel(
                *get_menu_dims(*curses.panel.top_panel().window().getmaxyx())
            )
            window = panel.window()
            window_mgr = WindowManager(window, box=True)
            line = window_mgr.readline([], prompt=prompt, y=1)
        except ResizeError:
            panel.bottom()
            window.reinitialize()
            continue
        else:
            return line
        finally:
            del panel
            curses.panel.update_panels()


def mk_stats(stats):
    """Make statistics.

    :param tuple stats: statistics
    """
    while True:
        stats += [
            (("", curses.color_pair(0)),),
            (
                (
                    "Enter 'q' or press Ctrl+D to return to main window",
                    curses.color_pair(0),
                ),
            ),
        ]
        panel = mk_panel(*curses.panel.top_panel().window().getmaxyx(), 0, 0)
        window = panel.window()
        window_mgr = WindowManager(window)
        window_mgr.writelines(*window.getyx(), stats)
        y, _ = window_mgr.window.getyx()
        try:
            line = ""
            while line != "q":
                line = window_mgr.readline(
                    [],
                    y=y,
                    prompt=((">", curses.color_pair(0)),),
                    scroll=True,
                    clear=True,
                )
        except EOFError:
            return
        except ResizeError:
            panel.bottom()
            window_mgr.reinitialize()
            continue
        else:
            break
        finally:
            del panel
            curses.panel.update_panels()
    return


def get_menu_dims(max_y, max_x):
    """Get menu window dimensions.

    :param int max_y: maximum y position
    :param int max_x: maximum x position

    :returns: height, width and initial x, y cursor positions
    :rtype: tuple
    """
    nlines = max_y // 2
    ncols = max_x // 2
    return nlines, ncols, (max_y - nlines) // 2, (max_x - ncols) // 2


def mk_panel(nlines, ncols, begin_y, begin_x):
    """Make panel.

    :param int nlines: number of lines
    :param int ncols: number of columns
    :param int begin_y: initial y position
    :param int begin_x: initial x position

    :returns: panel
    :rtype: panel
    """
    panel = curses.panel.new_panel(curses.newwin(nlines, ncols, begin_y, begin_x))
    curses.panel.update_panels()
    curses.doupdate()
    return panel


def initialize_colour():
    """Initialize colour pairs."""
    colour_pairs = (
        (1, 2, -1),  # name
        (2, 8, -1),  # tags
        (3, 5, -1),  # time span
        (4, 11, -1),  # total
        (5, 9, -1),  # error
    )
    for colour_pair in colour_pairs:
        curses.init_pair(*colour_pair)
