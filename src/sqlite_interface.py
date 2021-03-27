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
import sqlite3
import collections

# third party imports
# library specific imports


COLUMN_DEFINITIONS = collections.OrderedDict(
    {
        "time_span": (
            "start TIMESTAMP PRIMARY KEY",
            "end TIMESTAMP CHECK (end > start)",
        ),
        "tagged": (
            "tag TEXT",
            "start TIMESTAMP",
            "FOREIGN KEY(start) REFERENCES time_span(start)",
        ),
        "running": (
            "name TEXT",
            "start TIMESTAMP",
            "FOREIGN KEY(start) REFERENCES time_span(start)",
        ),
    }
)


class SQLiteError(Exception):
    """Raised when SQLite statement execution fails.

    :ivar str sql: SQLite statement
    """

    def __init__(self, *args, sql="", **kwargs):
        """Initialize SQLiteError.

        :param str sql: SQLite statement
        """
        super().__init__(*args, **kwargs)
        self.sql = sql


class SQLiteInterface:
    """SQLite database interface.

    :ivar str database: SQLite database file
    """

    def __init__(self, database):
        """Initialize SQLite database interface.

        :param str database: SQLite database file
        """
        self.database = database

    def connect(self):
        """Connect to SQLite database.

        :raises SQLiteError: when connection to SQLite database fails

        :returns: connection
        :rtype: Connection
        """
        try:
            return sqlite3.connect(
                self.database,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
        except sqlite3.Error as exception:
            raise SQLiteError("connection to SQLite database failed") from exception

    def execute(self, statement, *parameters):
        """Execute SQLite statement(s).

        :param str statement: SQLite statement
        :param tuple parameters: parameters

        :raises SQLiteError: when SQLite statement execution fails

        :returns: rows
        :rtype: list
        """
        try:
            connection = self.connect()
            if len(parameters) > 1:
                rows = connection.executemany(statement, parameters).fetchall()
            else:
                rows = connection.execute(statement, *parameters).fetchall()
        except sqlite3.Error as exception:
            raise SQLiteError(
                "SQLite statement execution failed", sql=statement
            ) from exception
        connection.commit()
        return rows

    def create_tables(self):
        """Create tables."""
        for table, columns in COLUMN_DEFINITIONS.items():
            sql = f"CREATE TABLE IF NOT EXISTS {table} ({','.join(columns)})"
            self.execute(sql)
