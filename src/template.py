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
:synopsis: Templates.
"""


# standard library imports
import curses

# third party imports
# library specific imports


class Template:
    """Output formatting template."""

    @property
    def name(self):
        return ("{name}", curses.color_pair(1))

    @property
    def tag(self):
        return ("[{tag}]", curses.color_pair(2))

    @property
    def time_span(self):
        return ("{start}-{end}", curses.color_pair(3))

    @property
    def total(self):
        return ("({hours}h{minutes}m)", curses.color_pair(4))

    @property
    def running(self):
        return ("({start}-)", curses.color_pair(3))

    @property
    def prompt(self):
        return ("~>", curses.color_pair(0))

    @property
    def info(self):
        return ("{info}", curses.color_pair(4))

    @property
    def error(self):
        return ("{error}", curses.color_pair(5))
