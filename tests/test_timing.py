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
import os
import os.path
import datetime
import unittest

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
        self.assertTrue((src.timing.read_time_in("now") - now).seconds < 10)

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
        self.assertEqual((src.timing.read_date_in("today") - today).days, 0)

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
        Expecting: name and current time and date
        """
        now = datetime.datetime.now()
        timer = src.timing.Timer(self.DATABASE)
        timer.start("task")
        self.assertEqual("task", timer.current_task.name)
        self.assertTrue((timer.current_task.start - now).seconds < 10)

    def test_stop(self):
        """Test stopping task.

        Trying: stopping task
        Expecting: database contains (updated) task
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("task")
        timer.stop()
        now = datetime.datetime.now()
        self.assertTrue((now - timer.current_task.end).seconds < 10)
        self.assertEqual(
            (now - timer.current_task.end).seconds,
            timer.current_task.total
        )

    def test_show(self):
        """Test showing current task.

        Trying: showing current task
        Expecting: current task
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start("task")
        current_task = timer.show()
        timer.stop()
        name, start, end, total, _ = timer.current_task
        start = start.strftime("%H:%M")
        end = end.strftime("%H:%M")
        hours = total // 3600
        minutes = (total % 3600) // 60
        self.assertEqual(
            f"{name} ({start} - {end}, total: {hours}h{minutes}m)",
            current_task
        )
