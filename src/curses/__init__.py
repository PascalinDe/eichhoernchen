#    This file is part of Eichhoernchen 2.2.
#    Copyright (C) 2018-2021  Carine Dengler
#
#    Eichhoernchen is free software: you can redistribute it and/or modify
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
import time
import logging
import unicodedata
import curses
import curses.panel

from difflib import SequenceMatcher
from collections import defaultdict, UserList

# third party imports
# library specific imports
from src import Task
from src.interpreter import InterpreterError, UserAbort
from src.output_formatting import pprint_prompt


class ResizeError(Exception):
    """Raised when window has been resized."""

    pass


class WindowUpdateError(Exception):
    """Raised when window has been updated."""

    pass


class Buffer(UserList):
    """Buffer."""

    def __init__(self, iterable=()):
        """Initialize buffer."""
        self._pos = len(iterable)
        super().__init__(iterable)

    @property
    def pos(self):
        """Return current position.

        :returns: current position
        :rtype: int
        """
        return self._pos

    @property
    def cursor(self):
        """Return character at the current cursor position.

        :returns: character at the current cursor position
        :rtype: str
        """
        if not self.data:
            raise IndexError("empty buffer")
        return self.data[self._pos]

    def append(self, x):
        """Append a new character to the end of the buffer.

        :param str x: new character
        """
        if self._pos == len(self.data) - 1:
            self._pos += 1
        super().append(x)

    def extend(self, iterable):
        """Append characters from iterable to the end of the buffer.

        :param list iterable: characters
        """
        if self._pos == len(self.data) - 1:
            self._pos += len(iterable)
        super().extend(iterable)

    def insert(self, i, x):
        """Insert character x in the buffer before position i.

        :param int i: position
        :param str x: character
        """
        if self._pos >= i:
            self._pos += 1
        super().insert(i, x)

    def remove(self, x):
        """Remove the first occurrence of character x from the buffer.

        :param str x: character
        """
        try:
            i = self.data.index(x)
        except ValueError:
            pass
        else:
            if (self._pos == i and self._pos > 0) or self._pos > i:
                self._pos -= 1
        super().remove(x)

    def pop(self, index=-1):
        """Remove the character with the index index from the buffer
        and return it.

        :param int index: index

        :returns: character
        :rtype: str
        """
        if self._pos > 0 and self._pos >= index:
            self._pos -= 1
        return super().pop(index)

    def clear(self):
        """Remove all characters from the buffer."""
        self._pos = 0
        super().clear()

    def reverse(self):
        """Reverse the characters of the buffer in place."""
        self._pos = (len(self.data) - 1) - self._pos
        super().reverse()

    def move(self, n):
        """Move cursor position n steps to the right.

        :param int n: number of steps

        :raises: IndexError
        """
        if self._pos + n <= len(self.data) and self._pos + n >= 0:
            self._pos += n
        else:
            raise IndexError("new position out of range")

    def move_to_start(self):
        """Move cursor position to start."""
        self._pos = 0

    def move_to_end(self):
        """Move cursor position to end."""
        self._pos = len(self.data)


