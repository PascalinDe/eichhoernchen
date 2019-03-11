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
:synopsis: Timing.
"""


# standard library imports
import datetime

# third party imports
# library specific imports
import src.sqlite


def read_time_in(string):
    """Read time in.

    :param str string: string

    :returns: time
    :rtype: datetime.datetime
    """
    if string == "now":
        time = datetime.datetime.now()
    else:
        try:
            now = datetime.datetime.now()
            time = datetime.datetime.strptime(string, "%H:%M")
            time = datetime.datetime(
                now.year, now.month, now.day, time.hour, time.minute
            )
        except ValueError as exception:
            raise ValueError("hh:mm or use shortcut 'now'") from exception
    return time


def read_date_in(string):
    """Read date in.

    :param str string: string

    :returns: date
    :rtype: datetime.datetime
    """
    if string == "today":
        date = datetime.datetime.now()
    else:
        try:
            date = datetime.datetime.strptime(string, "%Y-%m-%d")
        except ValueError as exception:
            raise ValueError("yy-mm-dd or use shortcut 'today'") from exception
    return date


class Timer(object):
    """Timer.

    :ivar SQLite sqlite: Eichhörnchen SQLite database interface
    :ivar Task current_task: current task
    """

    def __init__(self, database, task=None):
        """Initialize timer.

        :param str database: Eichhörnchen SQLite3 database
        :param task: task
        :type: Task or None
        """
        self.sqlite = src.sqlite.SQLite(database)
        self.sqlite.create_table()
        if not task:
            name = ""
            start = end = due = read_time_in("now")
            total = (end - start).seconds
            self.current_task = src.sqlite.Task(name, start, end, total, due)
        else:
            self.current_task = task

    def _replace(self, **kwargs):
        """Replace current task."""
        self.current_task = self.current_task._replace(**kwargs)

    def start(self, name):
        """Start task.

        :param str name: name
        """
        result_set = self.sqlite.select_one("name", (name,))
        if result_set:
            self._replace(start=read_time_in("now"))
        else:
            self._replace(name=name, start=read_time_in("now"))

    def stop(self):
        """Stop task."""
        now = read_time_in("now")
        total = (
            self.current_task.total
            + (now - self.current_task.start).seconds
        )
        self._replace(end=read_time_in("now"), total=total)
        row = self.sqlite.update_one(
            "end",
            "name",
            (self.current_task.end, self.current_task.name)
        )
        if not row:
            self.sqlite.insert([[*self.current_task]])

    def show(self):
        """Show current task.

        :returns: current task
        :rtype: str
        """
        start = self.current_task.start.strftime("%H:%M")
        end = self.current_task.end.strftime("%H:%M")
        hours = self.current_task.total // 3600
        minutes = (self.current_task.total % 3600) // 60
        current_task = (
            f"{self.current_task.name} "
            f"({start} - {end}, total: {hours}h{minutes}m)"
        )
        return current_task
