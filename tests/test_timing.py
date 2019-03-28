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

    def test_reset_current_task(self):
        """Test resetting current task.

        Trying: resetting current task
        Expecting: default task
        """
        timer = src.timing.Timer(self.DATABASE)
        timer._reset_current_task()     # pylint: disable=protected-access
        start = end = datetime.datetime.now()
        expected = src.sqlite.Task("", start, end, 0, [])
        self.assertEqual(timer.current_task.name, expected.name)
        self.assertTrue(
            expected.start - timer.current_task.start < self.SECONDS
        )
        self.assertTrue(
            expected.end - timer.current_task.end < self.SECONDS
        )
        self.assertEqual(timer.current_task.total, expected.total)
        self.assertEqual(timer.current_task.tags, expected.tags)

    def test_start(self):
        """Test starting task.

        Trying: starting task
        Expecting: task is initialized and
        database contains initialized task
        """
        timer = src.timing.Timer(self.DATABASE)
        name = "foo"
        start = end = datetime.datetime.now()
        expected = src.sqlite.Task(name, start, end, 0, [])
        timer.start(name)
        self.assertEqual(timer.current_task.name, expected.name)
        self.assertTrue(
            timer.current_task.start - expected.start < self.SECONDS
        )
        self.assertTrue(timer.current_task.end - expected.end < self.SECONDS)
        self.assertEqual(timer.current_task.total, expected.total)
        self.assertEqual(timer.current_task.tags, expected.tags)
        rows = timer.sqlite.select("tasks", column="name", parameters=(name,))
        self.assertEqual(len(rows), 1)

    def test_start_running_task(self):
        """Test starting task when there is a running task.

        Trying: starting task
        Expecting: RuntimeError
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("foo")
        with self.assertRaises(Warning):
            timer.start("bar")

    def test_restart(self):
        """Test restarting task.

        Trying: restarting task
        Expecting: current task is fetched from database
        """
        timer = src.timing.Timer(self.DATABASE)
        name = "foo"
        start = end = datetime.datetime.now()
        current_task = src.sqlite.Task(name, start, end, 0, [])
        timer.sqlite.insert("tasks", [current_task[:-1]])
        time.sleep(1)
        timer.start(name)
        self.assertTrue(
            datetime.datetime.now() - timer.current_task.start < self.SECONDS
        )
        self.assertTrue(
            datetime.datetime.now() - timer.current_task.end < self.SECONDS
        )

    def test_start_tagged(self):
        """Test starting task with 2 tags.

        Trying: starting task with 2 tags
        Expecting: current task has 2 tags and 2 tags are fetched
        from database
        """
        timer = src.timing.Timer(self.DATABASE)
        tags = ["foo", "bar"]
        name = "baz"
        timer.start(f"[{tags[0]}][{tags[1]}]{name}")
        self.assertEqual(timer.current_task.tags, tags)
        rows = timer.sqlite.select("tags", column="name", parameters=(name,))
        self.assertCountEqual([row[0] for row in rows], tags)

    def test_restart_tagged(self):
        """Test restarting task with 2 tags and 1 new tag.

        Trying: restarting task with 2 tags
        Expecting: current task has 3 tags
        """
        timer = src.timing.Timer(self.DATABASE)
        tags = ["foo", "bar"]
        name = "baz"
        timer.start(f"[{tags[0]}][{tags[1]}]{name}")
        timer.stop()
        tags.append("foobar")
        timer.start(f"[{tags[2]}]{name}")
        self.assertCountEqual(timer.current_task.tags, tags)

    def test_stop(self):
        """Test stopping task.

        Trying: stopping task
        Expecting: current task is reset and
        database contains updated task
        """
        timer = src.timing.Timer(self.DATABASE)
        name = "foo"
        timer.start(name)
        time.sleep(1)
        timer.stop()
        # current task is reset
        start = end = datetime.datetime.now()
        expected = src.sqlite.Task("", start, end, 0, [])
        self.assertEqual(expected.name, timer.current_task.name)
        self.assertTrue(
            expected.start - timer.current_task.start < self.SECONDS
        )
        self.assertTrue(
            expected.end - timer.current_task.end < self.SECONDS
        )
        self.assertEqual(expected.total, timer.current_task.total)
        # database contains updated task
        rows = timer.sqlite.select(
            "tasks", column="name", parameters=(name,)
        )
        self.assertEqual(len(rows), 1)

    def test_sum(self):
        """Test summing up two tasks.

        Trying: summing up two tasks
        Expecting: sum of total attributes
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("foo")
        time.sleep(1)
        timer.stop()
        timer.start("bar")
        time.sleep(1)
        timer.stop()
        self.assertEqual(2, timer.sum(["foo", "bar"]))

    def test_sum_nonexisting(self):
        """Test summing up two tasks.

        Trying: summing up task and nonexisting task
        Expecting: ValueError
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("foo")
        time.sleep(1)
        timer.stop()
        with self.assertRaises(ValueError):
            timer.sum(["foo", "bar"])
