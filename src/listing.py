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
:synopsis: Listing.
"""


# standard library imports
from datetime import datetime

# third party imports

# library specific imports
from src import Task


def select_today(sqlite):
    """Select today's tasks.

    :param SQLite sqlite: Eichhörnchen SQLite database interface

    :returns: list of today's tasks
    :rtype: list
    """
    connection = sqlite.connect()
    sql = (
        "SELECT start,end,name,text FROM time_span "
        "WHERE start >= datetime('now','localtime','start of day')"
    )
    rows = connection.execute(sql).fetchall()
    return rows


def list_tasks(sqlite, task=Task("", "", []), today=True):
    """List tasks.

    :param Task task: current task
    :param bool today: toggle listing today's tasks on/off

    :returns: list of tasks
    :rtype: list
    """
    if today:
        rows = select_today(sqlite)
    else:
        connection = sqlite.connect()
        rows = connection.execute(
            "SELECT start,end,name,text FROM time_span"
        ).fetchall()
    if task.name:
        start, _ = sorted(task.time_span, key=lambda x: x[0], reverse=True)[0]
        now = datetime.now()
        rows.append((start, now, task.name, task.tag))
    return rows
