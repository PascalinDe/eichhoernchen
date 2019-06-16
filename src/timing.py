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
import collections
import datetime

# third party imports
# library specific imports
import src.sqlite
from src import Task


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

    def _reset_task(self, task=Task("", [], ())):
        """Reset current task."""
        self.task = task

    def _replace_task(self, **kwargs):
        """Replace current task."""
        self._reset_task(task=self.task._replace(**kwargs))

    def start(self, task, tags=[]):
        """Start task.

        :param str task: task
        :param list tags: tags
        """
        start = datetime.datetime.now()
        connection = self.sqlite.connect()
        if self.task.name:
            raise Warning("there is already a running task")
        sql = "INSERT INTO time_span (start) VALUES (?)"
        connection.execute(sql, (start,))
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.execute(sql, (task, start))
        connection.commit()
        if tags:
            sql = "INSERT INTO tagged (tag,start) VALUES (?,?)"
            connection.executemany(sql, [(tag, start) for tag in tags])
            connection.commit()
        self._reset_task(task=src.Task(task, tags, (start, None)))

    def stop(self):
        """Stop task."""
        end = datetime.datetime.now()
        connection = self.sqlite.connect()
        sql = "UPDATE time_span SET end = ? WHERE start = ?"
        connection.execute(sql, (end, self.task.time_span[0]))
        connection.commit()
        self._reset_task()

    def _define_time_period(self, period, to):
        """Define time period.

        :param str period: time period
        :param str to: end of time period

        :returns: time period
        :rtype: str
        """
        if to != "now":
            to = datetime.datetime.strptime(to, "%Y-%m-%d")
        if period == "all":
            if to != "now":
                return f"""WHERE date(time_span.start) <=
                date('{to}','start of day')"""
            else:
                return ""
        elif period == "year":
            sql = """WHERE date(time_span.start) >=
            date('now','localtime','start of year')"""
        elif period == "month":
            sql = """WHERE date(time_span.start) >=
            date('now','localtime','start of month')"""
        elif period == "week":
            sql = """WHERE date(time_span.start) >
            date('now','weekday 0','-7 day')"""
        elif period == "yesterday":
            sql = """WHERE date(time_span.start) >=
            date('now','start of day','-1 day')"""
        elif period == "today":
            sql = """WHERE date(time_span.start) >=
            date('now','start of day')"""
        if to != "now":
            return sql + f"""AND date(time_span.start) <=
            date('{to}','start of day')"""
        else:
            return sql

    def list_tasks(self, period="today", to="now"):
        """List tasks.

        :param str period: time period
        :param str to: end of time period

        :returns: list of tasks
        :rtype: list
        """
        sql = """
        SELECT time_span.start,end,name,tag FROM time_span
        JOIN running ON time_span.start = running.start
        LEFT JOIN tagged ON time_span.start = tagged.start
        """
        sql += self._define_time_period(period, to)
        connection = self.sqlite.connect()
        rows = connection.execute(sql).fetchall()
        agg = collections.defaultdict(list)
        for start, end, name, tag in rows:
            agg[(name, (start, end))].append(tag)
        tasks = []
        for (name, (start, end)), tags in agg.items():
            if any(tags):
                tags = [tag for tag in tags if tag]
            else:
                tags = []
            if not end:
                end = datetime.datetime.now()
            tasks.append(Task(name, tags, (start, end)))
        return tasks

    def sum_total(self, tasks=True, tags=False, period="today"):
        """Sum total time up.

        :param bool tasks: toggle summing total time (tasks) on/off
        :param bool tags: toggle summing total time (tags) on/off
        :param str period: time period
        """
        if not tasks and not tags:
            raise ValueError("neither tasks nor tags toggle is on")
        sum_total = collections.defaultdict(int)
        for task in self.list_tasks(period=period):
            start, end = task.time_span
            total = int((end - start).total_seconds())
            if tasks:
                sum_total[(task.name, tuple(task.tags))] += total
            if tags:
                for tag in task.tags:
                    sum_total[("", (tag,))] += total
        return list(sum_total.items())
