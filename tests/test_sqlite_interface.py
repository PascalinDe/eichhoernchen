#    This file is part of Eichhörnchen 2.2.
#    Copyright (C) 2018-2021  Carine Dengler
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
:synopsis: SQLite database interface.
"""


# standard library imports
import os
import sqlite3
import unittest

# third party imports
# library specific imports
import src.sqlite_interface


class TestSQLiteInterface(unittest.TestCase):
    """Test SQLite database interface.

    :ivar SQLiteInterface interface: SQLite database interface
    """

    def setUp(self):
        """Set up SQLite database interface test cases."""
        self.interface = src.sqlite_interface.SQLiteInterface(
            os.path.join(os.getcwd(), "temp.db")
        )

    def tearDown(self):
        """Tear down SQLite database interface test cases."""
        try:
            os.unlink(os.path.join(os.getcwd(), "temp.db"))
        except FileNotFoundError:
            pass

    def test_connect(self):
        """Test SQLite database connection.

        Trying: connecting to database
        Expecting: Connection object
        """
        self.assertIsInstance(self.interface.connect(), sqlite3.Connection)

    def test_create_tables(self):
        """Test table creation.

        Trying: creating tables
        Expecting: tables exist
        """
        self.interface.create_tables()
        connection = self.interface.connect()
        self.assertEqual(
            [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            ],
            list(src.sqlite_interface.COLUMN_DEFINITIONS.keys()),
        )
