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
    """Test typed named tuple Task.

    :ivar Task task: typed named tuple Task
    """

    def setUp(self):
        """Set test cases up.

        Trying: name = 'name', start = end = total = '00:00:00'
        and due = '2019-01-01'
        """
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d")
        self.task = src.sqlite.Task(
            "name", start, end, total, due
        )

    def test_field_types(self):
        """Test field types.

        Expecting: name = str, start = end = total = due = datetime.datetime
        """
        field_types = {
            "name": str,
            "start": datetime.datetime,
            "end": datetime.datetime,
            "total": datetime.datetime,
            "due": datetime.datetime
        }
        self.assertEqual(field_types, self.task._field_types)

    def test_attributes(self):
        """Test attributes."""
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d")
        self.assertEqual("name", self.task.name)
        self.assertEqual(start, self.task.start)
        self.assertEqual(end, self.task.end)
        self.assertEqual(total, self.task.total)
        self.assertEqual(due, self.task.due)


class TestSQLite(unittest.TestCase):
    """Test Eichhörnchen SQLite database interface.

    :ivar Task task: typed named tuple Task
    :ivar SQLite sqlite: Eichhörnchen SQLite database interface
    """

    def setUp(self):
        """Set test cases up."""
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d")
        self.task = src.sqlite.Task(
            "{name}", start, end, total, due
        )
        self.sqlite = src.sqlite.SQLite(":memory:")

    def test_connect(self):
        """Test connection to Eichhörnchen SQLite3 database.

        Expecting: Connection object
        """
        connection = self.sqlite.connect()
        self.assertIs(sqlite3.Connection, type(connection))

    def test_create_table(self):
        """Test table creation.

        Expecting: table exists
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

    def test_insert_many(self):
        """Test row insertion.

        Trying: insert n rows, 1 <= n <= 100
        Expecting: database contains n rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d")
        n = random.randint(1, 100)
        rows = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                due
            ) for index in range(n)
        ]
        self.sqlite.insert(rows, connection=connection, close=False)
        sql = "SELECT * FROM {table}".format(table=self.sqlite.TABLE)
        cursor = connection.execute(sql)
        self.assertEqual(
            rows, [src.sqlite.Task(*row) for row in list(cursor)]
        )

    def test_insert_empty(self):
        """Test empty list insertion.

        Trying: insert empty list
        Expecting: database contains 0 rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        self.sqlite.insert([], connection=connection, close=False)
        sql = "SELECT * FROM {table}".format(table=self.sqlite.TABLE)
        cursor = connection.execute(sql)
        self.assertEqual([], list(cursor))

    def test_select_many_existing(self):
        """Test one or more row(s) selection.

        Trying: insert n rows and select m rows, 1 <= n <= 100, 1 <= m <= n
        Expecting: result-set contains m rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        now = datetime.datetime.now()
        now = datetime.datetime.strptime(
            "{year}-{month}-{day}".format(
                year=str(now.year).zfill(4),
                month=str(now.month).zfill(2),
                day=str(now.day).zfill(2)
            ),
            "%Y-%m-%d"
        )
        due = datetime.datetime.strptime(
            "2019-01-01", "%Y-%m-%d"
        )
        n = random.randint(1, 100)
        m = random.randint(1, n)
        rows = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                now
            ) for index in range(m)
        ]
        padding = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                due
            ) for index in range(m, n)
        ]
        self.sqlite.insert(rows+padding, connection=connection, close=False)
        result_set = self.sqlite.select_many(
            column="due", parameters=(now,), connection=connection, close=False
        )
        self.assertEqual(rows, [src.sqlite.Task(*row) for row in result_set])

    def test_select_many_non_existing(self):
        """Test one or more row(s) selection.

        Trying: insert n rows and select non-existing rows, 1 <= n <= 100
        Expecting: empty result-set
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d")
        now = datetime.datetime.now()
        now = datetime.datetime.strptime(
            "{year}-{month}-{day}".format(
                year=str(now.year).zfill(4),
                month=str(now.month).zfill(2),
                day=str(now.day).zfill(2)
            ),
            "%Y-%m-%d"
        )
        n = random.randint(1, 100)
        rows = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                due
            ) for index in range(n)
        ]
        self.sqlite.insert(rows, connection=connection, close=False)
        result_set = self.sqlite.select_many(
            column="due", parameters=(now,), connection=connection, close=False
        )
        self.assertEqual([], result_set)

    def test_select_one_existing(self):
        """Test one row selection.

        Trying: insert 1 rows and select 1 existing row
        Expecting: result-set is 1 row
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime(
            "2019-01-01", "%Y-%m-%d"
        )
        rows = [src.sqlite.Task(name, start, end, total, due)]
        self.sqlite.insert(rows, connection=connection, close=False)
        result_set = self.sqlite.select_one(
            column="name",
            parameters=(name,),
            connection=connection,
            close=False
        )
        self.assertEqual(rows[0], src.sqlite.Task(*result_set))

    def test_select_one_non_existing(self):
        """Test one row selection.

        Trying: insert 1 row and select 1 non-existing row
        Expecting: result-set is None
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime(
            "2019-01-01", "%Y-%m-%d"
        )
        rows = [src.sqlite.Task(name, start, end, total, due)]
        self.sqlite.insert(rows, connection=connection, close=False)
        result_set = self.sqlite.select_one(
            column="name",
            parameters=("foo",),
            connection=connection,
            close=False
        )
        self.assertIs(result_set, None)

    def test_select_one_more_than_one(self):
        """Test one row selection.

        Trying: insert n rows and select m existing rows
        Expecting: SQLiteError
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        now = datetime.datetime.now()
        now = datetime.datetime.strptime(
            "{year}-{month}-{day}".format(
                year=str(now.year).zfill(4),
                month=str(now.month).zfill(2),
                day=str(now.day).zfill(2)
            ),
            "%Y-%m-%d"
        )
        due = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d")
        n = random.randint(1, 100)
        m = random.randint(1, n)
        rows = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                now
            ) for index in range(m)
        ]
        padding = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                due
            ) for index in range(m, n)
        ]
        self.sqlite.insert(rows+padding, connection=connection, close=False)
        with self.assertRaises(src.sqlite.SQLiteError):
            _ = self.sqlite.select_one(
                "due", (now,), connection=connection, close=False
            )

    def test_update_many_entire_column_existing(self):
        """Test entire column update.

        Trying: update entire column containing n rows, 1 <= n <= 100
        Expecting: result-set contains n rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime(
            "2019-01-01", "%Y-%m-%d"
        )
        now = datetime.datetime.now()
        now = datetime.datetime.strptime(
            "{year}-{month}-{day}".format(
                year=str(now.year).zfill(4),
                month=str(now.month).zfill(2),
                day=str(now.day).zfill(2)
            ),
            "%Y-%m-%d"
        )
        n = random.randint(1, 100)
        rows = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                due
            ) for index in range(n)
        ]
        self.sqlite.insert(rows, connection=connection, close=False)
        rows = [row._replace(due=now) for row in rows]
        result_set = self.sqlite.update_many(
            "due", parameters=(now,), connection=connection, close=False
        )
        self.assertEqual(rows, [src.sqlite.Task(*row) for row in result_set])

    def test_update_many_entire_column_non_existing(self):
        """Test entire column update.

        Trying: update entire non-existing column
        Expecting: SQLiteError
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime(
            "2019-01-01", "%Y-%m-%d"
        )
        n = random.randint(1, 100)
        rows = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                due
            ) for index in range(n)
        ]
        self.sqlite.insert(rows, connection=connection, close=False)
        with self.assertRaises(src.sqlite.SQLiteError):
            _ = self.sqlite.update_many(
                "foo", parameters=(name,), connection=connection, close=False
            )

    def test_update_many_existing(self):
        """Test one or more row(s) update.

        Trying: update m existing rows, 1 <= n <= 100, 1 <= m <= n
        Expecting: result-set contains m rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime(
            "2019-01-01", "%Y-%m-%d"
        )
        now = datetime.datetime.now()
        now = datetime.datetime.strptime(
            "{year}-{month}-{day}".format(
                year=str(now.year).zfill(4),
                month=str(now.month).zfill(2),
                day=str(now.day).zfill(2)
            ),
            "%Y-%m-%d"
        )
        n = random.randint(1, 100)
        m = random.randint(0, n)
        rows = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                now
            ) for index in range(m)
        ]
        padding = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                due
            ) for index in range(m, n)
        ]
        self.sqlite.insert(rows+padding, connection=connection, close=False)
        parameter = datetime.datetime.strptime("2018-01-01", "%Y-%m-%d")
        result_set = self.sqlite.update_many(
            "due",
            parameters=(parameter, due),
            column1="due",
            connection=connection,
            close=False
        )
        padding = [row._replace(due=parameter) for row in padding]
        self.assertEqual(
            padding, [src.sqlite.Task(*row) for row in result_set]
        )

    def test_update_many_non_existing(self):
        """Test one or more row(s) update.

        Trying: insert n rows, update 1 non-existing row, 1 <= n <= 100
        Expecting: empty result-set
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime(
            "2019-01-01", "%Y-%m-%d"
        )
        now = datetime.datetime.now()
        now = datetime.datetime.strptime(
            "{year}-{month}-{day}".format(
                year=str(now.year).zfill(4),
                month=str(now.month).zfill(2),
                day=str(now.day).zfill(2)
            ),
            "%Y-%m-%d"
        )
        n = random.randint(1, 100)
        rows = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                due
            ) for index in range(n)
        ]
        self.sqlite.insert(rows, connection=connection, close=False)
        result_set = self.sqlite.update_many(
            "due",
            parameters=(now, "foo"),
            column1="name",
            connection=connection,
            close=False
        )
        self.assertEqual([], result_set)

    def test_update_one_existing(self):
        """Test one row update.

        Trying: update 1 existing row
        Expecting: result-set is 1 row
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime(
            "2019-01-01", "%Y-%m-%d"
        )
        now = datetime.datetime.now()
        now = datetime.datetime.strptime(
            "{year}-{month}-{day}".format(
                year=str(now.year).zfill(4),
                month=str(now.month).zfill(2),
                day=str(now.day).zfill(2)
            ),
            "%Y-%m-%d"
        )
        task = src.sqlite.Task(name, start, end, total, due)
        self.sqlite.insert([task], connection=connection, close=False)
        result_set = self.sqlite.update_one(
            "due",
            parameters=(now, due),
            column1="due",
            connection=connection,
            close=False
        )
        self.assertEqual(task._replace(due=now), src.sqlite.Task(*result_set))

    def test_update_one_non_existing(self):
        """Test one row update.

        Trying: update 1 non-existing row
        Expecting: result-set is None
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "foo"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        now = datetime.datetime.now()
        now = datetime.datetime.strptime(
            "{year}-{month}-{day}".format(
                year=str(now.year).zfill(4),
                month=str(now.month).zfill(2),
                day=str(now.day).zfill(2)
            ),
            "%Y-%m-%d"
        )
        task = src.sqlite.Task(name, start, end, total, now)
        self.sqlite.insert([task], connection=connection, close=False)
        result_set = self.sqlite.update_one(
            "name",
            parameters=("bar", "baz"),
            column1="name",
            connection=connection,
            close=False
        )
        self.assertEqual(None, result_set)

    def test_delete_existing(self):
        """Test row deletion.

        Trying: delete n existing rows, 1 <= n <= 100
        Expecting: database contains 0 rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime(
            "2019-01-01", "%Y-%m-%d"
        )
        n = random.randint(1, 100)
        rows = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                due
            ) for index in range(n)
        ]
        self.sqlite.insert(rows, connection=connection, close=False)
        self.sqlite.delete(
            "due", parameters=(due,), connection=connection, close=False
        )
        sql = "SELECT * FROM {table}".format(table=self.sqlite.TABLE)
        result_set = connection.execute(sql).fetchall()
        self.assertEqual(0, len(result_set))

    def test_delete_non_existing(self):
        """Test row deletion.

        Trying: delete non-existing rows, 1 <= n <= 100
        Expecting: database contains n rows
        """
        connection = self.sqlite.connect()
        self.sqlite.create_table(connection=connection, close=False)
        name = "name_{index}"
        start = end = total = datetime.datetime.strptime(
            "00:00:00", "%H:%M:%S"
        )
        due = datetime.datetime.strptime(
            "2019-01-01", "%Y-%m-%d"
        )
        n = random.randint(1, 100)
        rows = [
            src.sqlite.Task(
                name.format(index=str(index).zfill(3)),
                start,
                end,
                total,
                due
            ) for index in range(n)
        ]
        self.sqlite.insert(rows, connection=connection, close=False)
        self.sqlite.delete(
            "name", parameters=("foo",), connection=connection, close=False
        )
        sql = "SELECT * FROM {table}".format(table=self.sqlite.TABLE)
        result_set = connection.execute(sql).fetchall()
        self.assertEqual(n, len(result_set))
