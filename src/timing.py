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
import re
import datetime

# third party imports
# library specific imports
import src.sqlite


class Timer(object):
    """Timer.

    :ivar SQLite sqlite: Eichhörnchen SQLite database interface
    :ivar Task current_task: current task
    """

    TAG_PATTERN = re.compile(r"\[(.+?)\]")

    def __init__(self, database):
        """Initialize timer.

        :param str database: Eichhörnchen SQLite3 database
        """
        self.sqlite = src.sqlite.SQLite(database)
        self.sqlite.create_tables()
        self._reset_current_task()

    def _reset_current_task(self):
        """Reset current task."""
        start = end = datetime.datetime.now()
        self.current_task = src.sqlite.Task("", start, end, 0, [])

    def _replace(self, **kwargs):
        """Replace current task."""
        self.current_task = self.current_task._replace(**kwargs)

    def start(self, args):
        """Start task.

        :param str args: arguments
        """
        if self.current_task.name:
            raise Warning("there is already a running task")
        now = datetime.datetime.now()
        tags = self.TAG_PATTERN.findall(args)
        name = self.TAG_PATTERN.sub("", args)
        self._replace(name=name, start=now, end=now, tags=tags)
        rows0 = self.sqlite.select("tasks", column="name", parameters=(name,))
        if rows0:
            rows1 = self.sqlite.select(
                "tags", column="name", parameters=(name,)
            )
            if rows1:
                known = [row[0] for row in rows1]
                rows = [
                    (tag, self.current_task.name)
                    for tag in tags if tag not in known
                ]
                self.sqlite.insert("tags", rows)
                tags += known
            task = src.sqlite.Task(*(rows0[0] + (tags,)))
            self._replace(total=task.total)
            self.sqlite.update(
                "tasks", "start", column1="name", parameters=(now, name)
            )
        else:
            self.sqlite.insert("tasks", [self.current_task[:-1]])
            rows = [
                (tag, self.current_task.name) for tag in self.current_task.tags
            ]
            self.sqlite.insert("tags", rows)

    def stop(self):
        """Stop task."""
        now = datetime.datetime.now()
        total = (now - self.current_task.start).seconds
        self._replace(end=now, total=self.current_task.total+total)
        rows = self.sqlite.select(
            "tasks", column="name", parameters=(self.current_task.name,)
        )
        self.sqlite.update(
            "tasks",
            "total",
            (self.current_task.total, self.current_task.name),
            column1="name"
        )
        self.sqlite.update(
            "tasks",
            "end",
            (self.current_task.end, self.current_task.name),
            column1="name"
        )
        self._reset_current_task()

    def list(self):
        """List tasks.

        :returns: list of tasks
        :rtype: list
        """
        now = datetime.datetime.now()
        start_of_day = datetime.datetime(now.year, now.month, now.day, 0, 0)
        tasks = [
            src.sqlite.Task(*row, [])
            for row in self.sqlite.select(
                "tasks",
                column="start", parameters=(start_of_day,), operator=">="
            )
        ]
        return tasks

    def sum(self, names):
        """Sum up tasks.

        :param list names: list of names

        :returns: sum of total attributes
        :rtype: int
        """
        tasks = []
        for name in names:
            rows = self.sqlite.select(
                "tasks", column="name", parameters=(name,)
            )
            if not rows:
                raise ValueError(f"'{name}' does not exist")
            tasks.append(src.sqlite.Task(*rows[0], []))
        return sum([task.total for task in tasks])
