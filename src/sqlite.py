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
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
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
        """Insert rows.

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

    def select_many(self, column="", parameters=(), operator="="):
        """Select rows.

        :param str column: column
        :param tuple parameters: parameters
        :param str operator: operator

        :returns: rows
        :rtype: list
        """
        connection = self.connect()
        if column and parameters:
            sql = "SELECT * FROM {table} WHERE {column} {operator} ?"
            sql = sql.format(
                table=self.TABLE, column=column, operator=operator
            )
            cursor = connection.execute(sql, parameters)
        else:
            sql = "SELECT * FROM {table}".format(table=self.TABLE)
            cursor = connection.execute(sql)
        rows = [tuple(row) for row in cursor]
        return rows

    def select_one(self, column, parameters, operator="="):
        """Select row.

        :param str column: column
        :param tuple parameters: parameters
        :param str operator: operator

        :returns: row or None
        :rtype: tuple or None
        """
        rows = self.select_many(
            column=column, parameters=parameters, operator=operator
        )
        if len(rows) > 1:
            raise RuntimeError("result-set contains more than one row")
        elif len(rows) == 1:
            rows = rows[0]
        else:
            row = None
        return row

    def update_many(self, column0, parameters, column1=""):
        """Update rows.

        :param str column0: column to be updated
        :param tuple parameters: parameters
        :param str column1: column WHERE clause

        :returns: rows
        :rtype: list
        """
        connection = self.connect()
        if column1:
            sql = "UPDATE {table} SET {column0} = ? WHERE {column1} = ?"
            sql = sql.format(
                table=self.TABLE, column0=column0, column1=column1
            )
        else:
            sql = "UPDATE {table} SET {column0} = ?"
            sql = sql.format(table=self.TABLE, column0=column0)
        connection.executemany(sql, parameters)
        connection.commit()
        connection.close()
        if column1:
            parameters = [(row[1],) for row in parameters]
        rows = [
            self.select_many(column=column1, parameters=row)
            for row in parameters
        ]
        return rows

    def update_one(self, column0, column1, parameters):
        """Update row.

        :param str column0: column to be updated
        :param str column1: column WHERE clause
        :param tuple parameters: parameters

        :returns: row or None
        :rtype: tuple or None
        """
        rows = self.update_many(
            column0, (parameters,), column1=column1
        ).pop(0)
        if len(rows) > 1:
            raise RuntimeError("result-set contains more than one row")
        elif len(rows) == 1:
            row = rows[0]
        else:
            row = None
        return row

    def delete(self, column, parameters, operator="="):
        """Delete rows.

        :param str column: column
        :param tuple parameters: parameters
        :param str operator: operator
        """
        connection = self.connect()
        sql = "DELETE FROM {table} WHERE {column} {operator} ?"
        sql = sql.format(table=self.TABLE, column=column, operator=operator)
        connection.executemany(sql, parameters)
        connection.commit()
        connection.close()
        return
