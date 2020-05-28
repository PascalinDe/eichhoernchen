#    This file is part of Eichhörnchen 2.0.
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
import collections

# third party imports
# library specific imports
import src.sqlite
from src import FullName, Task


class Timer():
    """Timer.

    :ivar SQLite sqlite: Eichhörnchen SQLite database interface
    :ivar Task task: current task
    """

    def __init__(self, database):
        """Initialize timer.

        :param str database: Eichhörnchen SQLite3 database
        """
        self.sqlite = src.sqlite.SQLite(database)
        connection = self.sqlite.connect()
        for table in src.sqlite.COLUMN_DEF:
            src.sqlite.create_table(connection, table, close=False)
        connection.close()
        self._reset_task()

    def _reset_task(self, task=Task("", set(), ())):
        """Reset current task."""
        self.task = task

    def _replace_task(self, **kwargs):
        """Replace current task."""
        self._reset_task(task=self.task._replace(**kwargs))

    def start(self, full_name):
        """Start task.

        :param FullName full_name: full name
        """
        start = datetime.datetime.now()
        connection = self.sqlite.connect()
        if self.task.name:
            raise Warning("there is already a running task")
        sql = "INSERT INTO time_span (start) VALUES (?)"
        connection.execute(sql, (start,))
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.execute(sql, (full_name.name, start))
        connection.commit()
        if full_name.tags:
            sql = "INSERT INTO tagged (tag,start) VALUES (?,?)"
            connection.executemany(
                sql, [(tag, start) for tag in full_name.tags]
            )
            connection.commit()
        self._reset_task(
            task=src.Task(full_name.name, full_name.tags, (start, None))
        )

    def stop(self):
        """Stop task."""
        end = datetime.datetime.now()
        connection = self.sqlite.connect()
        sql = "UPDATE time_span SET end = ? WHERE start = ?"
        connection.execute(sql, (end, self.task.time_span[0]))
        connection.commit()
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
        elif endpoint == "month":
            return "date('now','localtime','start of month')"
        elif endpoint == "week":
            return "date('now','weekday 0','-7 day')"
        elif endpoint == "yesterday":
            return "date('now','start of day','-1 day')"
        elif endpoint == "today":
            return "date('now','localtime','start of day')"
        else:
            return f"date('{endpoint}','localtime','start of day')"

    def _define_time_period(self, from_, to):
        """Define time period.

        :param str from_: start of time period
        :param str to: end of time period

        :returns: time period
        :rtype: str
        """
        if from_ == "week":
            sql = f"""WHERE date(time_span.start)>
            {self._get_date(from_)} AND """
        elif from_ != "all":
            sql = f"""WHERE date(time_span.start)>=
            {self._get_date(from_)} AND """
        else:
            sql = "WHERE "
        sql += f"date(time_span.start)<={self._get_date(to)}"
        return sql

    def list_tasks(
            self, full_name=FullName("", set()), from_="today", to="today"
    ):
        """List tasks.

        :param str from_: start of time period
        :param str to: end of time period

        :returns: list of tasks
        :rtype: list
        """
        sql = """SELECT time_span.start,end,name,tag FROM time_span
        JOIN running ON time_span.start=running.start
        LEFT JOIN tagged ON time_span.start=tagged.start """
        sql += self._define_time_period(from_, to)
        connection = self.sqlite.connect()
        rows = connection.execute(sql).fetchall()
        agg = collections.defaultdict(list)
        for start, end, name, tag in rows:
            agg[(name, (start, end))].append(tag)
        tasks = []
        for (name, (start, end)), tags in agg.items():
            if any(tags):
                tags = {tag for tag in tags if tag}
            else:
                tags = set()
            if full_name.name:
                if (name, tags) != tuple(full_name):
                    continue
            if not end:
                end = datetime.datetime.now()
            tasks.append(Task(name, tags, (start, end)))
        return tasks

    def sum_total(self, summand="full name", from_="today", to="today"):
        """Sum total time up.

        :param str summand: summand
        :param str from_: start of time period
        :param str to: end of time period
        """
        full_name = summand == "full name"
        name = summand == "name"
        tag = summand == "tag"
        sum_total = collections.defaultdict(int)
        for task in self.list_tasks(from_=from_, to=to):
            start, end = task.time_span
            total = int((end - start).total_seconds())
            if full_name:
                sum_total[(task.name, tuple(task.tags))] += total
            if name:
                sum_total[(task.name, ("",))] += total
            if tag:
                for tag in task.tags:
                    sum_total[("", (tag,))] += total
        return list(sum_total.items())

    def edit(self, task, action, *args):
        """Edit task.

        :param Task task: task to edit
        :param str action: action
        :param str args: arguments
        """
        connection = self.sqlite.connect()
        name = task.name
        tags = task.tags
        start, end = task.time_span
        is_running = self.task == Task(name, task.tags, (start, None))
        if is_running and action in ("start", "end"):
            raise ValueError(f"cannot edit {action} of a running task")
        if action == "name":
            name, = args
            sql = "UPDATE running SET name=? WHERE start=?"
            connection.execute(sql, (name, start))
        elif action == "tags":
            tags, = args
            tags = set(tags)
            sql = "DELETE FROM tagged WHERE start=?"
            connection.execute(sql, (start,))
            sql = "INSERT INTO tagged (tag,start) VALUES (?,?)"
            connection.executemany(
                sql, [(tag, start) for tag in tags]
            )
        elif action == "end":
            end, = args
            if end <= start:
                raise ValueError(f"{end} is before task's start")
            sql = "UPDATE time_span SET end=? WHERE start=?"
            connection.execute(sql, (end, start))
        elif action == "start":
            start, = args
            if end <= start:
                raise ValueError(f"{start} is after task's end")
            sql = "SELECT start FROM running WHERE start=?"
            row = connection.execute(sql, (start,)).fetchone()
            if row:
                raise ValueError(f"task started at {start} already exists")
            sql = "UPDATE time_span SET start=? WHERE start=?"
            connection.execute(sql, (start, task.time_span[0]))
            sql = "UPDATE running SET start=? WHERE start=?"
            connection.execute(sql, (start, task.time_span[0]))
            sql = "UPDATE tagged SET start=? WHERE start=?"
            connection.execute(sql, (start, task.time_span[0]))
        connection.commit()
        tasks = self.list_tasks(
            full_name=FullName(name, tags), from_=start.date(), to=end.date()
        )
        task = [task for task in tasks if task.time_span == (start, end)][0]
        if is_running:
            self._reset_task(task=task)
        return task

    def remove(self, task):
        """Remove task.

        :param Task task: task to remove
        """
        connection = self.sqlite.connect()
        start, _ = task.time_span
        is_running = self.task == Task(task.name, task.tags, (start, None))
        if is_running:
            raise ValueError("cannot remove a running task")
        connection.execute("DELETE FROM running WHERE start=?", (start,))
        connection.execute("DELETE FROM tagged WHERE start=?", (start,))
        connection.execute("DELETE FROM time_span WHERE start=?", (start,))
        connection.commit()

    def add(self, full_name=FullName("", set()), start="", end=""):
        """Add task.

        :param FullName full_name: full name
        :param str start: start of time period
        :param str end: end of time period
        """
        connection = self.sqlite.connect()
        start = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M")
        end = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M")
        if end <= start:
            raise ValueError(
                f"task's end ({end}) is before its start ({start})"
            )
        row = connection.execute(
            "SELECT start FROM running WHERE start=?", (start,)
        ).fetchone()
        if row:
            raise ValueError(f"task started at {start} already exists")
        connection.execute(
            "INSERT INTO running (start,name) VALUES (?,?)",
            (start, full_name.name)
        )
        connection.executemany(
            "INSERT INTO tagged (tag,start) VALUES (?,?)",
            [(tag, start) for tag in full_name.tags]
        )
        connection.execute(
            "INSERT INTO time_span (start,end) VALUES (?,?)",
            (start, end)
        )
        connection.commit()
        return Task(full_name.name, full_name.tags, (start, end))
