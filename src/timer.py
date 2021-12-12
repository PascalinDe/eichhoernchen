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
import src

from src import FullName, Task
from src.sqlite_interface import SQLiteInterface


class Timer:
    """Timer.

    :ivar SQLiteInterface interface: SQLite database interface
    :ivar Task task: current task
    """

    def __init__(self, database):
        """Initialize timer.

        :param str database: SQLite database file
        """
        self.interface = SQLiteInterface(database)
        self.interface.create_tables()
        self._reset_task()
        self._cache_tags()

    def _reset_task(self, task=Task("", frozenset(), tuple())):
        """Reset current task.

        :param Task task: new task
        """
        self.task = task

    @property
    def tags(self):
        """Known tags cache."""
        if not self._tags:
            self._cache_tags()
        return self._tags

    def _cache_tags(self):
        """Cache known tags."""
        self._tags = tuple(
            tag
            for (tag,) in self.interface.execute(
                "SELECT DISTINCT(tag) FROM tagged ORDER BY tag"
            )
        )

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
        self._cache_tags()

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

        :param Task task: task

        :raises: ValueError
        """
        start, end = task.time_span
        if end <= start:
            raise ValueError(f"task's end i'{end}' is before its start '{start}'")
        if self.interface.execute(
            "SELECT 1 FROM running WHERE start = ?",
            (start,),
        ):
            raise ValueError(f"there is already a task started at '{start}'")
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
        self._cache_tags()

    def remove(self, task):
        """Remove task.

        :param Task task: task

        :raises: ValueError
        """
        if self.task.name and self.task.time_span[0] == task.time_span[0]:
            raise ValueError("cannot remove current task")
        for table in ("running", "tagged", "time_span"):
            self.interface.execute(
                f"DELETE FROM {table} WHERE start = ?",
                (task.time_span[0],),
            )
        self._cache_tags()

    def edit(self, task, attribute, *args):
        """Edit task.

        :param Task task: task
        :param str attribute: attribute
        :param tuple args: arguments

        :raises: ValueError

        :returns: modified task
        :rtype: Task
        """
        name, tags = task.name, task.tags
        start, end = task.time_span
        if reset := (any(self.task) and self.task.time_span[0] == start):
            if attribute in ("start", "end"):
                raise ValueError(f"cannot edit current task's '{attribute}'")
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
                raise ValueError(f"new end '{end}' is before start '{start}'")
            self.interface.execute(
                "UPDATE time_span SET end = ? WHERE start = ?",
                (end, start),
            )
        if attribute == "start":
            start = args[0]
            if end <= start:
                raise ValueError(f"new start '{start}' is after end '{end}'")
            if self.interface.execute(
                "SELECT 1 FROM running WHERE start = ?", (start,)
            ):
                raise ValueError(f"there is already a task started at '{start}'")
            for table in ("time_span", "running", "tagged"):
                self.interface.execute(
                    f"UPDATE {table} SET start = ? WHERE start = ?",
                    (start, task.time_span[0]),
                )
        task = Task(name, tags, (start, end))
        if reset:
            self._reset_task(task=task)
        self._cache_tags()
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
        include_running=True,
    ):
        """List tasks.

        :param str start: start of time period
        :param str end: end of time period
        :param FullName full_name: full name
        :param bool match_full_name: toggle matching full name on/off
        :param bool include_running: toggle including current task on/off

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
            if not include_running and (
                self.task.name and self.task.time_span[0] == start
            ):
                continue
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
        """Sum run times up.

        :param str start: start of time period
        :param str end: end of time period
        :param FullName full_name: full name
        :param bool match_full_name: toggle matching full name on/off

        :returns: summed up run times
        :rtype: list
        """
        run_times = collections.defaultdict(int)
        for task in self.list(
            start,
            end,
            full_name=full_name,
            match_full_name=match_full_name,
        ):
            run_time = int((task.time_span[-1] - task.time_span[0]).total_seconds())
            if all(full_name):
                run_times[(task.name, tuple(task.tags))] += run_time
                continue
            if full_name.name:
                run_times[(task.name, ("",))] += run_time
                continue
            if full_name.tags:
                run_times[("", tuple(task.tags))] += run_time
        return list(run_times.items())

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
            start,
            end,
            full_name=full_name,
            match_full_name=any(full_name),
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