class WindowManager:
    """Window manager.

    :ivar list upper_stack: upper window stack
    :ivar list lower_stack: lower window stack
    :ivar bool box: if a border is drawn around the edges
    :ivar str banner: banner
    :ivar tuple commands: valid commands
    :ivar Logger logger: logger
    """

    def __init__(self, window, box=False, banner="", commands=tuple(), tags=tuple()):
        """Initialize window manager.

        :param window window: window
        :param bool box: if a border is drawn around the edges
        :param str banner: banner
        :param tuple commands: valid commands
        :param tuple tags: known tags
        """
        self._window = window
        self.box = box
        self.banner = banner
        self.commands = commands
        self._tags = tags
        self.logger = logging.getLogger().getChild(WindowManager.__name__)
        self.reinitialize()
        self.window.idlok(True)
        self.window.keypad(True)
        self.window.scrollok(True)

    @property
    def window(self):
        """Window."""
        return self._window

    @window.setter
    def window(self, window):
        """Replace window."""
        self._window = window

    @property
    def tags(self):
        """Known tags cache."""
        return self._tags

    @tags.setter
    def tags(self, tags):
        """Cache known tags."""
        self._tags = tags

    def reinitialize(self):
        """Reinitialize window."""
        try:
            self.window.clear()
            self.upper_stack = []
            self.lower_stack = []
            y, x = 0, 0
            if self.box:
                self.window.box()
                y += 1
                x += 1
            if self.banner:
                self.window.addstr(y, x, self.banner)
                y, _ = self.window.getyx()
                self.window.move(y + 2, 0)
        except Exception as exception:
            self.logger.getChild(WindowManager.reinitialize.__name__).exception(
                f"at ({y},{x}): {exception}"
            )
            raise

    def _get_suggestions(self, line):
        """Get suggestions.

        :param list line: line

        :returns: suggestions
        :rtype: list
        """
        if not line:
            return self.commands
        else:
            matchers = defaultdict(list)
            if "[" in line:
                pool = self.tags
                line = line[line.rindex("[") + 1 :]
            else:
                pool = self.commands
            for suggestion in pool:
                matcher = SequenceMatcher(
                    None,
                    "".join(line),
                    suggestion,
                ).find_longest_match(0, len(line))
                if matcher.b > 0:
                    continue
                if matcher.size < len(line):
                    continue
                matchers[matcher.size].append(suggestion)
            if not matchers:
                return list()
            return sorted(matchers.items(), key=lambda x: x[0], reverse=True)[0]

    def _completeline(self, prompt, buffer):
        """Complete line.

        :param str prompt: prompt
        :param Buffer buffer: buffer
        """
        y, _ = self.window.getyx()
        z = len(buffer)
        try:
            suggestions = self._get_suggestions("".join(buffer))
        except Exception as exception:
            self.logger.getChild(WindowManager.completeline.__name__).exception(
                exception
            )
            raise
        if len(suggestions[1]) > 1:
            self.move_scroll_down()
            self.writelines(
                self.window.getyx()[0],
                int(self.box),
                tuple(
                    ((suggestion, curses.color_pair(0)),)
                    for suggestion in suggestions[1]
                ),
            )
        if len(suggestions[1]) == 1:
            for _ in range(suggestions[0]):
                buffer.pop()
            buffer += [*suggestions[1][0]]
        if z == len(buffer):
            y, _ = self.window.getyx()
        else:
            buffer.move_to_end()
            self.window.move(y, 0)
            self.window.clrtoeol()
        self.writeline(
            y, 0, (*prompt, ("".join(buffer), curses.color_pair(0))), move=False
        )

    def _browse_command_history(
        self, ch, prompt, buffer, history_up, history_down, command
    ):
        """Browse command history.

        :param str ch: character
        :param str prompt: prompt
        :param Buffer buffer: buffer
        :param list history_up: upper command history buffer
        :param list history_down: lower command history buffer
        :param str command: current command
        """
        y, _ = self.window.getyx()
        current_length = len(command)
        if ch == curses.KEY_DOWN:
            if not history_down:
                return
            history_up.append(command)
            command = history_down.pop()
        if ch == curses.KEY_UP:
            if not history_up:
                return
            history_down.append(command)
            command = history_up.pop()
        length = sum(len(p[0]) for p in prompt)
        if length + current_length > self.window.getmaxyx()[1]:
            self.window.move(y, 0)
            self.window.clrtoeol()
            y = y - 1
        buffer = Buffer(command)
        self.window.move(y, 0)
        self.window.clrtoeol()
        self.writeline(y, 0, prompt, move=False)
        self.writeline(
            self.window.getyx()[0],
            length,
            (("".join(buffer), curses.color_pair(0)),),
            move=False,
        )

    def _scrapeline(self, y):
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

    def _scroll_up(self):
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
        self.lower_stack.append(self._scrapeline(max_y - 1))
        self.window.scroll(-1)
        self.writeline(min_y, 0, self.upper_stack.pop())
        self.window.move(max_y - 1, min_x)

    def _scroll_down(self):
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

    def _scroll_up_down(self, ch):
        """Scroll up/down.

        :param str ch: character
        """
        y, _ = self.window.getyx()
        max_y, _ = self.window.getmaxyx()
        if isinstance(ch, int) and curses.keyname(ch) == b"kDN5":
            if y < max_y and self.lower_stack:
                self._scroll_down()
                if not self.lower_stack:
                    self.window.move(y, len(self._scrapeline(y)[0][0].strip()))
            return
        if isinstance(ch, int) and curses.keyname(ch) == b"kUP5":
            if y > 2 or len(self.upper_stack) > 1:
                self._scroll_up()

    def move_scroll_down(self):
        """Move/scroll down."""
        y, _ = self.window.getyx()
        max_y, _ = self.window.getmaxyx()
        if self.box:
            max_y -= 1
        if y < max_y - 1:
            self.window.move(y + 1, 0)
        else:
            self._scroll_down()

    def _move_left(self, x, min_x, buffer):
        """Move cursor to the left.

        :param int x: x position
        :param int min_x: minimum x position
        :param Buffer buffer: buffer
        """
        y, _ = self.window.getyx()
        if x > min_x:
            buffer.move(-1)
            self.window.move(y, x - 1)
            return
        if len(buffer) > 0 and buffer.pos > 0:
            buffer.move(-1)
            self.window.insstr(y, x, buffer.cursor)

    def _move_right(self, x, min_x, buffer):
        """Move cursor to the right.

        :param int x: x position
        :param int min_x: minimum x position
        :param Buffer buffer: buffer
        """
        y, _ = self.window.getyx()
        _, max_x = self.window.getmaxyx()
        if x < max_x - 1:
            if buffer.pos < len(buffer):
                buffer.move(1)
                self.window.move(y, x + 1)
            return
        if buffer.pos < len(buffer) - 1:
            self.window.delch(y, min_x)
            buffer.move(1)
            self.window.insstr(y, x, buffer.cursor)
            return
        if self.window.instr(y, x, 1).decode(encoding="utf-8") == buffer[-1]:
            self.window.delch(y, min_x)
            buffer.move(1)
            self.window.delch(y, x)

    def _delete(self, x, min_x, buffer):
        """Delete character.

        :param int x: x position
        :param int min_x: minimum x position
        :param Buffer buffer: buffer
        """
        _, max_x = self.window.getmaxyx()
        y, _ = self.window.getyx()
        if x > min_x:
            x -= 1
            buffer.pop(buffer.pos - 1)
            if self.box:
                self.window.delch(y, max_x - 1)
            self.window.delch(y, x)
        if len(buffer) > max_x - (min_x + 2) and buffer.pos >= x - 1:
            self.window.insstr(y, min_x, buffer[(buffer.pos - x) + 1])
            self.window.move(y, x + 1)

    def _insert(self, x, min_x, buffer, ch):
        """Insert character.

        :param int x: x position
        :param int min_x: minimum x position
        :param Buffer buffer: buffer
        :param str ch: character
        """
        _, max_x = self.window.getmaxyx()
        y, _ = self.window.getyx()
        buffer.insert(buffer.pos, ch)
        if x < max_x - 1:
            x += 1
        else:
            self.window.delch(y, min_x)
            self.window.move(y, x - 1)
        self.window.insstr(ch)
        self.window.move(y, x)

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
        try:
            self.window.move(y, x)
            if self.box:
                x += 1
            min_x = x
            if prompt:
                self.writeline(y, x, prompt, move=False)
                min_x += sum(len(part[0]) for part in prompt)
        except Exception as exception:
            self.logger.getChild(WindowManager.readline.__name__).exception(
                f"at ({y},{x}): {exception}"
            )
            raise
        buffer = Buffer()
        history_up = history.copy()
        history_down = []
        command = ""
        exceptions = {
            curses.KEY_RESIZE: ResizeError,
            "\x03": KeyboardInterrupt,
            "\x04": EOFError,
        }
        while True:
            try:
                if self.box:
                    self.window.box()
                max_y, max_x = self.window.getmaxyx()
                y, x = self.window.getyx()
                ch = self.window.get_wch()
                if x == 0:
                    while y < max_y and self.lower_stack:
                        self.scroll_down()
                        y, _ = self.window.getyx()
                    x = len(self._scrapeline(y)[0][0].strip())
                    self.window.move(y, x)
                if exception := exceptions.get(ch):
                    raise exception
                if ch == "\x09":
                    self._completeline(prompt, buffer)
                    continue
                if ch in (curses.KEY_DOWN, curses.KEY_UP):
                    self._browse_command_history(
                        ch,
                        prompt,
                        buffer,
                        history_up,
                        history_down,
                        command,
                    )
                    continue
                if isinstance(ch, int) and curses.keyname(ch) in (b"kDN5", b"kUP5"):
                    if not scroll:
                        continue
                    self._scroll_up_down(ch)
                    continue
                if ch in (curses.KEY_ENTER, os.linesep):
                    break
                if ch == curses.KEY_LEFT:
                    self._move_left(x, min_x, buffer)
                    continue
                if ch == curses.KEY_RIGHT:
                    self._move_right(x, min_x, buffer)
                    continue
                if ch in (curses.KEY_BACKSPACE, 8, 127):
                    self._delete(x, min_x, buffer)
                    continue
                if isinstance(ch, int):
                    continue
                if unicodedata.category(ch).startswith("C"):
                    continue
                self._insert(x, min_x, buffer, ch)
            except Exception as exception:
                self.logger.getChild(WindowManager.readline.__name__).exception(
                    f"at ({y},{x}): {exception}"
                )
                raise
        try:
            if clear:
                self.window.move(y, 1)
                self.window.clrtoeol()
            if self.box:
                self.window.box()
        except Exception as exception:
            self.logger.getChild(WindowManager.readline.__name__).exception(
                f"at ({y},{x}): {exception}"
            )
            raise
        return "".join(buffer).strip()

    def writeline(self, y, x, multi_part_line, move=True):
        """Write multi-part line.

        :param int y: y position
        :param int x: x position
        :param tuple multi_part_line: multi-part line
        :param bool move: toggle moving cursor down on/off
        """
        _, max_x = self.window.getmaxyx()
        for i, (line, attr) in enumerate(multi_part_line):
            try:
                self.window.addstr(y, x, line, attr)
                y, x = self.window.getyx()
            except Exception as exception:
                self.logger.getChild(WindowManager.writeline.__name__).exception(
                    f"'{line}' at ({y},{x}): {exception}"
                )
                raise
            if x > max_x - 1:
                if i < len(line) - 1:
                    self.move_scroll_down()
                    y, x = self.window.getyx()
        if move:
            self.move_scroll_down()

    def writelines(self, y, x, multi_part_lines, move=True):
        """Write multi-part lines.

        :param int y: y position
        :param int x: x position
        :param tuple multi_part_lines: multi-part lines
        :param bool move: toggle moving cursor down on/off
        """
        for multi_part_line in multi_part_lines:
            self.writeline(y, x, multi_part_line, move=move)
            y, x = self.window.getyx()
            if self.box and x == 0:
                x += 1


