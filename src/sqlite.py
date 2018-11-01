#    This file is part of Eichhörnchen 1.0.
#    Copyright (C) 2018  Carine Dengler
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
:synopsis: Eichhörnchen SQLite3 database interface.
"""


# standard library imports
import collections

# third party imports
# library specific imports


_Task = collections.namedtuple(
    "Task", ["name", "start_time", "end_time", "priority"]
)


class Task(_Task):      # pylint: disable=missing-docstring
    __slots__ = ()

    def __repr__(self):
        repr_ = "{name} ({start_time} - {end_time}): {priority}".format(
            name=self.name,
            start_time=self.start_time,
            end_time=self.end_time,
            priority=self.priority
        )
        return repr_
