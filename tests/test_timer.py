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
:synopsis: Timer test cases.
"""


# standard library imports
import csv
import json
import datetime
import unittest
import os
import os.path

# third party imports
# library specific imports
import src.timer
import src.sqlite_interface

from src import FullName, Task


class TestTimer(unittest.TestCase):
    """Timer test cases.

    :cvar str DATABASE: SQLite database file
    """

    DATABASE = "test.db"

    def tearDown(self):
        """Tear down test cases."""
        try:
            os.remove(self.DATABASE)
        except FileNotFoundError:
            pass

    def test_start(self):
        """Test starting task.

        Trying: start task
        Expecting: task has been started
        """
        timer = src.timer.Timer(self.DATABASE)
        name = "foo"
        tags = {"bar", "baz"}
        timer.start(Task(name, tags, tuple()))
        for actual, expected in (
            (timer.task.name, name),
            (timer.task.tags, tags),
        ):
            self.assertEqual(actual, expected)
        for columns, table in (
            ("start,end", "time_span"),
            ("name", "running"),
            ("tag", "tagged"),
        ):
            rows = timer.interface.execute(
                f"SELECT {columns} FROM {table} WHERE start=?",
                (timer.task.time_span[0],),
            )
            if table == "time_span":
                expected_len = 1
                actual_columns = rows[0]
                expected_columns = timer.task.time_span
            if table == "running":
                expected_len = 1
                actual_columns = rows[0]
                expected_columns = (name,)
            if table == "tagged":
                expected_len = 2
                actual_columns = ({x for row in rows for x in row},)
                expected_columns = (tags,)
            self.assertEqual(len(rows), expected_len)
            self.assertEqual(actual_columns, expected_columns)

    def test_stop(self):
        """Test stopping task.

        Trying: stop task
        Expecting: task has been stopped
        """
        timer = src.timer.Timer(self.DATABASE)
        name = "foo"
        timer.start(Task(name, frozenset(), tuple()))
        timer.stop()
        self.assertFalse(any(timer.task))
        start, end = timer.interface.execute(
            """SELECT time_span.start,end
            FROM time_span
            JOIN running ON time_span.start=running.start
            WHERE name=?""",
            (name,),
        ).pop(0)
        self.assertTrue(end > start)

    def test_edit_name(self):
        """Test editing task.

        Trying: edit name
        Expecting: name has been updated
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(Task("foo", frozenset(), tuple()))
        task = timer.task
        timer.stop()
        name = "bar"
        timer.edit(task, "name", name)
        self.assertEqual(
            *timer.interface.execute(
                "SELECT name FROM running WHERE start=?", (task.time_span[0],)
            ),
            (name,),
        )

    def test_edit_tags(self):
        """Test editing task.

        Trying: edit task
        Expecting: tags have been updated
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(Task("foo", {"bar"}, tuple()))
        task = timer.task
        timer.stop()
        tags = {"bar", "baz"}
        timer.edit(task, "tags", tags)
        self.assertCountEqual(
            (
                x
                for row in timer.interface.execute(
                    "SELECT tag FROM tagged WHERE start=?", (task.time_span[0],)
                )
                for x in row
            ),
            tags,
        )

    def test_edit_start(self):
        """Test editing task.

        Trying: edit start
        Expecting: start has been updated
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(Task("foo", frozenset(), tuple()))
        task = timer.task
        timer.stop()
        minutes = datetime.timedelta(minutes=1)
        task = Task(
            task.name,
            task.tags,
            task.time_span,
        )
        start = task.time_span[0] - minutes
        timer.edit(task, "start", start)
        for table in ("time_span", "running"):
            statement = f"SELECT 1 FROM {table} WHERE start=?"
            self.assertFalse(timer.interface.execute(statement, (task.time_span[0],)))
            self.assertTrue(timer.interface.execute(statement, (start,)))

    def test_edit_end(self):
        """Test editing task.

        Trying: edit end
        Expecting: end has been updated
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(Task("foo", frozenset(), tuple()))
        task = timer.task
        timer.stop()
        minutes = datetime.timedelta(minutes=1)
        task = Task(
            task.name,
            task.tags,
            (task.time_span[0], task.time_span[0] + minutes),
        )
        end = task.time_span[1] + minutes
        timer.edit(task, "end", end)
        self.assertTrue(
            timer.interface.execute(
                "SELECT 1 FROM time_span WHERE end=?",
                (end,),
            )
        )

    def test_edit_currently_running(self):
        """Test editing task.

        Trying: edit currently running task
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(Task("foo", frozenset(), tuple()))
        for action in ("start", "end"):
            with self.assertRaises(ValueError):
                timer.edit(timer.task, action)

    def test_remove(self):
        """Test removing task.

        Trying: remove task
        Expecting: task has been removed
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(Task("foo", {"bar"}, tuple()))
        task = timer.task
        timer.stop()
        timer.remove(task)
        for table in ("time_span", "running", "tagged"):
            self.assertFalse(
                timer.interface.execute(
                    f"SELECT 1 FROM {table} WHERE start=?",
                    (task.time_span[0],),
                )
            )

    def test_remove_currently_running(self):
        """Test removing task.

        Trying: remove currently running task
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(Task("foo", frozenset(), tuple()))
        with self.assertRaises(ValueError):
            timer.remove(timer.task)

    def _insert_tasks(self, tasks):
        """Insert tasks.

        :param tuple tasks: tasks to insert
        """
        timer = src.timer.Timer(self.DATABASE)
        for task in tasks:
            start, end = task.time_span
            if end:
                timer.interface.execute(
                    "INSERT INTO time_span (start,end) VALUES (?,?)",
                    (start, end),
                )
            else:
                timer.interface.execute(
                    "INSERT INTO time_span (start) VALUES (?)",
                    (start,),
                )
            if task.tags:
                timer.interface.execute(
                    "INSERT INTO tagged (tag,start) VALUES (?,?)",
                    *((tag, start) for tag in task.tags),
                )
        timer.interface.execute(
            "INSERT INTO running (name,start) VALUES (?,?)",
            *((task.name, task.time_span[0]) for task in tasks),
        )

    def test_list_buggy_tasks(self):
        """Test listing buggy tasks.

        Trying: list buggy tasks
        Expecting: list of buggy tasks
        """
        timer = src.timer.Timer(self.DATABASE)
        now = datetime.datetime.now()
        hours = datetime.timedelta(hours=1)
        tasks = (
            Task("foo", {"bar"}, (now, None)),
            Task("baz", {"foobar", "toto"}, (now + hours, None)),
            Task("tata", frozenset(), (now - hours, now)),
        )
        self._insert_tasks(tasks)
        self.assertCountEqual(
            (
                Task(task.name, task.tags, (task.time_span[0], None))
                for task in timer.list_buggy_tasks()
            ),
            tasks[:-1],
        )

    def test_add(self):
        """Test adding task.

        Trying: add task
        Expecting: task has been added
        """
        timer = src.timer.Timer(self.DATABASE)
        start = datetime.datetime.now()
        timer.add(Task("foo", {"bar"}, (start, start + datetime.timedelta(days=1))))
        for table in ("time_span", "running", "tagged"):
            self.assertTrue(
                timer.interface.execute(
                    f"SELECT 1 FROM {table} WHERE start=?", (start,)
                )
            )

    def test_add_same_start(self):
        """Test adding task.

        Trying: add task started at the same time than existing task
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        start = datetime.datetime.now()
        time_span = (start, start + datetime.timedelta(hours=1))
        task = Task("foo", {"bar"}, time_span)
        self._insert_tasks((task,))
        with self.assertRaises(ValueError):
            timer.add(task)

    def test_list(self):
        """Test listing tasks.

        Trying: list tasks
        Expecting: list of tasks
        """
        timer = src.timer.Timer(self.DATABASE)
        start = datetime.datetime.now()
        hours = datetime.timedelta(hours=1)
        end = start + (4 * hours)
        tasks = (
            Task("foo", {"bar"}, (start, start + hours)),
            Task("foo", frozenset(), (start + hours, start + (2 * hours))),
            Task("foobar", {"bar", "toto"}, (start + (2 * hours), start + (3 * hours))),
            Task("tata", {"bar", "toto"}, (start + (3 * hours), end)),
        )
        self._insert_tasks(tasks)
        self.assertCountEqual(
            timer.list(start, end, full_match=False),
            tasks,
        )
        for full_match, expected in ((True, (tasks[0],)), (False, tasks[:2])):
            self.assertCountEqual(
                timer.list(
                    start,
                    end,
                    full_name=FullName("foo", {"bar"}),
                    full_match=full_match,
                ),
                expected,
            )
        for full_match, expected in ((True, (tasks[2],)), (False, tasks[2:])):
            self.assertCountEqual(
                timer.list(
                    start,
                    end,
                    full_name=FullName("foobar", {"bar", "toto"}),
                    full_match=full_match,
                ),
                expected,
            )

    def test_sum(self):
        """Test summing runtime up.

        Trying: sum runtime up
        Expecting: summed up runtime per task
        """
        timer = src.timer.Timer(self.DATABASE)
        start = datetime.datetime.now()
        minutes = datetime.timedelta(minutes=1)
        end = start + (4 * minutes)
        tasks = (
            Task("foo", {"bar"}, (start, start + minutes)),
            Task("foo", {"bar"}, (start + minutes, (start + 2 * minutes))),
            Task("foo", {"baz"}, (start + (2 * minutes), start + (3 * minutes))),
            Task("foobar", {"bar"}, (start + (3 * minutes), end)),
        )
        self._insert_tasks(tasks)
        self.assertCountEqual(
            timer.sum(
                start,
                end,
                full_name=FullName("foo", frozenset()),
                full_match=False,
            ).items(),
            ((("foo", ("",)), int(3 * minutes.total_seconds())),),
        )
        self.assertCountEqual(
            timer.sum(
                start,
                end,
                full_name=FullName("", {"bar"}),
                full_match=False,
            ).items(),
            ((("", ("bar",)), int(3 * minutes.total_seconds())),),
        )
        self.assertCountEqual(
            timer.sum(
                start,
                end,
                full_name=FullName("foo", {"bar"}),
                full_match=True,
            ).items(),
            ((("foo", ("bar",)), int(2 * minutes.total_seconds())),),
        )

    def test_export(self):
        """Test exporting tasks.

        Trying: export tasks
        Expecting: tasks have been exported
        """
        timer = src.timer.Timer(self.DATABASE)
        start = datetime.datetime.now()
        minutes = datetime.timedelta(minutes=1)
        end = start + (3 * minutes)
        tasks = (
            Task("foo", {"bar"}, (start, start + minutes)),
            Task("foobar", frozenset(), (start + minutes, start + (2 * minutes))),
            Task("toto", frozenset(), (start + (2 * minutes), end)),
        )
        self._insert_tasks(tasks)
        filename = timer.export("csv", start, end, full_match=False)
        with open(filename) as fp:
            self.assertListEqual(
                list(row for row in csv.reader(fp)),
                sorted(
                    (
                        [
                            task.name,
                            tag,
                            task.time_span[0].isoformat(timespec="seconds"),
                            task.time_span[1].isoformat(timespec="seconds"),
                        ]
                        for task in tasks
                        for tag in sorted(task.tags) or {""}
                    ),
                    key=lambda x: x[2],
                ),
            )
        filename = timer.export("json", start, end, full_match=False)
        with open(filename) as fp:
            self.assertListEqual(
                json.load(fp),
                sorted(
                    (
                        [
                            task.name,
                            list(task.tags),
                            task.time_span[0].isoformat(timespec="seconds"),
                            task.time_span[1].isoformat(timespec="seconds"),
                        ]
                        for task in tasks
                    ),
                    key=lambda x: x[2],
                ),
            )
