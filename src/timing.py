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


def read_time_in(time):
    """Read time in.

    :param str time: time

    :returns: time
    :rtype: datetime.datetime
    """
    if time == "now":
        time = datetime.datetime.now()
    else:
        try:
            now = datetime.datetime.now()
            time = datetime.datetime.strptime(time, "%H:%M")
            time = datetime.datetime(
                now.year, now.month, now.day, time.hour, time.minute
            )
        except ValueError as exception:
            raise ValueError("hh:mm or use shortcut 'now'") from exception
    return time


def read_date_in(date):
    """Read date in.

    :param str date: date

    :returns: date
    :rtype: datetime.datetime
    """
    if date == "today":
        date = datetime.datetime.now()
    else:
        try:
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError as exception:
            raise ValueError("yy-mm-dd or use shortcut 'today'") from exception
    return date


class Timer(object):
    """Timer.

    :ivar SQLite sqlite: Eichhörnchen SQLite database interface
    :ivar Task current_task: current task
    """

    def __init__(self, database):
        """Initialize timer.

        :param str database: Eichhörnchen SQLite3 database
        """
        self.sqlite = src.sqlite.SQLite(database)
        self.sqlite.create_table()
        self._reset_current_task()

    def _reset_current_task(self):
        """Reset current task."""
        name = ""
        start = end = due = read_time_in("now")
        total = (end - start).seconds
        self.current_task = src.sqlite.Task(name, start, end, total, due)

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
        self._reset_current_task()

    def show(self):
        """Show current task.

        :returns: current task
        :rtype: str
        """
        if self.current_task.name:
            start = self.current_task.start.strftime("%H:%M")
            now = read_time_in("now")
            total = (
                self.current_task.total
                + (now - self.current_task.start).seconds
            )
            now = now.strftime("%H:%M")
            hours = total // 3600
            minutes = (total % 3600) // 60
            current_task = (
                f"{self.current_task.name} "
                f"({start}-{now}, total: {hours}h{minutes}m)"
            )
        else:
            current_task = "no current task"
        return current_task
