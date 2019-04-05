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
import datetime

# third party imports
# library specific imports


class SQLiteError(Exception):
    """Raised when SQL statement execution fails.

    :ivar str sql: SQL statement
    """

    def __init__(self, *args, sql="", **kwargs):
        """Initialize SQLiteError.

        :param str sql: SQL statement
        """
        super().__init__(*args, **kwargs)
        self.sql = sql


class SQLite(object):
    """Eichhörnchen SQLite database interface.

    :cvar dict COLUMN_DEF: SQLite column definitions
    :ivar str database: Eichhörnchen SQLite3 database
    """
    COLUMN_DEF = {
        "task": ("name TEXT PRIMARY KEY",),
        "tag": (
            "text TEXT PRIMARY KEY",
            "name TEXT",
            "FOREIGN KEY(name) REFERENCES task(name)"
        ),
        "time_span": (
            "start TIMESTAMP",
            "end TIMESTAMP",
            "name TEXT",
            "text TEXT",
            "FOREIGN KEY(name) REFERENCES task(name)",
            "FOREIGN KEY(text) REFERENCES tag(text)"
        )
    }

    def __init__(self, database):
        """Initialize SQLite3 database interface.

        :param str database: Eichhörnchen SQLite3 database
        """
        self.database = database

    def connect(self):
        """Connect to Eichhörnchen SQLite3 database.

        :return: connection
        :rtype: Connection
        """
        try:
            connection = sqlite3.connect(
                self.database,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
        except sqlite3.Error as exception:
            raise SQLiteError("connecting failed")
        return connection

    def create_table(self, table, connection=None, close=True):
        """Create table.

        :param str table: table
        :param Connection connection: connection
        :param bool close: toggle closing database connection on/off
        """
        if not connection:
            connection = self.connect()
        try:
            column_def = ",".join(self.COLUMN_DEF[table])
            sql = f"CREATE TABLE IF NOT EXISTS {table} ({column_def})"
            connection.execute(sql)
            connection.commit()
        except sqlite3.Error as exception:
            raise SQLiteError(
                "create table statement failed", sql=sql
            ) from exception
        except KeyError as exception:
            raise ValueError(f"'{table}' is not defined")
        finally:
            if close:
                connection.close()
