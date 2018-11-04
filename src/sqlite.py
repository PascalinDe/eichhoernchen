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
:synopsis: Eichhörnchen SQLite3 database interface.
"""


# standard library imports
import sqlite3
import collections

# third party imports
# library specific imports


_Task = collections.namedtuple(
    "Task", ["name", "start", "end", "total", "due"]
)


class Task(_Task):      # pylint: disable=missing-docstring
    __slots__ = ()

    def __repr__(self):
        repr_ = "{name} ({start} - {end}, total: {total}) (due: {due})".format(
            name=self.name,
            start=self.start,
            end=self.end,
            total=self.total,
            due=self.due
        )
        return repr_


class SQLite():
    """Eichhörnchen SQLite database interface.

    :cvar str DATABASE: SQLite database
    :cvar str TABLE: SQLite table
    :cvar dict COLUMN_DEFS: SQLite column definitions
    """

    DATABASE = "eichhoernchen"
    TABLE = "tasks"
    COLUMN_DEFS = {
        "name": "TEXT PRIMARY KEY",
        "start": "TIMESTAMP",
        "end": "TIMESTAMP",
        "total": "TIMESTAMP",
        "due": "TIMESTAMP",
    }

    def __init__(self):
        """Initialize SQLite3 database interface."""
        return

    def connect(self):
        """Connect to Eichhörnchen SQLite3 database.

        :return: connection
        :rtype: Connect
        """
        connection = sqlite3.connect(
            self.DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES
        )
        connection.row_factory = sqlite3.Row
        return connection

    def create_table(self):
        """Create tasks table."""
        connection = self.connect()
        sql = "CREATE TABLE IF NOT EXISTS {table} ({column_defs})".format(
            table=self.TABLE,
            column_defs=", ".join(
                "{} {}".format(k, v) for k, v in self.COLUMN_DEFS.items()
            )
        )
        connection.execute(sql)
        connection.commit()
        connection.close()
        return

    def insert(self, rows):
        """Insert tasks.

        :param list rows: rows
        """
        connection = self.connect()
        sql = "INSERT INTO {table} VALUES ({columns})".format(
            table=self.TABLE,
            columns=", ".join(
                "?" for _ in self.COLUMN_DEFS.items()
            )
        )
        connection.executemany(sql, rows)
        connection.commit()
        connection.close()
        return
