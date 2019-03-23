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
import sqlite3
import datetime
import unittest

# third party imports
# library specific imports
import src.sqlite


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

    def test_create_tables(self):
        """Test table creation.

        Expecting: table exists
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
        self.assertEqual(
            [row[0] for row in cursor], list(self.sqlite.COLUMN_DEFS.keys())
        )

    def test_insert_many(self):
        """Test row insertion.

        Trying: insert 3 rows
        Expecting: database contains 3 rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        start = end = datetime.datetime.now()
        rows = [
            ("foo", start, end, 0),
            ("bar", start, end, 0),
            ("baz", start, end, 0)
        ]
        self.sqlite.insert("tasks", rows, connection=connection, close=False)
        cursor = connection.execute("SELECT * FROM tasks")
        self.assertEqual(list(cursor), rows)

    def test_insert_empty(self):
        """Test empty list insertion.

        Trying: insert empty list
        Expecting: database contains 0 rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        self.sqlite.insert("tasks", [], connection=connection, close=False)
        cursor = connection.execute("SELECT * FROM tasks")
        self.assertEqual(list(cursor), [])

    def test_select_existing(self):
        """Test one or more row(s) selection.

        Trying: insert 2 rows and select 1 row
        Expecting: result-set contains 1 row
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        start = end = datetime.datetime.now()
        rows = [
            ("foo", start, end, 0),
            ("bar", start, end, 0)
        ]
        self.sqlite.insert("tasks", rows, connection=connection, close=False)
        actual = self.sqlite.select(
            "tasks",
            column="name",
            parameters=("foo",),
            connection=connection,
            close=False
        )
        self.assertEqual(actual, [rows[0]])

    def test_select_non_existing(self):
        """Test one or more row(s) selection.

        Trying: insert 2 rows and select non-existing rows
        Expecting: empty result-set
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        start = end = datetime.datetime.now()
        rows = [
            ("foo", start, end, 0),
            ("bar", start, end, 0)
        ]
        self.sqlite.insert("tasks", rows, connection=connection, close=False)
        actual = self.sqlite.select(
            "tasks",
            column="name",
            parameters=("baz",),
            connection=connection,
            close=False
        )
        self.assertEqual(actual, [])

    def test_update_entire_column_existing(self):
        """Test one or more row(s) update.

        Trying: update entire column containing 3 rows
        Expecting: result-set contains 3 rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        start = end = datetime.datetime.now()
        rows = [
            ("foo", start, end, 0),
            ("bar", start, end, 0),
            ("baz", start, end, 0)
        ]
        self.sqlite.insert("tasks", rows, connection=connection, close=False)
        expected = [row[:-1] + (1,) for row in rows]
        actual = self.sqlite.update(
            "tasks", "total",
            parameters=(1,), connection=connection, close=False
        )
        self.assertEqual(actual, expected)

    def test_update_entire_column_non_existing(self):
        """Test one or more row(s) update.

        Trying: update entire non-existing column
        Expecting: SQLiteError
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        start = end = datetime.datetime.now()
        rows = [
            ("foo", start, end, 0),
            ("bar", start, end, 0)
        ]
        self.sqlite.insert("tasks", rows, connection=connection, close=False)
        with self.assertRaises(src.sqlite.SQLiteError):
            self.sqlite.update(
                "tasks", "baz",
                parameters=("foobar",), connection=connection, close=False
            )

    def test_update_one_existing(self):
        """Test one or more row(s) update.

        Trying: update 1 existing row
        Expecting: result-set contains 1 row
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        start = end = datetime.datetime.now()
        rows = [
            ("foo", start, end, 0),
            ("bar", start, end, 0)
        ]
        self.sqlite.insert("tasks", rows, connection=connection, close=False)
        expected = [
            ("baz",) + rows[0][1:],
        ]
        actual = self.sqlite.update(
            "tasks",
            "name",
            parameters=("baz", "foo"),
            column1="name",
            connection=connection,
            close=False
        )
        self.assertTrue(set(expected).issubset(set(actual)))

    def test_update_one_non_existing(self):
        """Test one or more row(s) update.

        Trying: update 1 non-existing row
        Expecting: empty result-set
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        start = end = datetime.datetime.now()
        rows = [
            ("foo", start, end, 0),
            ("bar", start, end, 0)
        ]
        self.sqlite.insert("tasks", rows, connection=connection, close=False)
        actual = self.sqlite.update(
            "tasks",
            "name",
            parameters=("foobar", "baz"),
            column1="name",
            connection=connection,
            close=False
        )
        self.assertEqual(actual, [])

    def test_delete_existing(self):
        """Test row deletion.

        Trying: delete 1 out of 3 existing rows
        Expecting: database contains 2 rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        start = end = datetime.datetime.now()
        rows = [
            ("foo", start, end, 0),
            ("bar", start, end, 0),
            ("baz", start, end, 0)
        ]
        self.sqlite.insert("tasks", rows, connection=connection, close=False)
        self.sqlite.delete(
            "tasks", "name",
            parameters=("foo",), connection=connection, close=False
        )
        actual = connection.execute("SELECT * FROM tasks").fetchall()
        expected = rows[1:]
        self.assertEqual(actual, expected)

    def test_delete_non_existing(self):
        """Test row deletion.

        Trying: delete 1 non-existing rows
        Expecting: database contains 3 rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_tables(connection=connection, close=False)
        start = end = datetime.datetime.now()
        rows = [
            ("foo", start, end, 0),
            ("bar", start, end, 0),
            ("baz", start, end, 0)
        ]
        self.sqlite.insert("tasks", rows, connection=connection, close=False)
        self.sqlite.delete(
            "tasks", "name",
            parameters=("foobar",), connection=connection, close=False
        )
        actual = connection.execute("SELECT * FROM tasks").fetchall()
        self.assertEqual(actual, rows)