def get_panel(nlines, ncols, begin_y, begin_x):
    """Get panel.

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


def loop(interpreter, window_mgr, type_="main"):
    """Loop through user interaction.

    :param Interpreter interpreter: command-line interpreter
    :param WindowManager window_mgr: window manager
    :param str type_: user shell type

    :raises: SystemExit
    :raises: UserAbort
    """
    history = []
    while True:
        try:
            try:
                line = window_mgr.readline(
                    history,
                    prompt=pprint_prompt(
                        task=interpreter.timer.task
                        if type_ == "main"
                        else Task("", frozenset(), ())
                    ),
                    scroll=True,
                )
            except ResizeError:
                window_mgr.reinitialize()
                continue
            if not line:
                window_mgr.move_scroll_down()
                continue
            try:
                output = interpreter.interpret_line(line)
            except (InterpreterError, Warning) as exception:
                window_mgr.move_scroll_down()
                window_mgr.writeline(
                    *window_mgr.window.getyx(),
                    ((str(exception), curses.color_pair(5)),),
                )
            else:
                window_mgr.move_scroll_down()
                window_mgr.writelines(*window_mgr.window.getyx(), output)
                if type_ == "main":
                    window_mgr.tags = interpreter.timer.tags
                history.append(line)
        except (EOFError, KeyboardInterrupt):
            if type_ == "main" and interpreter.timer.task.name:
                interpreter.timer.stop()
            window_mgr.move_scroll_down()
            window_mgr.writeline(
                *window_mgr.window.getyx(),
                (("Goodbye!" if type_ == "main" else "", curses.color_pair(0)),),
            )
            window_mgr.window.refresh()
            time.sleep(0.5)
            raise SystemExit if type_ == "main" else UserAbort
