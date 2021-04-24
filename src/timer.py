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
:synopsis: Timer.
"""


# standard library imports
import csv
import json
import pathlib
import datetime
import tempfile
import itertools
import collections

# third party imports
# library specific imports
import src.sqlite_interface

from src import FullName, Task


class Timer:
    """Timer.

    :ivar SQLiteInterface interface: SQLite database interface
    :ivar Task task: currently running task
    """

    def __init__(self, database):
        """Initialize timer.

        :param str database: SQLite database file
        """
        self.interface = src.sqlite_interface.SQLiteInterface(database)
        self.interface.create_tables()
        self._reset_task()

    def _reset_task(self, task=Task("", frozenset(), tuple())):
        """Reset currently running task.

        :param Task task: new task
        """
        self.task = task

    def start(self, task):
        """Start task.

        :param Task task: task
        """
        start = datetime.datetime.now()
        self.interface.execute(
            "INSERT INTO time_span (start) VALUES (?)",
            (start,),
        )
        self.interface.execute(
            "INSERT INTO running (name,start) VALUES (?,?)", (task.name, start)
        )
        if task.tags:
            self.interface.execute(
                "INSERT INTO tagged (tag,start) VALUES (?,?)",
                *((tag, start) for tag in task.tags),
            )
        self._reset_task(task=src.Task(task.name, task.tags, (start, None)))

    def stop(self):
        """Stop task."""
        if self.task.name:
            self.interface.execute(
                "UPDATE time_span SET end=? WHERE start=?",
                (datetime.datetime.now(), self.task.time_span[0]),
            )
            self._reset_task()

    def add(self, task):
        """Add task.

        :param Task task: task

        :raises ValueError: when the task cannot be added

        :returns: task
        :rtype: Task
        """
        start, end = task.time_span
        if self.interface.execute("SELECT start FROM running WHERE start=?", (start,)):
            raise ValueError(f"there is already a task started at {start}")
        self.interface.execute(
            "INSERT INTO running (start,name) VALUES (?,?)", (start, task.name)
        )
        self.interface.execute(
            "INSERT INTO time_span (start,end) VALUES (?,?)", (start, end)
        )
        if task.tags:
            self.interface.execute(
                "INSERT INTO tagged (tag,start) VALUES (?,?)",
                *((tag, start) for tag in task.tags),
            )
        return task

    def remove(self, task):
        """Remove task.

        :param Task task: task

        :raises ValueError: when the task cannot be removed
        """
        if self.task == task:
            raise ValueError("cannot remove currently running task")
        for table in ("running", "tagged", "time_span"):
            self.interface.execute(
                f"DELETE FROM {table} WHERE start=?", (task.time_span[0],)
            )

    def list_buggy_tasks(self):
        """List buggy tasks.

        :returns: buggy task
        :rtype: generator
        """
        rows = self.interface.execute(
            """SELECT running.start,name,tag
            FROM running
            LEFT JOIN tagged ON running.start=tagged.start
            JOIN time_span ON time_span.start=running.start
            WHERE time_span.end IS NULL"""
        )
        return (
            Task(
                name,
                {row[-1] for row in rows if row[-1]},
                (start, datetime.datetime.now()),
            )
            for (start, name), rows in itertools.groupby(rows, key=lambda x: x[:2])
        )

    def edit(self, task, action, *args):
        """Edit task.

        :param Task task: task
        :param str action: action
        :param str args: argument(s)

        :raises ValueError: when task cannot be edited

        :returns: task
        :rtype: Task
        """
        start, end = task.time_span
        currently_running = any(self.task) and self.task.time_span[0] == start
        if currently_running:
            if action in ("start", "end"):
                raise ValueError(f"cannot edit '{action}' of currently running task")
        if action == "name":
            self.interface.execute(
                "UPDATE running SET name=? WHERE start=?", (args[0], start)
            )
            task = Task(args[0], task.tags, task.time_span)
        if action == "tags":
            self.interface.execute("DELETE FROM tagged WHERE start=?", (start,))
            self.interface.execute(
                "INSERT INTO tagged (tag,start) VALUES (?,?)",
                *((tag, start) for tag in args[0]),
            )
            task = Task(task.name, args[0], task.time_span)
        if action == "end":
            end = args[0]
            if end <= start:
                raise ValueError(f"new end '{end}' is before task's start")
            self.interface.execute(
                "UPDATE time_span SET end=? WHERE start=?", (end, start)
            )
            task = Task(task.name, task.tags, (start, end))
        if action == "start":
            start = args[0]
            if self.interface.execute(
                "SELECT start FROM running WHERE start=?", (start,)
            ):
                raise ValueError(
                    f"there is already a task started at new start '{start}'"
                )
            for table in ("time_span", "running", "tagged"):
                self.interface.execute(
                    f"UPDATE {table} SET start=? WHERE start=?",
                    (start, task.time_span[0]),
                )
            task = Task(task.name, task.tags, (start, end))
        if currently_running:
            self._reset_task(task=task)
        return task

    def list(self, start, end, full_name=FullName("", frozenset()), full_match=True):
        """List tasks.

        :param str start: start of time period
        :param str end: end of time period
        :param FullName full_name: full name
        :param bool full_match: toggle matching full name on/off

        :returns: task
        :rtype: generator
        """
        rows = self.interface.execute(
            f"""SELECT time_span.start,end,name,tag
            FROM time_span
            JOIN running ON time_span.start=running.start
            LEFT JOIN tagged ON time_span.start=tagged.start
            WHERE date(time_span.start,'localtime')
            BETWEEN date('{start}','localtime','start of day')
            AND date('{end}','localtime','start of day')"""
        )
        for (start, end, name), rows in itertools.groupby(rows, key=lambda x: x[:3]):
            tags = {row[-1] for row in rows if row[-1]}
            if full_match and (name, tags) != full_name:
                continue
            elif any(full_name) and not (
                False or full_name.name == name or full_name.tags == tags
            ):
                continue
            yield Task(name, tags, (start, end or datetime.datetime.now()))

    def sum(self, start, end, full_name=FullName("", frozenset()), full_match=True):
        """Sum runtime up.

        :param str start: start of time period
        :param str end: end of time period
        :param FullName full_name: full name
        :param bool full_match: toggle matching full name on/off

        :returns: summed up runtime per task
        :rtype: collections.defaultdict
        """
        runtimes = collections.defaultdict(int)
        for task in self.list(start, end, full_name=full_name, full_match=full_match):
            runtime = int((task.time_span[1] - task.time_span[0]).total_seconds())
            if all(full_name):
                runtimes[(full_name.name, tuple(full_name.tags))] += runtime
                continue
            if full_name.name:
                runtimes[(full_name.name, ("",))] += runtime
            if full_name.tags:
                runtimes[("", tuple(full_name.tags))] += runtime
        return runtimes

    def _export_to_csv(self, filename, tasks):
        """Export to CSV file.

        :param str filename: filename
        :param generator tasks: tasks
        """
        rows = (
            (
                task.name,
                tag,
                task.time_span[0].isoformat(timespec="seconds"),
                task.time_span[1].isoformat(timespec="seconds"),
            )
            for task in tasks
            for tag in sorted(task.tags or ("",))
        )
        with open(filename, mode="w") as fp:
            csv.writer(fp).writerows(sorted(rows, key=lambda x: x[2]))

    def _export_to_json(self, filename, tasks):
        """Export to JSON file.

        :param str filename: filename
        :param generator tasks: tasks
        """
        with open(filename, mode="w") as fp:
            json.dump(
                sorted(
                    (
                        (
                            task.name,
                            tuple(task.tags),
                            task.time_span[0].isoformat(timespec="seconds"),
                            task.time_span[1].isoformat(timespec="seconds"),
                        )
                        for task in tasks
                    ),
                    key=lambda x: x[2],
                ),
                fp,
            )

    def export(
        self, ext, start, end, full_name=FullName("", frozenset()), full_match=True
    ):
        """Export tasks.

        :param str ext: filename extension
        :param str start: start of time period
        :param str end: end of time period
        :param FullName full_name: full name
        :param bool full_match: toggle matching full name on/off

        :returns: filename
        :rtype: str
        """
        tasks = self.list(start, end, full_name=full_name, full_match=full_match)
        filename = (
            pathlib.Path(tempfile.gettempdir())
            / f"{datetime.datetime.now().strftime('%Y%m%d')}.{ext}"
        )
        if ext == "csv":
            self._export_to_csv(filename, tasks)
        if ext == "json":
            self._export_to_json(filename, tasks)
        return filename
