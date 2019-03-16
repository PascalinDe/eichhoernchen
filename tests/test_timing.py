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
        timer._reset_current_task()
        self.assertEqual("", timer.current_task.name)
        self.assertEqual(
            0, (datetime.datetime.now() - timer.current_task.start).seconds
        )
        self.assertTrue(timer.current_task.start == timer.current_task.end)
        self.assertEqual(
            datetime.datetime(9999, 12, 31), timer.current_task.due
        )
        self.assertEqual(0, timer.current_task.total)

    def test_start(self):
        """Test starting task.

        Trying: starting task
        Expecting: task is initialized and
        database contains initialized task
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("foo")
        self.assertEqual("foo", timer.current_task.name)
        self.assertEqual(
            0, (datetime.datetime.now() - timer.current_task.start).seconds
        )
        self.assertEqual(
            0, (datetime.datetime.now() - timer.current_task.end).seconds
        )
        self.assertEqual(0, timer.current_task.total)
        self.assertEqual(
            datetime.datetime(9999, 12, 31), timer.current_task.due
        )
        self.assertEqual(
            timer.current_task,
            src.sqlite.Task(*timer.sqlite.select_one("name", ("foo",)))
        )

    def test_start_due_date(self):
        """Test starting task with due date.

        Trying: starting task with due date
        Expecting: due date is set
        """
        name = "foo"
        due = "2019-03-17"
        timer = src.timing.Timer(self.DATABASE)
        timer.start(f"{name} {due}")
        due = datetime.datetime.strptime(due, "%Y-%m-%d")
        self.assertEqual(due, timer.current_task.due)

    def test_start_running_task(self):
        """Test starting task when there is a running task.

        Trying: starting task
        Expecting: RuntimeError
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("foo")
        with self.assertRaises(RuntimeError):
            timer.start("bar")

    def test_restart(self):
        """Test restarting task.

        Trying: restarting task
        Expecting: current task is fetched from database
        """
        name = "foo"
        start = end = due = datetime.datetime.now()
        task = src.sqlite.Task(name, start, end, 0, due)
        timer = src.timing.Timer(self.DATABASE)
        timer.sqlite.insert([[*task]])
        time.sleep(1)
        timer.start(name)
        self.assertEqual(
            0, (datetime.datetime.now() - timer.current_task.start).seconds
        )
        self.assertEqual(
            1, (datetime.datetime.now() - timer.current_task.end).seconds
        )

    def test_stop(self):
        """Test stopping task.

        Trying: stopping task
        Expecting: current task is reset and
        database contains updated task
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("task")
        time.sleep(1)
        timer.stop()
        # current task is reset
        self.assertEqual(
            "", timer.current_task.name
        )
        self.assertTrue(
            timer.current_task.start == timer.current_task.end
        )
        self.assertEqual(
            datetime.datetime(9999, 12, 31), timer.current_task.due
        )
        self.assertEqual(0, timer.current_task.total)
        # database contains updated task
        current_task = src.sqlite.Task(
            *timer.sqlite.select_one("name", ("task",))
        )
        self.assertEqual(1, (current_task.end - current_task.start).seconds)
        self.assertEqual(1, current_task.total)
