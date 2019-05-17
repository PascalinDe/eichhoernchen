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
:synopsis: Timing test cases.
"""


# standard library imports
import datetime
import unittest
import os
import os.path

# third party imports
# library specific imports
import src.sqlite
import src.timing
from src import Task


class TestTiming(unittest.TestCase):
    """Timing test cases.

    :cvar str DATABASE: Eichhörnchen SQLite3 database
    """
    DATABASE = "test.db"

    def tearDown(self):
        """Tear down test cases."""
        if os.path.exists(self.DATABASE):
            os.remove(self.DATABASE)

    def test_start(self):
        """Test starting task.

        Trying: starting task
        Expecting: task is initialized and 'time_span' contains start and
        'running' table contains task name
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        name = "foo"
        timer.start(name)
        self.assertEqual(timer.task.name, name)
        rows = connection.execute(
            "SELECT start,end FROM time_span WHERE start = ?",
            (timer.task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        time_span = rows[0]
        rows = connection.execute(
            "SELECT name FROM running WHERE start = ?",
            (timer.task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        name = rows[0][0]
        self.assertEqual(time_span, timer.task.time_span)
        self.assertEqual(name, timer.task.name)

    def test_start_tagged(self):
        """Test starting task.

        Trying: starting tagged task
        Expecting: task is initialized and 'running' table contains
        task name and 'tagged' table contains tag(s)
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        name = "foo"
        tags = ["bar"]
        timer.start(name, tags=tags)
        self.assertEqual(timer.task.tags, tags)
        rows = connection.execute(
            "SELECT tag FROM tagged WHERE start = ?",
            (timer.task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        tags = rows[0]
        self.assertEqual(list(tags), timer.task.tags)

    def test_start_running(self):
        """Test starting task.

        Trying: starting task when there is a running task
        Expecting: Warning
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("foo")
        with self.assertRaises(Warning):
            timer.start("bar")

    def test_stop(self):
        """Test stopping task.

        Trying: stopping task
        Expecting: table 'time_span' has been updated
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        timer.start("foo")
        timer.stop()
        rows = connection.execute(
            "SELECT start,end FROM time_span WHERE end = ?",
            (timer.task.time_span[1],)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        time_span = rows[0]
        self.assertEqual(time_span, timer.task.time_span)

    def test_list_tasks_today(self):
        """Test listing today's tasks.

        Trying: listing today's tasks
        Expecting: list of today's tasks
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        sql = "INSERT INTO time_span (start) VALUES (?)"
        values = [(now,), (now - datetime.timedelta(days=1),)]
        connection.executemany(sql, values)
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        values = [v + w for (v, w) in zip([("foo",), ("bar",)], values)]
        connection.executemany(sql, values)
        connection.commit()
        expected = [Task("foo", [], (now, None))]
        self.assertEqual(timer.list_tasks(), expected)

    def test_list_tasks_yesterday(self):
        """Test listing all tasks since yesterday.

        Trying: listing all tasks since yesterday
        Expecting: list of all tasks since yesterday
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        sql = "INSERT INTO time_span (start) VALUES (?)"
        values = [
            (now,),
            (now - datetime.timedelta(days=1),),
            (now - datetime.timedelta(days=2),)
        ]
        connection.executemany(sql, values)
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        values = [
            v + w for (v, w) in zip([("foo",), ("bar",), ("baz",)], values)
        ]
        connection.executemany(sql, values)
        connection.commit()
        expected = [
            Task("foo", [], (now, None)),
            Task("bar", [], (now - datetime.timedelta(days=1), None))
        ]
        self.assertEqual(timer.list_tasks(period="yesterday"), expected)

    def test_list_tasks_week(self):
        """Test listing all tasks since the beginning of the week.

        Trying: listing all tasks since the beginning of the week
        Expecting: list of all tasks since the beginning of the week
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        sql = "INSERT INTO time_span (start) VALUES (?)"
        values = [
            (now,),
            (now - datetime.timedelta(days=1),),
            (now - datetime.timedelta(days=7),)
        ]
        connection.executemany(sql, values)
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        values = [
            v + w for (v, w) in zip([("foo",), ("bar",), ("baz",)], values)
        ]
        connection.executemany(sql, values)
        connection.commit()
        if now.weekday() >= 1:
            expected = [Task(v, [], (w, None)) for (v, w) in values[:2]]
        else:
            v, w = values.pop(0)
            expected = [Task(v, [], (w, None))]
        self.assertEqual(timer.list_tasks(period="week"), expected)

    def test_list_tasks_month(self):
        """Test listing all tasks since the beginning of the month.

        Trying: listing all tasks since the beginning of the month
        Expecting: list of all tasks since the beginning of the month
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        sql = "INSERT INTO time_span (start) VALUES (?)"
        values = [
            (now,),
            (now.replace(day=1),),
            (now.replace(day=1) - datetime.timedelta(days=1),)
        ]
        connection.executemany(sql, values)
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        values = [
            v + w for (v, w) in zip([("foo",), ("bar",), ("baz",)], values)
        ]
        connection.executemany(sql, values)
        connection.commit()
        expected = [Task(v, [], (w, None)) for (v, w) in values[:2]]
        self.assertEqual(timer.list_tasks(period="month"), expected)

    def test_list_tasks_year(self):
        """Test listing all tasks since the beginning of the year.

        Trying: listing all tasks since the beginning of the year
        Expecting: list of all tasks since the beginning of the year
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        sql = "INSERT INTO time_span (start) VALUES (?)"
        values = [
            (now,),
            (now.replace(month=1, day=1),),
            (now.replace(month=1, day=1) - datetime.timedelta(days=1),)
        ]
        connection.executemany(sql, values)
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        values = [
            v + w for (v, w) in zip([("foo",), ("bar",), ("baz",)], values)
        ]
        connection.executemany(sql, values)
        connection.commit()
        expected = [Task(v, [], (w, None)) for (v, w) in values[:2]]
        self.assertEqual(timer.list_tasks(period="year"), expected)

    def test_list_tasks_all(self):
        """Test listing all tasks.

        Trying: listing all tasks
        Expecting: list of all tasks
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        sql = "INSERT INTO time_span (start) VALUES (?)"
        values = [
            (now,),
            (now.replace(day=1) - datetime.timedelta(days=1),),
            (now.replace(month=1, day=1) - datetime.timedelta(days=1),)
        ]
        connection.executemany(sql, values)
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        values = [
            v + w for (v, w) in zip([("foo",), ("bar",), ("baz",)], values)
        ]
        connection.executemany(sql, values)
        connection.commit()
        expected = [Task(v, [], (w, None)) for (v, w) in values]
        self.assertEqual(timer.list_tasks(period="all"), expected)
