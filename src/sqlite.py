#    This file is part of Eichhörnchen 2.0.
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


TIME_SPAN_COLUMN_DEF = (
    "time_span", (
        "start TIMESTAMP PRIMARY KEY",
        "end TIMESTAMP CHECK (end > start)"
    )
)
TAGGED_COLUMN_DEF = (
    "tagged", (
        "tag TEXT",
        "start TIMESTAMP",
        "FOREIGN KEY(start) REFERENCES time_span(start)"
    )
)
RUNNING_COLUMN_DEF = (
    "running", (
        "name TEXT",
        "start TIMESTAMP",
        "FOREIGN KEY(start) REFERENCES time_span(start)"
    )
)
COLUMN_DEF = collections.OrderedDict(
    [TIME_SPAN_COLUMN_DEF, TAGGED_COLUMN_DEF, RUNNING_COLUMN_DEF]
)


def create_table(connection, table, close=True):
    """Create table.

    :param Connection connection: Eichhörnchen SQLite3 database connection
    :param str table: table
    :param bool close: toggle closing database connection on/off
    """
    try:
        column_def = ",".join(COLUMN_DEF[table])
        sql = f"CREATE TABLE IF NOT EXISTS {table} ({column_def})"
        connection.execute(sql)
        connection.commit()
    except sqlite3.Error as exception:
        raise SQLiteError(
            "create table statement failed", sql=sql
        ) from exception
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


class SQLite():
    """Eichhörnchen SQLite database interface.

    :ivar str database: Eichhörnchen SQLite3 database
    """

    def __init__(self, database):
        """Initialize SQLite3 database interface.

        :param str database: Eichhörnchen SQLite3 database
        """
        self.database = database

    def connect(self):
        """Connect to Eichhörnchen SQLite3 database.

        :returns: connection
        :rtype: Connection
        """
        try:
            connection = sqlite3.connect(
                self.database,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
        except sqlite3.Error as exception:
            raise SQLiteError(
                "connecting to Eichhörnchen SQLite3 database failed"
            ) from exception
        return connection
