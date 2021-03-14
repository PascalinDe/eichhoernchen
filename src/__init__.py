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
:synopsis: Basic objects.
"""


# standard library imports
import collections

# third party imports
# library specific imports


# full name composed of name and one or more tags, e.g. foo[bar][baz]
FullName = collections.namedtuple(
    "FullName", ("name", "tags"), defaults=("", frozenset())
)


_Task = collections.namedtuple("Task", ("name", "tags", "time_span"))


class Task(_Task):
    """Task composed of name, one or more tags and its start and end time."""

    __slots__ = ()

    @property
    def total(self):
        """Run time (in seconds).

        :returns: run time (in seconds)
        :rtype: int
        """
        delta = self.time_span[1] - self.time_span[0]
        if delta.days >= 1:
            return delta.seconds + delta.days * (24 * 60 * 60)
        return delta.seconds
