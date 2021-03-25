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
:synopsis: Eichhörnchen SQLite3 database interface.
"""


# standard library imports
import sqlite3
import collections

# third party imports
# library specific imports

TIME_SPAN_COLUMN_DEF = (
    "time_span",
    ("start TIMESTAMP PRIMARY KEY", "end TIMESTAMP CHECK (end > start)"),
)
TAGGED_COLUMN_DEF = (
    "tagged",
    ("tag TEXT", "start TIMESTAMP", "FOREIGN KEY(start) REFERENCES time_span(start)"),
)
RUNNING_COLUMN_DEF = (
    "running",
    ("name TEXT", "start TIMESTAMP", "FOREIGN KEY(start) REFERENCES time_span(start)"),
)
COLUMN_DEF = collections.OrderedDict(
    (TIME_SPAN_COLUMN_DEF, TAGGED_COLUMN_DEF, RUNNING_COLUMN_DEF)
)


def create_table(connection, table, close=True):
    """Create table.

    :param Connection connection: SQLite3 database connection
    :param str table: table
    :param bool close: toggle closing database connection on/off

    :raises ValueError: when table is not defined
    """
    try:
        sql = f"CREATE TABLE IF NOT EXISTS {table} " f"({','.join(COLUMN_DEF[table])})"
        connection.execute(sql)
        connection.commit()
    except sqlite3.Error as exception:
        raise SQLiteError("failed to create table", sql=sql) from exception
    except KeyError:
        raise ValueError(f"'{table}' is not defined")
    finally:
        if close:
            connection.close()


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


class SQLite:
    """SQLite database interface.

    :ivar str database: SQLite3 database name
    """

    def __init__(self, database):
        """Initialize SQLite3 database interface.

        :param str database: path to SQLite3 database
        """
        self.database = database

    def connect(self):
        """Connect to SQLite3 database.

        :raises SQLiteError: when connection to SQLite3 database fails

        :returns: connection
        :rtype: Connection
        """
        try:
            return sqlite3.connect(
                self.database,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
        except sqlite3.Error as exception:
            raise SQLiteError("failed to connect to SQLite3 database") from exception

    def create_database(self):
        """Create SQLite3 database."""
        connection = self.connect()
        for table in COLUMN_DEF:
            create_table(connection, table, close=False)
        connection.close()

    def execute(self, statement, *parameters):
        """Execute SQLite3 statement(s).

        :param str statement: SQLite3 statement
        :param tuple parameters: parameters

        :raises SQLiteError: when SQLite3 statement execution fails

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
                "failed to execute SQLite3 statement", sql=statement
            ) from exception
        connection.commit()
        return rows
