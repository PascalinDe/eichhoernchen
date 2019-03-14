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

    def test_read_current_time_in(self):
        """Test read-in of time.

        Trying: now
        Expecting: current time
        """
        now = datetime.datetime.now()
        self.assertEqual(0, (src.timing.read_time_in("now") - now).seconds)

    def test_read_time_in(self):
        """Test read-in of time.

        Trying: 15:07
        Expecting: 15:07 and current date (datetime object)
        """
        now = datetime.datetime.now()
        self.assertEqual(
            datetime.datetime(now.year, now.month, now.day, 15, 7),
            src.timing.read_time_in("15:07")
        )

    def test_read_current_date_in(self):
        """Test read-in of date.

        Trying: today
        Expecting: current date
        """
        today = datetime.datetime.now()
        self.assertEqual(0, (src.timing.read_date_in("today") - today).days)

    def test_read_date_in(self):
        """Test read-in of date.

        Trying: 2019-03-03
        Expecting: 2019-03-03
        """
        self.assertEqual(
            datetime.datetime(2019, 3, 3),
            src.timing.read_date_in("2019-03-03")
        )

    def test_start(self):
        """Test starting task.

        Trying: starting task
        Expecting: current task is initialized and
        database contains initialized task
        """
        now = datetime.datetime.now()
        timer = src.timing.Timer(self.DATABASE)
        timer.start("task")
        self.assertEqual("task", timer.current_task.name)
        self.assertEqual(0, (timer.current_task.start - now).seconds)
        self.assertTrue(timer.current_task.end == timer.current_task.due)
        self.assertEqual(0, timer.current_task.total)
        self.assertEqual(
            timer.current_task,
            src.sqlite.Task(*timer.sqlite.select_one("name", ("task",)))
        )

    def test_start_running_task(self):
        """Test starting task when there is a running task.

        Trying: starting task
        Expecting: RuntimeError
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("task0")
        with self.assertRaises(RuntimeError):
            timer.start("task1")

    def test_restart(self):
        """Test restarting task.

        Trying: restarting task
        Expecting: current task is fetched from database
        """
        pass

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
            timer.current_task.start
            == timer.current_task.end
            == timer.current_task.due
        )
        self.assertEqual(0, timer.current_task.total)
        # database contains updated task
        current_task = src.sqlite.Task(
            *timer.sqlite.select_one("name", ("task",))
        )
        self.assertEqual(1, (current_task.end - current_task.start).seconds)
        self.assertEqual(1, current_task.total)

    def test_stop_restarted_task(self):
        """Test stopping restarted task.

        Trying: stopping restarted task
        Expecting: database contains updated task
        """
        pass

    def test_show_current_task(self):
        """Test showing current task.

        Trying: current task
        Expecting: current task
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("task")
        current_task = timer.show()
        name, start, _, total, _ = timer.current_task
        now = datetime.datetime.now()
        total = timer.current_task.total + (now -start).seconds
        start = start.strftime("%H:%M")
        now = now.strftime("%H:%M")
        hours = total // 3600
        minutes = (total % 3600) // 60
        self.assertEqual(
            f"{name} ({start}-{now}, total: {hours}h{minutes}m)",
            current_task
        )

    def test_show_no_current_task(self):
        """Test showing current task.

        Trying: no current task
        Expecting: no current task
        """
        timer = src.timing.Timer(self.DATABASE)
        self.assertEqual(
            "no current task",
            timer.show()
        )

    def test_list(self):
        """Test listing tasks.

        Trying: tasks
        Expecting: list of tasks
        """
        pass
