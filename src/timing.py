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
        start = end = due = datetime.datetime.now()
        due = datetime.datetime(9999, 12, 31)
        total = (end - start).seconds
        self.current_task = src.sqlite.Task(name, start, end, total, due)

    def _calculate_print(self, total):
        """Calculate print.

        :param int total: total

        :returns: print
        :rtype: str
        """
        hours = total // 3600
        minutes = (total % 3600) // 60
        return f"total: {hours}h{minutes}m"

    def _replace(self, **kwargs):
        """Replace current task."""
        self.current_task = self.current_task._replace(**kwargs)

    def start(self, args):
        """Start task.

        :param str args: arguments
        """
        if self.current_task.name:
            raise RuntimeError("there is a running task")
        try:
            name = " ".join(args.split(" ")[:-1])
            due = datetime.datetime.strptime(args.split(" ")[-1], "%Y-%m-%d")
        except ValueError:
            name = args
            due = None
        now = datetime.datetime.now()
        result_set = self.sqlite.select_one("name", (name,))
        if result_set:
            task = src.sqlite.Task(*result_set)
            if due:
                self._replace(
                    name=name, start=now, total=task.total, due=due
                )
            else:
                self._replace(name=name, start=now, total=task.total)
        else:
            if due:
                self._replace(name=name, start=now, due=due)
            else:
                self._replace(name=name, start=now)
            self.sqlite.insert([[*self.current_task]])

    def stop(self):
        """Stop task."""
        now = datetime.datetime.now()
        total = (
            self.current_task.total
            + (now - self.current_task.start).seconds
        )
        self._replace(end=now, total=total)
        row = self.sqlite.select_one("name", (self.current_task.name,))
        if not row:
            self.sqlite.insert([[*self.current_task]])
        row = self.sqlite.update_one(
            "end",
            "name",
            (self.current_task.end, self.current_task.name)
        )
        self.sqlite.update_one(
            "total",
            "name",
            (self.current_task.total, self.current_task.name)
        )
        self._reset_current_task()

    def show(self):
        """Show current task.

        :returns: current task
        :rtype: str
        """
        if self.current_task.name:
            now = datetime.datetime.now()
            start = self.current_task.start.strftime("%H:%M")
            total = (
                self.current_task.total
                + (now - self.current_task.start).seconds
            )
            now = now.strftime("%H:%M")
            if self.current_task.due != datetime.datetime(9999, 12, 31):
                due = self.current_task.due
                current_task = (
                    f"{self.current_task.name} "
                    f"{start}-{now} ({self._calculate_print(total)}, "
                    f"due: {datetime.datetime.strftime(due, '%Y-%m-%d')})"
                )
            else:
                current_task = (
                    f"{self.current_task.name} "
                    f"{start}-{now} ({self._calculate_print(total)})"
                )
        else:
            current_task = "no current task"
        return current_task

    def list(self):
        """List tasks.

        :returns: list of tasks
        :rtype: str
        """
        now = datetime.datetime.now()
        start_of_day = datetime.datetime(now.year, now.month, now.day, 0, 0)
        tasks = [
            src.sqlite.Task(*task)
            for task in self.sqlite.select_many(
                column="start",
                parameters=(start_of_day,),
                operator=">="
            )
        ]
        if tasks:
            for task in tasks:
                if task.due != datetime.datetime(9999, 12, 31):
                    yield(
                        f"{task.name} ({self._calculate_print(task.total)}, "
                        f"due: "
                        f"{datetime.datetime.strftime(task.due, '%Y-%m-%d')})"
                    )
                else:
                    yield f"{task.name} ({self._calculate_print(task.total)})"
        else:
            yield "no tasks"
