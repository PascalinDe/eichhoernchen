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
:synopsis: Colour schemes.
"""


# standard library imports
# third party imports
# library specific imports


class FGColours():
    """
    Foreground colours.

    Black       0;30     Dark Gray     1;30
    Blue        0;34     Light Blue    1;34
    Green       0;32     Light Green   1;32
    Cyan        0;36     Light Cyan    1;36
    Red         0;31     Light Red     1;31
    Purple      0;35     Light Purple  1;35
    Brown       0;33     Yellow        1;33
    Light Gray  0;37     White         1;37

    .. _Source: http://www.tldp.org/HOWTO/Bash-Prompt-HOWTO/x329.html
    """
    BLACK = "\033[0;31m"
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    CYAN = "\033[0;36m"
    RED = "\033[0;31m"
    PURPLE = "\033[0;35m"
    BROWN = "\033[0;33m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_GREEN = "\033[1;32m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_PURPLE = "\033[1;35m"
    YELLOW = "\033[1;33m"
    WHITE = "\033[1;37m"


class BGColours():
    """Background colours.

    Black       40
    Blue        44
    Green       42
    Cyan        46
    Red         41
    Purple      45
    Brown       43
    Light Gray  47

    .. _Source: http://www.tldp.org/HOWTO/Bash-Prompt-HOWTO/x329.html
    """
    BLACK = "\033[41m"
    BLUE = "\033[44m"
    GREEN = "\033[42m"
    CYAN = "\033[46m"
    RED = "\033[41m"
    PURPLE = "\033[45m"
    BROWN = "\033[43m"
    LIGHT_GRAY = "\033[47m"


class MonochromeColourScheme():
    """Monochrome colour scheme."""

    @property
    def default(self):
        return "\033[0m"

    @property
    def name(self):
        return self.default

    @property
    def tag(self):
        return self.default

    @property
    def time_span(self):
        return self.default

    @property
    def total(self):
        return self.default


class GrmlVCSLikeColourScheme(MonochromeColourScheme):
    """Grml version control system like colour scheme."""

    @property
    def name(self):
        return FGColours.GREEN

    @property
    def tag(self):
        return FGColours.DARK_GRAY

    @property
    def time_span(self):
        return FGColours.PURPLE

    @property
    def total(self):
        return FGColours.YELLOW
