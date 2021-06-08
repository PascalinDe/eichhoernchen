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
    :ivar Task task: current task
    """

    def __init__(self, database):
        """Initialize timer.

        :param str database: SQLite database file path
        """
        self.interface = src.sqlite_interface.SQLiteInterface(database)
        self.interface.create_tables()
        self._reset_task()

    def _reset_task(self, task=Task("", frozenset(), tuple())):
        """Reset current task.

        :param Task task: new task
        """
        self.task = task

    def start(self, task):
        """Start task.

        :param Task task: new task
        """
        start = datetime.datetime.now()
        statements = (
            (
                "INSERT INTO time_span (start) VALUES (?)",
                (start,),
            ),
            (
                "INSERT INTO running (name,start) VALUES (?,?)",
                (task.name, start),
            ),
        )
        if task.tags:
            statements += (
                (
                    "INSERT INTO tagged (tag,start) VALUES (?,?)",
                    *((tag, start) for tag in task.tags),
                ),
            )
        for (statement, *parameters) in statements:
            self.interface.execute(statement, *parameters)
        self._reset_task(
            task=src.Task(task.name, task.tags, (start, None)),
        )

    def stop(self):
        """Stop current task."""
        if self.task.name:
            self.interface.execute(
                "UPDATE time_span SET end = ? WHERE start = ?",
                (datetime.datetime.now(), self.task.time_span[0]),
            )
            self._reset_task()

    def add(self, task):
        """Add task.

        :param Task task: task to add

        :raises ValueError: when the task cannot be added

        :returns: new task
        :rtype: Task
        """
        start, end = task.time_span
        if end <= start:
            raise ValueError(f"task's end {end} is before its start {start}")
        if self.interface.execute(
            "SELECT 1 FROM running WHERE start = ?",
            (start,),
        ):
            raise ValueError(f"a task started at {start} already exists")
        statements = (
            (
                "INSERT INTO running (start,name) VALUES (?,?)",
                (start, task.name),
            ),
            ("INSERT INTO time_span (start,end) VALUES (?,?)", (start, end)),
        )
        if task.tags:
            statements += (
                (
                    "INSERT INTO tagged (tag,start) VALUES (?,?)",
                    *((tag, start) for tag in task.tags),
                ),
            )
        for statement, *parameters in statements:
            self.interface.execute(
                statement,
                *parameters,
            )
        return task

    def remove(self, task):
        """Remove task.

        :param Task task: task to remove

        :raises ValueError: when the task cannot be removed
        """
        if self.task == task:
            raise ValueError("cannot remove current task")
        for table in ("running", "tagged", "time_span"):
            self.interface.execute(
                f"DELETE FROM {table} WHERE start = ?",
                (task.time_span[0],),
            )

    def edit(self, task, attribute, *args):
        """Edit task.

        :param Task task: task to edit
        :param str attribute: attribute
        :param tuple args: arguments

        :raises ValueError: when task cannot be edited

        :returns: edited task
        :rtype: Task
        """
        name, tags = task.name, task.tags
        start, end = task.time_span
        if reset := (any(self.task) and self.task.time_span[0] == start):
            if attribute in ("start", "end"):
                raise ValueError(f"cannot edit {attribute} of current task")
        if attribute == "name":
            name = args[0]
            self.interface.execute(
                "UPDATE running SET name = ? WHERE start = ?",
                (name, start),
            )
        if attribute == "tags":
            tags = set(args[0])
            self.interface.execute("DELETE FROM tagged WHERE start = ?", (start,))
            self.interface.execute(
                "INSERT INTO tagged (tag,start) VALUES (?,?)",
                *((tag, start) for tag in tags),
            )
        if attribute == "end":
            end = args[0]
            if end <= start:
                raise ValueError(f"new end '{end}' is before task's start")
            self.interface.execute(
                "UPDATE time_span SET end = ? WHERE start = ?",
                (end, start),
            )
        if attribute == "start":
            start = args[0]
            if end <= start:
                raise ValueError(f"new start '{start}' is after the task's end")
            if self.interface.execute(
                "SELECT 1 FROM running WHERE start = ?", (start,)
            ):
                raise ValueError(f"a task started at {start} already exists")
            for table in ("time_span", "running", "tagged"):
                self.interface.execute(
                    f"UPDATE {table} SET start = ? WHERE start = ?",
                    (start, task.time_span[0]),
                )
        if reset:
            self._reset_task(task=Task(name, tags, (start, end)))
        return task

    def list(
        self,
        start,
        end,
        full_name=FullName(
            "",
            frozenset(),
        ),
        match_full_name=True,
    ):
        """List tasks.

        :param str start: start of time period
        :param str end: end of time period
        :param FullName full_name: full name
        :param bool match_full_name: toggle matching full name on/off

        :returns: tasks
        :rtype: list
        """
        rows = self.interface.execute(
            f"""SELECT time_span.start,end,name,tag
            FROM time_span
            JOIN running ON time_span.start = running.start
            LEFT JOIN tagged ON time_span.start = tagged.start
            WHERE date(time_span.start,'localtime')
            BETWEEN date('{start}','localtime','start of day')
            AND date('{end}','localtime','start of day')
            """
        )
        tasks = []
        for (start, end, name), rows in itertools.groupby(rows, key=lambda x: x[:3]):
            tags = {row[-1] for row in rows if row[-1]}
            if match_full_name:
                if (name, tags) != full_name:
                    continue
            elif any(full_name):
                if not (
                    (full_name.name and full_name.name == name)
                    or (full_name.tags and full_name.tags == tags)
                ):
                    continue
            end = end or datetime.datetime.now()
            tasks.append(Task(name, tags, (start, end)))
        return tasks

    def list_buggy_tasks(self):
        """List buggy tasks.

        :returns: buggy tasks
        :rtype: list
        """
        rows = self.interface.execute(
            """SELECT running.start,name,tag
            FROM running
            LEFT JOIN tagged ON running.start=tagged.start
            JOIN time_span ON time_span.start=running.start
            WHERE time_span.end IS NULL
            """
        )
        tasks = []
        for (start, name), rows in itertools.groupby(rows, key=lambda x: x[:2]):
            tasks.append(
                Task(
                    name,
                    {row[-1] for row in rows if row[-1]},
                    (start, datetime.datetime.now()),
                ),
            )
        return tasks

    def sum(
        self, start, end, full_name=FullName("", frozenset()), match_full_name=True
    ):
        """Sum up runtime.

        :param str start: start of time period
        :param str end: end of time period
        :param FullName full_name: full name
        :param bool match_full_name: toggle matching full name on/off

        :returns: summed up runtimes
        :rtype: list
        """
        runtimes = collections.defaultdict(int)
        for task in self.list(
            start, end, full_name=full_name, match_full_name=match_full_name
        ):
            runtime = int((task.time_span[-1] - task.time_span[0]).total_seconds())
            if all(full_name):
                runtimes[(task.name, tuple(task.tags))] += runtime
                continue
            if full_name.name:
                runtimes[(task.name, ("",))] += runtime
                continue
            if full_name.tags:
                runtimes[("", tuple(task.tags))] += runtime
        return list(runtimes.items())

    def export(self, ext, start, end, full_name=FullName("", frozenset())):
        """Export tasks.

        :param str ext: file extension
        :param str start: start of time period
        :param str end: end of time period
        :param FullName full_name: full name

        :returns: filename
        :rtype: str
        """
        tasks = self.list(
            start, end, full_name=full_name, match_full_name=any(full_name)
        )
        filename = (
            pathlib.Path(tempfile.gettempdir())
            / f"{datetime.datetime.now().strftime('%Y%m%d')}.{ext}"
        )
        if ext == "csv":

            def _row(task):
                return (
                    task.name,
                    task.tags[0],
                    task.time_span[0].isoformat(timespec="seconds"),
                    task.time_span[1].isoformat(timespec="seconds"),
                )

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
        if ext == "json":
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
        return filename
