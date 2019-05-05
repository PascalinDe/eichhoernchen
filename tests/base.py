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
:synopsis: Testing base class(es).
"""


# standard library imports
import os
import os.path
import unittest

# third party imports
# library specific imports
import src.sqlite


class BaseTesting(unittest.TestCase):
    """Testing base class.

    :cvar str DATABASE: Eichhörnchen SQLite3 testing database
    :ivar SQLite sqlite: Eichhörnchen SQLite3 testing database interface
    """
    DATABASE = "testing.db"

    def setUp(self):
        """Set test cases up."""
        self.sqlite = src.sqlite.SQLite(self.DATABASE)
        for table in self.sqlite.COLUMN_DEF:
            self.sqlite.create_table(table)

    def tearDown(self):
        """Tear down test cases."""
        if os.path.exists(self.DATABASE):
            os.remove(self.DATABASE)
