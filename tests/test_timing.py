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
import time
import datetime
import unittest
import os
import os.path

# third party imports
# library specific imports
import src.sqlite
import src.timing


class TestTiming(unittest.TestCase):
    """Timing test cases.

    :cvar str DATABASE: Eichhörnchen SQLite3 database
    """
    DATABASE = "test.db"
    SECONDS = datetime.timedelta(seconds=1)

    def tearDown(self):
        """Tear down test cases."""
        if os.path.exists(self.DATABASE):
            os.remove(self.DATABASE)

    def test_start(self):
        """Test starting task.

        Trying: starting task
        Expecting: task is initialized and 'task' table contains task
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        name = "foo"
        timer.start(name)
        actual = timer.task
        now = datetime.datetime.now()
        time_span = [(now, now)]
        expected = src.timing.Task(name, "", time_span)
        self.assertEqual(actual.name, expected.name)
        self.assertEqual(actual.tag, expected.tag)
        f = lambda x, y: (x[0] - y[0], x[1] - y[1])
        self.assertTrue(
            f(expected.time_span[0], actual.time_span[0])
            < (self.SECONDS, self.SECONDS)
        )
        sql = "SELECT * FROM task WHERE name = ?"
        actual = connection.execute(sql, (name,)).fetchall()
        self.assertEqual(1, len(actual))

    def test_start_tagged(self):
        """Test starting task with 1 tag.

        Trying: starting task with 1 tag
        Expecting: current task has 1 tag and table 'tag'
        contains task
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        name = "foo"
        tag = "bar"
        timer.start(f"[{tag}]{name}")
        actual = timer.task
        self.assertEqual(actual.tag, tag)
        sql = "SELECT * FROM tag WHERE name = ?"
        actual = connection.execute(sql, (name,)).fetchall()
        self.assertEqual(1, len(actual))
        actual = actual[0]
        self.assertEqual(actual[0], tag)
        self.assertEqual(actual[1], name)

    def test_start_running_task(self):
        """Test starting task when there is a running task.

        Trying: starting task
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
        name = "foo"
        timer.start(name)
        time.sleep(1)
        timer.stop()
        sql = "SELECT start,end FROM time_span WHERE name = ?"
        actual = connection.execute(sql, (name,)).fetchall()
        actual = actual.pop(0)
        self.assertTrue(
            self.SECONDS < actual[1] - actual[0] < 2 * self.SECONDS
        )

    def test_list(self):
        """Test listing tasks (toggle listing today's tasks on).

        Trying: listing tasks (no running task)
        Expecting: list of tasks
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        sql = (
            "INSERT INTO time_span (start,end,name) "
            "VALUES (datetime('now','-2 day'),datetime('now','-1 day'),'foo')"
        )
        connection.execute(sql)
        connection.commit()
        name = "bar"
        timer.start(name)
        time.sleep(1)
        timer.stop()
        sql = "SELECT start,end FROM time_span WHERE name = ?"
        time_span = connection.execute(sql, (name,)).fetchall()
        expected = [src.timing.Task(name, "", time_span)]
        actual = timer.list()
        self.assertEqual(actual, expected)

    def test_list_running_task(self):
        """Test listing tasks when there is a running task.

        Trying: listing tasks (running task)
        Expecting: list of tasks
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        name = "foo"
        timer.start(name)
        time.sleep(1)
        actual = timer.list().pop(0)
        expected = src.timing.Task(name, "", [(now, now + self.SECONDS)])
        self.assertEqual(actual.name, expected.name)
        self.assertEqual(actual.tag, expected.tag)
        actual = actual.time_span.pop(0)
        expected = expected.time_span.pop(0)
        self.assertTrue(expected[0] - actual[0] < self.SECONDS)
        self.assertTrue(expected[1] - actual[1] < self.SECONDS)

    def test_list_today_off(self):
        """Test listing tasks (toggle listing today's tasks off).

        Trying: listing tasks
        Expecting: list of tasks
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        sql = (
            "INSERT INTO time_span (start,end,name) "
            "VALUES (datetime('now','-2 day'),datetime('now','-1 day'),'foo')"
        )
        connection.execute(sql)
        connection.commit()
        name = "bar"
        timer.start(name)
        time.sleep(1)
        timer.stop()
        sql = "SELECT start,end,name FROM time_span"
        time_span = connection.execute(sql).fetchall()
        expected = [
            src.timing.Task(name, "", [(start, end)])
            for start, end, name in time_span
        ]
        actual = timer.list(today=False)
        self.assertEqual(actual, expected)

    def test_sum(self):
        """Test summing up tasks.

        Trying: summing up tasks (no running task)
        Expecting: sum of run times
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        sql = (
            "INSERT INTO time_span (start,end,name) "
            "VALUES (datetime('now','-2 day'),datetime('now','-1 day'),'foo')"
        )
        connection.execute(sql)
        connection.commit()
        timer.start("bar")
        time.sleep(1)
        timer.stop()
        timer.start("baz")
        time.sleep(1)
        timer.stop()
        self.assertEqual(2, timer.sum())

    def test_sum_running_task(self):
        """Test summing up tasks.

        Trying: summing up tasks (running task)
        Expecting: sum of run times
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("foo")
        time.sleep(1)
        timer.stop()
        timer.start("bar")
        time.sleep(1)
        self.assertEqual(2, timer.sum())

    def test_sum_tag(self):
        """Test summing up tagged tasks.

        Trying: summing up tagged tasks
        Expecting: sum of run times of tagged tasks
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("foo")
        time.sleep(1)
        timer.stop()
        timer.start("bar[foobar]")
        time.sleep(1)
        timer.stop()
        timer.start("baz[foobar]")
        time.sleep(1)
        timer.stop()
        self.assertEqual(2, timer.sum("[foobar]"))

    def test_sum_tag_running_task(self):
        """Test summing up tagged tasks.

        Trying: summing up tagged tasks (running task)
        Expecting: sum of run times of tagged tasks
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("foo[foobar]")
        time.sleep(1)
        timer.stop()
        timer.start("bar[foobar]")
        time.sleep(1)
        self.assertEqual(2, timer.sum("[foobar]"))

    def test_sum_today_off(self):
        """Test summing up tasks (toggle listing today's tasks off).

        Trying: summing up tasks
        Expecting: sum of run times
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        sql = (
            "INSERT INTO time_span (start,end,name) "
            "VALUES (datetime('now','-2 day'),datetime('now','-1 day'),'foo')"
        )
        connection.execute(sql)
        connection.commit()
        timer.start("bar")
        time.sleep(1)
        timer.stop()
        timer.start("baz")
        time.sleep(1)
        timer.stop()
        self.assertEqual(24 * 60 * 60 + 2, timer.sum(today=False))
