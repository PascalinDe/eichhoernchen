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
:synopsis: SQLite utils.
"""


# standard library imports
import sqlite3
import collections

# third party imports
# library specific imports


class SQLiteError(Exception):
    """Raised when SQLite statement execution fails.

    :ivar str sql: SQLite statement
    """

    def __init__(self, *args, sql="", **kwargs):
        super().__init__(*args, **kwargs)
        self.sql = sql


class SQLiteInterface:
    """SQLite database interface.

    :ivar str database: SQLite database file
    """

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

    def __init__(self, database):
        """Initialize SQLite database interface.

        :param str database: SQLite database file
        """
        self.database = database

    def connect(self):
        """Connect to SQLite database.

        :raises: SQLiteError

        :returns: connection
        :rtype: Connection
        """
        try:
            return sqlite3.connect(
                self.database,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
        except sqlite3.Error as exception:
            raise SQLiteError("failed to connect to SQLite database") from exception

    def execute(self, statement, *parameters):
        """Execute SQLite statement.

        :param str statement: SQLite statement
        :param tuple parameters: parameters
        :raises: SQLiteError

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
                "failed to execute SQLite statement", sql=statement
            ) from exception
        connection.commit()
        return rows

    def create_tables(self):
        """Create tables."""
        for table, columns in self.COLUMN_DEFINITIONS.items():
            sql = f"CREATE TABLE IF NOT EXISTS {table} ({','.join(columns)})"
            self.execute(sql)
