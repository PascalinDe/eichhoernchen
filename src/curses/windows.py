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
from src.curses.utils import mk_panel, WindowManager, ResizeError


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
