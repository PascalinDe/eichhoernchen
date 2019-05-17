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
from datetime import datetime

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
        start = datetime.now()
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
        end = datetime.now()
        connection = self.sqlite.connect()
        sql = "UPDATE time_span SET end = ? WHERE start = ?"
        connection.execute(sql, (end, self.task.time_span[0]))
        connection.commit()
        time_span = (self.task.time_span[0], end)
        self._replace_task(time_span=time_span)

    def list_tasks(self, period="today"):
        """List tasks.

        :param str period: time period

        :returns: list of tasks
        :rtype: list
        """
        sql = """
        SELECT time_span.start,end,name,tag FROM time_span
        JOIN running ON time_span.start = running.start
        LEFT JOIN tagged ON time_span.start = tagged.start
        """
        if period == "year":
            sql += """WHERE time_span.start >=
            datetime('now','localtime','start of year')"""
        elif period == "month":
            sql += """WHERE time_span.start >=
            datetime('now','localtime','start of month')"""
        elif period == "week":
            sql += """WHERE time_span.start >=
            datetime('now','localtime','weekday 1','-7 day')"""
        elif period == "yesterday":
            sql += """WHERE time_span.start >=
            datetime('now','localtime','start of day','-1 day')"""
        elif period == "today":
            sql += """WHERE time_span.start >=
            datetime('now','localtime','start of day')"""
        connection = self.sqlite.connect()
        rows = connection.execute(sql).fetchall()
        agg = collections.defaultdict(list)
        for start, end, name, tag in rows:
            agg[(name, (start, end))].append(tag)
        tasks = []
        for (name, time_span), tags in agg.items():
            if any(tags):
                tags = [tag for tag in tags if tag]
            else:
                tags = []
            tasks.append(Task(name, tags, time_span))
        return tasks
