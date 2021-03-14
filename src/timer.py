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
import src.sqlite

from src import FullName, Task


class Timer:
    """Timer.

    :ivar SQLite sqlite: SQLite3 database interface
    :ivar Task task: currently running task
    """

    def __init__(self, database):
        """Initialize timer.

        :param str database: path to SQLite3 database
        """
        self.sqlite = src.sqlite.SQLite(database)
        self.sqlite.create_database()
        self._reset_task()

    def _reset_task(self, task=Task("", frozenset(), tuple())):
        """Reset currently running task.

        :param Task task: new task
        """
        self.task = task

    def start(self, full_name):
        """Start task.

        :param FullName full_name: full name
        """
        start = datetime.datetime.now()
        self.sqlite.execute("INSERT INTO time_span (start) VALUES (?)", (start,))
        self.sqlite.execute(
            "INSERT INTO running (name,start) VALUES (?,?)", (full_name.name, start)
        )
        if full_name.tags:
            self.sqlite.execute(
                "INSERT INTO tagged (tag,start) VALUES (?,?)",
                *((tag, start) for tag in full_name.tags),
            )
        self._reset_task(task=src.Task(*full_name, (start, None)))

    def stop(self):
        """Stop task."""
        if self.task.name:
            self.sqlite.execute(
                "UPDATE time_span SET end = ? WHERE start = ?",
                (datetime.datetime.now(), self.task.time_span[0]),
            )
            self._reset_task()

    def add(self, full_name, start, end):
        """Add task.

        :param FullName full_name: full name
        :param datetime start: start of time period
        :param datetime end: end of time period

        :raises ValueError: when the task cannot be added

        :returns: added task
        :rtype: Task
        """
        if end <= start:
            raise ValueError(f"new task's end ({end}) is before its start ({start})")
        if self.sqlite.execute("SELECT start FROM running WHERE start=?", (start,)):
            raise ValueError(f"there is already a task started at {start}")
        self.sqlite.execute(
            "INSERT INTO running (start,name) VALUES (?,?)", (start, full_name.name)
        )
        self.sqlite.execute(
            "INSERT INTO time_span (start,end) VALUES (?,?)", (start, end)
        )
        if full_name.tags:
            self.sqlite.execute(
                "INSERT INTO tagged (tag,start) VALUES (?,?)",
                *((tag, start) for tag in full_name.tags),
            )
        return Task(full_name.name, full_name.tags, (start, end))

    def remove(self, task):
        """Remove task.

        :param Task task: task to remove

        :raises ValueError: when the task cannot be removed
        """
        if self.task == task:
            raise ValueError("cannot remove a running task")
        for table in ("running", "tagged", "time_span"):
            self.sqlite.execute(
                f"DELETE FROM {table} WHERE start=?", (task.time_span[0],)
            )

    def clean_up(self):
        """List buggy tasks to clean up.

        :returns: buggy task to clean up
        :rtype: Task
        """
        rows = self.sqlite.execute(
            """SELECT running.start,name,tag
            FROM running
            LEFT JOIN tagged ON running.start=tagged.start
            JOIN time_span ON time_span.start=running.start
            WHERE time_span.end IS NULL"""
        )
        for (start, name), rows in itertools.groupby(rows, key=lambda x: x[:2]):
            yield Task(
                name,
                {row[-1] for row in rows if row[-1]},
                (start, datetime.datetime.now()),
            )

    def edit(self, task, action, *args):
        """Edit task.

        :param Task task: task to edit
        :param str action: editing action
        :param str args: arguments

        :raises ValueError: when task cannot be edited

        :returns: edited task
        :rtype: Task
        """
        name, tags = task.name, task.tags
        start, end = task.time_span
        reset = False
        if any(self.task) and self.task.time_span[0] == start:
            if action in ("start", "end"):
                raise ValueError(f"cannot edit {action} of a running task")
            reset = True
        if action == "name":
            name = args[0]
            self.sqlite.execute(
                "UPDATE running SET name=? WHERE start=?", (name, start)
            )
        if action == "tags":
            tags = set(args[0])
            self.sqlite.execute("DELETE FROM tagged WHERE start=?", (start,))
            self.sqlite.execute(
                "INSERT INTO tagged (tag,start) VALUES (?,?)",
                *((tag, start) for tag in tags),
            )
        if action == "end":
            end = args[0]
            if args[0] <= start:
                raise ValueError(f"new end '{end}' is before task's start")
            self.sqlite.execute(
                "UPDATE time_span SET end=? WHERE start=?", (end, start)
            )
        if action == "start":
            start = args[0]
            if end <= start:
                raise ValueError(f"new start {start} is after the task's end")
            if self.sqlite.execute("SELECT start FROM running WHERE start=?", (start,)):
                raise ValueError(
                    f"there is already a task started at new start {start}"
                )
            for table in ("time_span", "running", "tagged"):
                self.sqlite.execute(
                    f"UPDATE {table} SET start=? WHERE start=?",
                    (start, task.time_span[0]),
                )
        for task in self.list(start, end, full_name=FullName(name, tags)):
            if task.time_span[0] == start:
                break
        if reset:
            self._reset_task(task=task)
        return task

    def list(self, from_, to, full_name=FullName("", frozenset()), full_match=True):
        """List tasks.

        :param str from_: start of time period
        :param str to: end of time period
        :param FullName full_name: full name
        :param bool full_match: toggle matching full name on/off

        :returns: tasks
        :rtype: list
        """
        rows = self.sqlite.execute(
            f"""SELECT time_span.start,end,name,tag
            FROM time_span
            JOIN running ON time_span.start=running.start
            LEFT JOIN tagged ON time_span.start=tagged.start
            {_get_time_period(from_, to)}
            """
        )
        tasks = []
        for (start, end, name), rows in itertools.groupby(rows, key=lambda x: x[:3]):
            tags = {row[-1] for row in rows if row[-1]}
            if full_match:
                if (name, tags) != full_name:
                    continue
            elif any(full_name):
                if not (
                    False
                    or (full_name.name and full_name.name == name)
                    or (full_name.tags and full_name.tags == tags)
                ):
                    continue
            end = end or datetime.datetime.now()
            tasks.append(Task(name, tags, (start, end)))
        return tasks

    def sum(self, from_, to, full_name=FullName("", frozenset()), full_match=True):
        """Sum total time up.

        :param str from_: start of time period
        :param str to: end of time period
        :param FullName full_name: full name
        :param bool full_match: toggle matching full name on/off

        :returns: summed up total time per task
        :rtype: list
        """
        total_time = collections.defaultdict(int)
        for task in self.list(from_, to, full_name=full_name, full_match=full_match):
            runtime = int((task.time_span[-1] - task.time_span[0]).total_seconds())
            if all(full_name):
                total_time[(task.name, tuple(task.tags))] += runtime
                continue
            if full_name.name:
                total_time[(task.name, ("",))] += runtime
                continue
            if full_name.tags:
                total_time[("", tuple(task.tags))] += runtime
        return list(total_time.items())

    def _export_to_csv(self, filename, tasks):
        """Export to CSV file.

        :param str filename: filename
        :param list tasks: list of tasks
        """
        rows = (
            *(
                _row(Task(task.name, (tag,), task.time_span))
                for task in tasks
                for tag in sorted(task.tags)
                if task.tags
            ),
            *(
                _row(Task(task.name, ("",), task.time_span))
                for task in tasks
                if not task.tags
            ),
        )
        with open(filename, mode="w") as fp:
            csv.writer(fp).writerows(sorted(rows, key=lambda x: x[2]))

    def _export_to_json(self, filename, tasks):
        """Export to JSON file.

        :param str filename: filename
        :param list tasks: list of tasks
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

    def export(self, ext, from_, to, full_name=FullName("", frozenset())):
        """Export tasks.

        :param str ext: file format
        :param str from_: start of time period
        :param str to: end of time period
        :param FullName full_name: full_name

        :returns: filename
        :rtype: str
        """
        tasks = self.list(
            from_=from_, to=to, full_name=full_name, full_match=any(full_name)
        )
        filename = (
            pathlib.Path(tempfile.gettempdir())
            / f"{datetime.datetime.now().strftime('%Y%m%d')}.{ext}"
        )
        if ext == "csv":
            self._export_to_csv(filename, tasks)
        if ext == "json":
            self._export_to_json(filename, tasks)
        return filename


def _get_time_period(from_, to):
    """Get time period part.

    :param str from_: start of time period
    :param str to: end of time period

    :returns: time period part
    :rtype: str
    """
    return f"""WHERE date(time_span.start,'localtime')
BETWEEN date('{from_}','localtime','start of day')
AND date('{to}','localtime','start of day')"""


def _row(task):
    """Row.

    :param Task task: task

    :returns: row
    :rtype: tuple
    """
    return (
        task.name,
        task.tags[0],
        task.time_span[0].isoformat(timespec="seconds"),
        task.time_span[1].isoformat(timespec="seconds"),
    )
