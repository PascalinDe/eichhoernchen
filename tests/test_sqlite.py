#    This file is part of Eichhörnchen 1.2.
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
import unittest

# third party imports
# library specific imports
import src.sqlite


class TestSQLite(unittest.TestCase):
    """Test Eichhörnchen SQLite database interface.

    :ivar SQLite sqlite: Eichhörnchen SQLite database interface
    """

    def setUp(self):
        """Initialize SQLite database interface."""
        self.sqlite = src.sqlite.SQLite(":memory:")

    def test_connect(self):
        """Test connecting to Eichhörnchen SQLite database.

        Trying: connecting to database
        Expecting: Connection object
        """
        connection = self.sqlite.connect()
        self.assertIs(sqlite3.Connection, type(connection))

    def test_create_table(self):
        """Test table creation.

        Trying: creating table(s)
        Expecting: table(s) exists
        """
        connection = self.sqlite.connect()
        for table in src.sqlite.COLUMN_DEF:
            src.sqlite.create_table(connection, table, close=False)
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
        self.assertEqual(
            [row[0] for row in cursor], list(src.sqlite.COLUMN_DEF.keys())
        )
