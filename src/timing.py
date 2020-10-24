#    This file is part of Eichhörnchen 2.1.
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
:synopsis: Timer.
"""


# standard library imports
import csv
import json
import datetime
import itertools
import collections

# third party imports
# library specific imports
import src.sqlite

from src import FullName, Task


class Timer:
    """Timer.

    :ivar SQLite sqlite: SQLite database interface
    :ivar Task task: currently running task
    """

    def __init__(self, database):
        """Initialize timer.

        :param str database: path to SQLite3 database
        """
        self.sqlite = src.sqlite.SQLite(database)
        self.sqlite.create_database()
        self._reset_task()

    def _reset_task(self, task=Task("", frozenset(), ())):
        """Reset currently running task.

        :param Task task: new running task
        """
        self.task = task

    def start(self, full_name):
        """Start task.

        :param FullName full_name: full name

        :raises Warning: when there is already a running task
        """
        if self.task.name:
            raise Warning("there is already a running task")
        start = datetime.datetime.now()
        self.sqlite.execute("INSERT INTO time_span (start) VALUES (?)", (start,))
        self.sqlite.execute(
            "INSERT INTO running (name,start) VALUES (?,?)", (full_name.name, start)
        )
        if full_name.tags:
            self.sqlite.execute(
                "INSERT INTO tagged (tag,start) VALUES (?,?)",
                *[(tag, start) for tag in full_name.tags],
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

    @staticmethod
    def _get_date(endpoint):
        """Get date.

        :param str endpoint: endpoint

        :returns: date
        :rtype: str
        """
        if endpoint == "year":
            return "date('now','localtime','start of year')"
        if endpoint == "month":
            return "date('now','localtime','start of month')"
        if endpoint == "week":
            return "date('now','weekday 0','-7 day')"
        if endpoint == "yesterday":
            return "date('now','start of day','-1 day')"
        if endpoint == "today":
            return "date('now','localtime','start of day')"
        return f"date('{endpoint}','localtime','start of day')"

    def _define_time_period(self, from_, to):
        """Define time period.

        :param str from_: start of time period
        :param str to: end of time period

        :returns: time period
        :rtype: str
        """
        sql = f"WHERE date(time_span.start)<={self._get_date(to)}"
        if from_ == "week":
            return f"{sql} AND date(time_span.start)>{self._get_date(from_)}"
        if from_ != "all":
            return f"{sql} AND date(time_span.start)>={self._get_date(from_)}"
        return sql

    def list_tasks(
        self,
        full_name=FullName("", frozenset()),
        from_="today",
        to="today",
        full_match=True,
    ):
        """List tasks.

        :param FullName full_name: full name
        :param str from_: start of time period
        :param str to: end of time period
        :param bool full_match: toggle matching full name on/off

        :returns: task
        :rtype: Task
        """
        rows = self.sqlite.execute(
            f"""SELECT time_span.start,end,name,tag FROM time_span
            JOIN running ON time_span.start=running.start
            LEFT JOIN tagged ON time_span.start=tagged.start
            {self._define_time_period(from_, to)}
            """
        )
        for (start, end, name), rows in itertools.groupby(rows, key=lambda x: x[:3]):
            tags = {row[-1] for row in rows if row[-1]}
            if full_match:
                if full_name.name and (name, tags) != full_name:
                    continue
            else:
                if full_name.name and name != full_name.name:
                    continue
                if full_name.tags and not tags == full_name.tags:
                    continue
            end = end or datetime.datetime.now()
            yield Task(name, tags, (start, end))

    def sum_total(self, summand=FullName("", frozenset()), from_="today", to="today"):
        """Sum total time up.

        :param FullName summand: full name
        :param str from_: start of time period
        :param str to: end of time period

        :returns: summed up time per task
        :rtype: dict_items
        """
        sum_total = collections.defaultdict(int)
        full_match = summand.name and summand.tags
        for task in self.list_tasks(
            full_name=summand, from_=from_, to=to, full_match=full_match
        ):
            total = int((task.time_span[-1] - task.time_span[0]).total_seconds())
            if summand.name and summand.tags:
                sum_total[(task.name, tuple(task.tags))] += total
                continue
            if summand.name:
                sum_total[(task.name, ("",))] += total
            if summand.tags:
                sum_total[("", tuple(task.tags))] += total
        return sum_total.items()

    def edit(self, task, action, *args):
        """Edit task.

        :param Task task: task to edit
        :param str action: action
        :param str args: arguments

        :raises ValueError: when the task cannot be edited

        :returns: edited task
        :rtype: Task
        """
        name = task.name
        start, end = task.time_span
        tags = task.tags
        is_running = self.task == Task(task.name, tags, (start, None))
        if is_running and action in ("start", "end"):
            raise ValueError(f"cannot edit {action} of a running task")
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
                *[(tag, start) for tag in tags],
            )
        if action == "end":
            if args[0] <= start:
                raise ValueError(f"{end} is before task's start")
            self.sqlite.execute(
                "UPDATE time_span SET end=? WHERE start=?", (args[0], start)
            )
        if action == "start":
            start = args[0]
            if end <= start:
                raise ValueError(f"{start} is after task's end")
            if self.sqlite.execute("SELECT start FROM running WHERE start=?", (start,)):
                raise ValueError(f"task started at {start} already exists")
            self.sqlite.execute(
                "UPDATE time_span SET start=? WHERE start=?", (start, task.time_span[0])
            )
            self.sqlite.execute(
                "UPDATE running SET start=? WHERE start=?", (start, task.time_span[0])
            )
            self.sqlite.execute(
                "UPDATE tagged SET start=? WHERE start=?", (start, task.time_span[0])
            )
        for task in self.list_tasks(
            full_name=FullName(name, tags), from_=start.date(), to=end.date()
        ):
            if task.time_span == (start, end):
                break
            if is_running:
                self._reset_task(task=task)
        return task

    def remove(self, task):
        """Remove task.

        :param Task task: task to remove

        :raises ValueError: when the task cannot be removed
        """
        if self.task == Task(task.name, task.tags, (task.time_span[0], None)):
            raise ValueError("cannot remove a running task")
        self.sqlite.execute("DELETE FROM running WHERE start=?", (task.time_span[0],))
        self.sqlite.execute("DELETE FROM tagged WHERE start=?", (task.time_span[0],))
        self.sqlite.execute("DELETE FROM time_span WHERE start=?", (task.time_span[0],))

    def add(self, full_name=FullName("", set()), start="", end=""):
        """Add task.

        :param FullName full_name: full name
        :param str start: start of time period
        :param str end: end of time period

        :raises ValueError: when the task cannot be added

        :returns: task
        :rtype: Task
        """
        start = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M")
        end = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M")
        if end <= start:
            raise ValueError(f"task's end ({end}) is before its start ({start})")
        if self.sqlite.execute("SELECT start FROM running WHERE start=?", (start,)):
            raise ValueError(f"task started at {start} already exists")
        self.sqlite.execute(
            "INSERT INTO running (start,name) VALUES (?,?)", (start, full_name.name)
        )
        if full_name.tags:
            self.sqlite.execute(
                "INSERT INTO tagged (tag,start) VALUES (?,?)",
                *[(tag, start) for tag in full_name.tags],
            )
        self.sqlite.execute(
            "INSERT INTO time_span (start,end) VALUES (?,?)", (start, end)
        )
        return Task(full_name.name, full_name.tags, (start, end))

    def _get_row(self, task):
        """Get row.

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

    def _export_csv(self, filename, tasks):
        """Export tasks to CSV file.

        :param str filename: filename
        :param list tasks: list of tasks
        """
        rows = [
            self._get_row(Task(task.name, (tag,), task.time_span))
            for task in tasks
            for tag in task.tags
            if task.tags
        ]
        rows += [
            self._get_row(Task(task.name, ("",), task.time_span))
            for task in tasks
            if not task.tags
        ]
        with open(filename, mode="w") as fp:
            csv.writer(fp).writerows(rows)

    def _export_json(self, filename, tasks):
        """Export tasks to JSON file.

        :param str filename: filename
        :param list tasks: list of tasks
        """
        with open(filename, mode="w") as fp:
            json.dump(
                [
                    (
                        task.name,
                        list(task.tags),
                        task.time_span[0].isoformat(timespec="seconds"),
                        task.time_span[1].isoformat(timespec="seconds"),
                    )
                    for task in tasks
                ],
                fp,
            )

    def export(self, ext="csv", from_="today", to="today"):
        """Export tasks.

        :param str ext: file format
        :param str from_: start of time period
        :param str to: end of time period

        :returns: confirmation message
        :rtype: str
        """
        tasks = self.list_tasks(from_=from_, to=to)
        filename = f"/tmp/{datetime.datetime.now().strftime('%Y%m%d')}.{ext}"
        if ext == "csv":
            self._export_csv(filename, tasks)
        if ext == "json":
            self._export_json(filename, tasks)
        return f"exported tasks from {from_} to {to} to {filename}"
