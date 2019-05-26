#    This file is part of Eichhörnchen 1.0.
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
:synopsis: Basic elements.
"""


# standard library imports
import collections
from datetime import datetime

# third party imports
# library specific imports


_Task = collections.namedtuple("Task", ["name", "tags", "time_span"])


class Task(_Task):
    """Task."""

    __slots__ = ()

    @property
    def total(self):
        """Run time (in seconds) attribute."""
        start, end = self.time_span
        seconds = (end - start).seconds
        return seconds
