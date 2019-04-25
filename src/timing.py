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
import collections

# third party imports
# library specific imports
import src.sqlite


_Task = collections.namedtuple("Task", ["name", "tag", "time_span"])


class Task(_Task):
    """Task."""

    __slots__ = ()

    def __str__(self):
        start, end = self.time_span.pop(index=0)
        start = start.strftime("%H:%M")
        end = end.strftime("%H:%M")
        if self.tag:
            tag = f" [{self.tag}]"
        else:
            tag = ""
        return f"{self.name} {start}-{end} ({self.total}){tag}"

    @property
    def total(self):
        seconds = sum([(end - start).seconds for start, end in self.time_span])
        seconds = (self.end - self.start).seconds
        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        return f"total: {hours}h{minutes}m"


class Timer(object):
    """Timer.

    :cvar Pattern TAG_PATTERN: regular expression matching tag

    :ivar SQLite sqlite: Eichhörnchen SQLite database interface
    :ivar Task task: current task
    """

    TAG_PATTERN = re.compile(r"\[(.+?)\]")

    def __init__(self, database):
        """Initialize timer.

        :param str database: Eichhörnchen SQLite3 database
        """
        self.sqlite = src.sqlite.SQLite(database)
        for table in self.sqlite.COLUMN_DEF:
            self.sqlite.create_table(table)
        self._reset_task()

    def _reset_task(self):
        """Reset current task."""
        self.task = Task("", "", [])

    def _replace_task(self, **kwargs):
        """Replace current task."""
        self.task = self.task._replace(**kwargs)

    def start(self, args):
        """Start task.

        :param str args: command-line arguments
        """
        connection = self.sqlite.connect()
        if self.task.name:
            raise Warning("there is already a running task")
        name = self.TAG_PATTERN.sub("", args).strip()
        match = self.TAG_PATTERN.search(args)
        if match:
            tag = match.group(1)
        else:
            tag = ""
        if tag:
            sql = (
                "SELECT start,end FROM time_span WHERE name = ? "
                "AND text = ? ORDER BY start DESC"
            )
            time_span = connection.execute(sql, (name, tag)).fetchall()
        else:
            sql = (
                "SELECT start,end FROM time_span WHERE name = ? "
                "AND text IS NULL"
            )
            time_span = connection.execute(sql, (name,)).fetchall()
        if not time_span:
            now = datetime.datetime.now()
            time_span = [(now, now)]
            if tag:
                sql = "INSERT OR IGNORE INTO tag (text,name) VALUES (?,?)"
                connection.execute(sql, (tag, name))
                connection.commit()
            sql = "INSERT OR IGNORE INTO task (name) VALUES (?)"
            connection.execute(sql, (name,))
            connection.commit()
        else:
            time_span = [(now, now)] + time_span
        self._replace_task(name=name, tag=tag, time_span=time_span)

    def stop(self):
        """Stop task."""
        connection = self.sqlite.connect()
        now = datetime.datetime.now()
        time_span = self.task.time_span.pop(0)
        start = time_span[0]
        if self.task.tag:
            sql = (
                "INSERT INTO time_span (start,end,name,text) "
                "VALUES (?,?,?,?)"
            )
            parameters = (start, now, self.task.name, self.task.tag)
            connection.execute(sql, parameters)
            connection.commit()
        else:
            sql = (
                "INSERT INTO time_span (start,end,name,text) "
                "VALUES (?,?,?,NULL)"
            )
            parameters = (start, now, self.task.name)
            connection.execute(sql, parameters)
            connection.commit()
        self._reset_task()

    def list(self, today=True):
        """List tasks.

        :param bool today: toggle listing today's tasks on/off

        :returns: list of tasks (sorted by starting time)
        :rtype: list
        """
        connection = self.sqlite.connect()
        task = []
        time_span = collections.defaultdict(list)
        if today:
            sql = (
                "SELECT start,end,name,text FROM time_span "
                "WHERE start >= datetime('now','localtime','start of day')"
            )
        else:
            sql = "SELECT start,end,name,text FROM time_span"
        rows = connection.execute(sql).fetchall()
        for row in rows:
            time_span[(row[2], row[3])].append((row[0], row[1]))
        if self.task.name:
            start, _ = self.task.time_span.pop(0)
            now = datetime.datetime.now()
            time_span[(self.task.name, self.task.tag)].append((start, now))
        for k, v in time_span.items():
            v.sort(key=lambda x: x[0], reverse=True)
            task.append(Task(k[0], k[1] if k[1] else "", v))
        task.sort(key=lambda x: x[2][-1])
        return task

    def sum(self, args="", today=True):
        """Sum up run times.

        :param str args: command-line arguments
        :param bool today: toggle listing today's tasks on/off

        :returns: sum of run times
        :rtype: int
        """
        connection = self.sqlite.connect()
        time_span = []
        match = self.TAG_PATTERN.match(args)
        if match:
            tag = match.group(1)
        else:
            tag = ""
            parameters = ()
        if today:
            sql = (
                "SELECT start,end,name,text FROM time_span "
                "WHERE start >= datetime('now','localtime','start of day')"
            )
            if tag:
                sql += " AND text = ?"
                parameters = (tag,)
        else:
            sql = "SELECT start,end,name,text FROM time_span"
            if tag:
                sql += "WHERE text = ?"
                parameters = (tag,)
        if parameters:
            rows = connection.execute(sql, parameters).fetchall()
        else:
            rows = connection.execute(sql).fetchall()
        for row in rows:
            time_span.append((row[0], row[1]))
        if self.task.name:
            start, _ = self.task.time_span[0]
            now = datetime.datetime.now()
            if tag:
                if self.task.tag == tag:
                    time_span.append((start, now))
            else:
                time_span.append((start, now))
        return sum(
            [int((end - start).total_seconds()) for start, end in time_span]
        )
