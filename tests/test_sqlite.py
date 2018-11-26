#    This file is part of Eichhörnchen 1.0.
#    Copyright (C) 2018  Carine Dengler
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
:synopsis: Eichhörnchen SQLite3 database interface tests.
"""


# standard library imports
import random
import sqlite3
import datetime
import unittest

# third party imports
# library specific imports
import src.sqlite


class TestTask(unittest.TestCase):
    """Test named tuple Task."""

    def test_named_tuple(self):
        """Test named tuple Task.

        Trying:
        name = 'name', start, end, total = '00:00:00' and due = '2019-01-01'
        Expecting: corresponding attribute values
        """
        name = "name"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d")
        task = src.sqlite.Task(name, start, end, total, due)
        self.assertEqual(name, task.name)
        self.assertEqual(start, task.start)
        self.assertEqual(end, task.end)
        self.assertEqual(total, task.total)
        self.assertEqual(due, task.due)


class TestSQLite(unittest.TestCase):
    """Test Eichhörnchen SQLite database interface.

    :ivar SQLite sqlite: Eichhörnchen SQLite database interface
    """

    def setUp(self):
        """Set test cases up."""
        self.sqlite = src.sqlite.SQLite(":memory:")

    def test_connect(self):
        """Test connection to Eichhörnchen SQLite3 database.

        Expecting: Connection object
        """
        connection = self.sqlite.connect()
        self.assertIs(sqlite3.Connection, type(connection))

    def test_create_table(self):
        """Test tasks table creation.

        Expecting: tasks table
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        sql = (
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='{name}'"
        ).format(name=self.sqlite.TABLE)
        cursor = connection.execute(sql)
        self.assertEqual(1, len(list(cursor)))
        connection.close()

    def test_insert_00(self):
        """Test row insertion.

        Trying: insert n rows, 0 <= n <= 100
        Expecting: n rows inserted
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d")
        n = random.randint(0, 100)
        rows = [
            src.sqlite.Task(name.format(index=index), start, end, total, due)
            for index in range(n)
        ]
        self.sqlite.insert(rows, connection, close=False)
        sql = "SELECT * FROM {table}".format(table=self.sqlite.TABLE)
        cursor = connection.execute(sql)
        self.assertEqual(n, len(list(cursor)))

    def test_insert_01(self):
        """Test row insertion.

        Trying:
        name = 'name', start, end, total = '00:00:00' and due = '2019-01-01'
        Expecting: corresponding row
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d")
        task = src.sqlite.Task(name, start, end, total, due)
        self.sqlite.insert([task], connection, close=False)
        sql = "SELECT * FROM {table}".format(table=self.sqlite.TABLE)
        row = src.sqlite.Task(*next(connection.execute(sql)))
        self.assertEqual(task, row)
