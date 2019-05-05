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
:synopsis: Listing tests.
"""


# standard library imports
from datetime import datetime, timedelta

# third party imports

# library specific imports
import tests.base
import src.sqlite
import src.timing
import src.listing


class TestListing(tests.base.BaseTesting):
    """Test listing."""

    def test_listing_today(self):
        """Test listing today's tasks.

        Trying: listing tasks
        Expecting: list of today's tasks
        """
        connection = self.sqlite.connect()
        now = datetime.now()
        time_spans = [
            (now - timedelta(days=2), now - timedelta(days=1), "foo", ""),
            (now - timedelta(hours=1), now, "bar", "")
        ]
        sql = "INSERT INTO time_span (start,end,name,text) VALUES (?,?,?,?)"
        connection.executemany(sql, time_spans)
        connection.commit()
        expected = [time_spans[1]]
        actual = src.listing.list_tasks(self.sqlite)
        self.assertEqual(actual, expected)

    def test_listing_all(self):
        """Test listing all tasks.

        Trying: listing tasks
        Expecting: list of all tasks
        """
        connection = self.sqlite.connect()
        now = datetime.now()
        expected = [
            (now - timedelta(days=2), now - timedelta(days=1), "foo", ""),
            (now - timedelta(hours=1), now, "bar", "")
        ]
        sql = "INSERT INTO time_span (start,end,name,text) VALUES (?,?,?,?)"
        connection.executemany(sql, expected)
        connection.commit()
        actual = src.listing.list_tasks(self.sqlite, today=False)
        self.assertEqual(actual, expected)

    def test_listing_current_task(self):
        """Test listing tasks when there is a running task.

        Trying: listing tasks
        Expecting: list of tasks including running task
        """
        now = datetime.now()
        start = now - timedelta(hours=1)
        task = src.timing.Task("foo", "", [(start, now)])
        expected = (start, now, "foo", "")
        actual = src.listing.list_tasks(self.sqlite, task=task)
        self.assertEqual(len(actual), 1)
        actual = actual[0]
        self.assertEqual(actual[0], expected[0])
        self.assertTrue(actual[1] - now < timedelta(seconds=1))
        self.assertEqual(actual[2:], expected[2:])
