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
import typing

# third party imports
# library specific imports


class Task(typing.NamedTuple):
    """Typed named tuple Task."""

    name: str
    start: datetime.datetime
    end: datetime.datetime
    total: int
    tags: list


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
        return


class SQLite():
    """Eichhörnchen SQLite database interface.

    :cvar dict COLUMN_DEFS: SQLite column definitions
    :ivar str database: Eichhörnchen SQLite3 database
    """

    COLUMN_DEFS = {
        "tasks": (
            "name TEXT PRIMARY KEY",
            "start TIMESTAMP",
            "end TIMESTAMP",
            "total INT"
        ),
        "tags": (
            "text TEXT",
            "name TEXT",
            "FOREIGN KEY(name) REFERENCES tasks(name)"
        )
    }

    def __init__(self, database):
        """Initialize SQLite3 database interface.

        :param str database: Eichhörnchen SQLite3 database
        """
        self.database = database
        return

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
            msg = "connecting to database failed"
            raise SQLiteError(msg) from exception
        return connection

    def create_tables(self, connection=None, close=True):
        """Create tasks table.

        :param Connection connection: connection
        :param bool close: close database connection
        """
        if not connection:
            connection = self.connect()
        try:
            for table, column_def in self.COLUMN_DEFS.items():
                column_def = ", ".join(column_def)
                sql = f"CREATE TABLE IF NOT EXISTS {table} ({column_def})"
                connection.execute(sql)
                connection.commit()
        except sqlite3.Error as exception:
            msg = "create table statement failed"
            raise SQLiteError(msg, sql=sql) from exception
        finally:
            if close:
                connection.close()

    def insert(self, table, rows, connection=None, close=True):
        """Insert rows.

        :param str table: table
        :param list rows: rows
        :param Connection connection: database connection
        :param bool close: close database connection
        """
        if not connection:
            connection = self.connect()
        try:
            if table != "tags":
                placeholders = ", ".join(
                    "?" for _ in range(len(self.COLUMN_DEFS[table]))
                )
            else:
                placeholders = ", ".join(
                    "?" for _ in range(len(self.COLUMN_DEFS[table]) - 1)
                )
            sql = f"INSERT INTO {table} VALUES ({placeholders})"
            connection.executemany(sql, rows)
            connection.commit()
        except sqlite3.IntegrityError as exception:
            msg = "insert statement affected integrity of the database"
            raise SQLiteError(msg, sql=sql) from exception
        except sqlite3.Error as exception:
            msg = "insert statement failed"
            raise SQLiteError(msg, sql=sql) from exception
        finally:
            if close:
                connection.close()

    def select(
            self, table,
            column="", parameters=(), operator="=", connection=None, close=True
    ):
        """Select rows.

        :param str table: table
        :param str column: column
        :param tuple parameters: parameters
        :param str operator: operator
        :param Connection connection: database connection
        :param bool close: close database connection

        :returns: rows
        :rtype: list
        """
        if not connection:
            connection = self.connect()
        try:
            if column and parameters:
                sql = f"SELECT * FROM {table} WHERE {column} {operator} ?"
                cursor = connection.execute(sql, parameters)
            else:
                sql = f"SELECT * FROM {table}"
                cursor = connection.execute(sql)
            rows = list(cursor)
        except sqlite3.Error as exception:
            msg = "select statement failed"
            raise SQLiteError(msg, sql=sql) from exception
        finally:
            if close:
                connection.close()
        return rows

    def update(
            self, table, column0, parameters,
            column1="", connection=None, close=True
    ):
        """Update rows.

        :param str table: table
        :param str column0: column to be updated
        :param tuple parameters: parameters
        :param str column1: column WHERE clause
        :param Connection connection: database connection
        :param bool close: close database connection

        :returns: rows
        :rtype: list
        """
        if not connection:
            connection = self.connect()
        if column1:
            sql = f"UPDATE {table} SET {column0} = ? WHERE {column1} = ?"
        else:
            sql = f"UPDATE {table} SET {column0} = ?"
        try:
            connection.execute(sql, parameters)
        except sqlite3.Error as exception:
            msg = "update statement failed"
            raise SQLiteError(msg, sql=sql) from exception
        connection.commit()
        if column1 and column0 != column1:
            sql = (
                f"SELECT * FROM {table} "
                f"WHERE {column0} = ? AND {column1} = ?"
            )
            cursor = connection.execute(sql, parameters)
            rows = list(cursor)
        elif column1:
            rows = self.select(
                table,
                column=column0,
                parameters=(parameters[0],),
                connection=connection,
                close=close
            )
        else:
            rows = self.select(
                table, column=column0, connection=connection, close=close
            )
        return rows

    def delete(
            self, table, column, parameters,
            operator="=", connection=None, close=True
    ):
        """Delete rows.

        :param str table: table
        :param str column: column
        :param tuple parameters: parameters
        :param str operator: operator
        :param Connection connection: database connection
        :param bool close: close database connection
        """
        if not connection:
            connection = self.connect()
        sql = f"DELETE FROM {table} WHERE {column} {operator} ?"
        try:
            connection.execute(sql, parameters)
        except sqlite3.Error as exception:
            msg = "delete statement failed"
            raise SQLiteError(msg, sql=sql)
        connection.commit()
        if close:
            connection.close()
        return
