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
    due: datetime.datetime

    def __str__(self):
        hours = self.total // 3600
        minutes = (self.total % 3600) // 60
        return (
            f"{self.name} ({self.start} - {self.end}, "
            f"total : {hours}h{minutes}m)"
        )


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

    :cvar str TABLE: SQLite table
    :cvar dict COLUMN_DEFS: SQLite column definitions
    :ivar str database: Eichhörnchen SQLite3 database
    """

    TABLE = "tasks"
    COLUMN_DEFS = {
        "name": "TEXT PRIMARY KEY",
        "start": "TIMESTAMP",
        "end": "TIMESTAMP",
        "total": "INT",
        "due": "TIMESTAMP",
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
            connection.row_factory = sqlite3.Row
        except sqlite3.Error as exception:
            msg = "connecting to database failed"
            raise SQLiteError(msg) from exception
        return connection

    def create_table(self, connection=None, close=True):
        """Create tasks table.

        :param Connection connection: connection
        :param bool close: close database connection
        """
        if not connection:
            connection = self.connect()
        try:
            column_defs=", ".join(
                f"{k} {v}" for k, v in self.COLUMN_DEFS.items()
            )
            sql = f"CREATE TABLE IF NOT EXISTS {self.TABLE} ({column_defs})"
            connection.execute(sql)
            connection.commit()
        except sqlite3.Error as exception:
            msg = "create table statement failed"
            raise SQLiteError(msg, sql=sql) from exception
        finally:
            if close:
                connection.close()

    def insert(self, rows, connection=None, close=True):
        """Insert rows.

        :param list rows: rows
        :param Connection connection: database connection
        :param bool close: close database connection
        """
        if not connection:
            connection = self.connect()
        try:
            columns=", ".join("?" for _ in self.COLUMN_DEFS.items())
            sql = f"INSERT INTO {self.TABLE} VALUES ({columns})"
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

    def select_many(
            self,
            column="", parameters=(), operator="=", connection=None, close=True
    ):
        """Select rows.

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
                sql = f"SELECT * FROM {self.TABLE} WHERE {column} {operator} ?"
                cursor = connection.execute(sql, parameters)
            else:
                sql = f"SELECT * FROM {self.TABLE}"
                cursor = connection.execute(sql)
            rows = [tuple(row) for row in cursor]
        except sqlite3.Error as exception:
            msg = "select statement failed"
            raise SQLiteError(msg, sql=sql) from exception
        finally:
            if close:
                connection.close()
        return rows

    def select_one(
            self, column, parameters,
            operator="=", connection=None, close=True
    ):
        """Select row.

        :param str column: column
        :param tuple parameters: parameters
        :param str operator: operator
        :param Connection: connection: database connection
        :param bool close: close database connection

        :returns: row or None
        :rtype: tuple or None
        """
        rows = self.select_many(
            column=column,
            parameters=parameters,
            operator=operator,
            connection=connection,
            close=close
        )
        if len(rows) > 1:
            raise SQLiteError("result-set contains more than one row")
        elif len(rows) == 1:
            row = rows[0]
        else:
            row = None
        return row

    def update_many(
            self, column0, parameters, column1="", connection=None, close=True
    ):
        """Update rows.

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
            sql = f"UPDATE {self.TABLE} SET {column0} = ? WHERE {column1} = ?"
        else:
            sql = f"UPDATE {self.TABLE} SET {column0} = ?"
        try:
            connection.execute(sql, parameters)
        except sqlite3.Error as exception:
            msg = "update statement failed"
            raise SQLiteError(msg, sql=sql) from exception
        connection.commit()
        if column1:
            parameters = (parameters[0],)
        else:
            parameters = ()
        rows = self.select_many(
            column=column0,
            parameters=parameters,
            connection=connection,
            close=close
        )
        return rows

    def update_one(
            self, column0, column1, parameters, connection=None, close=True
    ):
        """Update row.

        :param str column0: column to be updated
        :param str column1: column WHERE clause
        :param tuple parameters: parameters
        :param Connection connection: database connection
        :param bool close: close database connection

        :returns: row or None
        :rtype: tuple or None
        """
        rows = self.update_many(
            column0, parameters,
            column1=column1, connection=connection, close=close
        )
        if len(rows) > 1:
            raise SQLiteError("result-set contains more than one row")
        elif len(rows) == 1:
            row = rows[0]
        else:
            row = None
        return row

    def delete(
            self, column, parameters,
            operator="=", connection=None, close=True
    ):
        """Delete rows.

        :param str column: column
        :param tuple parameters: parameters
        :param str operator: operator
        :param Connection connection: database connection
        :param bool close: close database connection
        """
        if not connection:
            connection = self.connect()
        sql = f"DELETE FROM {self.TABLE} WHERE {column} {operator} ?"
        try:
            connection.execute(sql, parameters)
        except sqlite3.Error as exception:
            msg = "delete statement failed"
            raise SQLiteError(msg, sql=sql)
        connection.commit()
        if close:
            connection.close()
        return
