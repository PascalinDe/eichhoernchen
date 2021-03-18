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
:synopsis: Windows.
"""


# standard library imports
import curses

# third party imports
# library specific imports
from src.curses.utils import get_panel, WindowManager, ResizeError


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
        panel = get_panel(*curses.panel.top_panel().window().getmaxyx(), 0, 0)
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


def draw_menu(items, banner=""):
    """Draw menu.

    :param list items: items
    :param str banner: banner

    :returns:
    :rtype: int
    """
    if len(items) == 1:
        return 0
    while True:
        max_y, max_x = curses.panel.top_panel().window().getmaxyx()
        nlines = max_y // 2
        ncols = max_x // 2
        panel = get_panel(nlines, ncols, (max_y - nlines) // 2, (max_x - ncols) // 2)
        window = panel.window()
        window_mgr = WindowManager(window, box=True, banner=banner)
        y, x = window.getyx()
        multi_part_lines = (
            ((f"{i}: {item}", curses.color_pair(0)),)
            for i, item in enumerate(items, start=1)
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


def draw_input_box(banner="", prompt=tuple()):
    """Draw input box.

    :param str banner: banner
    :param tuple prompt: prompt

    :returns: line
    :rtype: str
    """
    while True:
        try:
            max_y, max_x = curses.panel.top_panel().window().getmaxyx()
            nlines = max_y // 2
            ncols = max_x // 2
            panel = get_panel(
                nlines, ncols, (max_y - nlines) // 2, (max_x - ncols) // 2
            )
            window = panel.window()
            window_mgr = WindowManager(window, box=True, banner=banner)
            y, _ = window_mgr.window.getyx()
            line = window_mgr.readline([], prompt=prompt, y=y if banner else 1)
        except ResizeError:
            panel.bottom()
            window.reinitialize()
            continue
        else:
            return line
        finally:
            del panel
            curses.panel.update_panels()
