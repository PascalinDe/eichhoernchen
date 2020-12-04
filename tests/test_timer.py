#    This file is part of Eichhörnchen 2.1.
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
import src.sqlite

from src import FullName, Task


class TestTimer(unittest.TestCase):
    """Timer test cases.

    :cvar str DATABASE: SQLite3 database
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
        Expecting: task is started
        """
        timer = src.timer.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        full_name = FullName("foo", {"bar", "baz"})
        timer.start(full_name)
        self.assertEqual(timer.task.name, full_name.name)
        self.assertEqual(timer.task.tags, full_name.tags)
        rows = connection.execute(
            "SELECT start,end FROM time_span WHERE start = ?",
            (timer.task.time_span[0],),
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], timer.task.time_span)
        rows = connection.execute(
            "SELECT name FROM running WHERE start = ?", (timer.task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(*rows[0], full_name.name)
        rows = connection.execute(
            "SELECT tag FROM tagged WHERE start = ?", (timer.task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual({x for row in rows for x in row}, timer.task.tags)

    def test_stop(self):
        """Test stopping task.

        Trying: stopping task
        Expecting: task has been stopped
        """
        timer = src.timer.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        name = "foo"
        timer.start(full_name=FullName(name))
        timer.stop()
        self.assertEqual(timer.task.name, "")
        rows = connection.execute(
            """SELECT time_span.start,end
            FROM time_span
            JOIN running ON time_span.start=running.start
            WHERE name = ?""",
            (name,),
        ).fetchall()
        start, end = rows.pop(0)
        self.assertTrue(end > start)

    def _insert(self, values):
        """Insert tasks.

        :param tuple values: tasks to insert
        """
        timer = src.timer.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        connection.executemany(
            "INSERT INTO time_span (start,end) VALUES (?,?)",
            ((start, end) for _, _, (start, end) in values if end),
        )
        connection.commit()
        connection.executemany(
            "INSERT INTO running (name,start) VALUES (?,?)",
            ((name, start) for name, _, (start, _) in values),
        )
        connection.commit()
        for _, tags, (start, _) in values:
            connection.executemany(
                "INSERT INTO tagged (tag,start) VALUES (?,?)",
                ((tag, start) for tag in tags),
            )
        connection.commit()

    def test_edit_name(self):
        """Test editing task.

        Trying: editing name
        Expecting: name has been updated
        """
        timer = src.timer.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        timer.start(full_name=FullName("foo"))
        task = timer.task
        timer.stop()
        name = "bar"
        timer.edit(task, "name", name)
        self.assertEqual(
            *connection.execute(
                "SELECT name FROM running WHERE start=?", (task.time_span[0],)
            ).fetchone(),
            name,
        )

    def test_edit_tags(self):
        """Test editing task.

        Trying: editing tags
        Expecting: tags have been updated
        """
        timer = src.timer.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        timer.start(full_name=FullName("foo", {"bar"}))
        task = timer.task
        timer.stop()
        tags = {"bar", "baz"}
        timer.edit(task, "tags", tags)
        self.assertCountEqual(
            (
                x
                for row in connection.execute(
                    "SELECT tag FROM tagged WHERE start=?", (task.time_span[0],)
                )
                for x in row
            ),
            tags,
        )

    def test_edit_start(self):
        """Test editing task.

        Trying: editing start
        Expecting: start has been updated
        """
        timer = src.timer.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        timer.start(full_name=FullName("foo"))
        task = timer.task
        timer.stop()
        timedelta = datetime.timedelta(minutes=1)
        task = Task(
            task.name, task.tags, (task.time_span[0], task.time_span[0] + timedelta)
        )
        start = task.time_span[0] - timedelta
        timer.edit(task, "start", start)
        for table in ("time_span", "running"):
            sql = f"SELECT 1 FROM {table} WHERE start=?"
            self.assertFalse(connection.execute(sql, (task.time_span[0],)).fetchall())
            self.assertTrue(connection.execute(sql, (start,)).fetchall())

    def test_edit_end(self):
        """Test editing task.

        Trying: editing end
        Expecting: end has been updated
        """
        timer = src.timer.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        timer.start(full_name=FullName("foo"))
        task = timer.task
        timer.stop()
        timedelta = datetime.timedelta(minutes=1)
        task = Task(
            task.name, task.tags, (task.time_span[0], task.time_span[0] + timedelta)
        )
        end = task.time_span[1] + timedelta
        timer.edit(task, "end", end)
        self.assertEqual(
            *connection.execute(
                "SELECT end FROM time_span WHERE start=?", (task.time_span[0],)
            ).fetchall(),
            (end,),
        )

    def test_edit_start_running(self):
        """Test editing task.

        Trying: editing start of a running task
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(full_name=FullName("foo"))
        with self.assertRaises(ValueError):
            timer.edit(timer.task, "start", datetime.datetime.now())

    def test_edit_start_after_end(self):
        """Test editing task.

        Trying: editing start so that new start is after end
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(full_name=FullName("foo"))
        task = timer.task
        timer.stop()
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        task = Task(task.name, task.tags, (task.time_span[0], now + timedelta))
        start = now + 2 * timedelta
        with self.assertRaises(ValueError):
            timer.edit(task, "start", start)

    def test_edit_end_running(self):
        """Test editing task.

        Trying: editing end of a running task
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(full_name=FullName("foo"))
        with self.assertRaises(ValueError):
            timer.edit(timer.task, "end", datetime.datetime.now())

    def test_edit_end_before_start(self):
        """Test editing task.

        Trying: editing end so that new end is before start
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(full_name=FullName("foo"))
        task = timer.task
        timer.stop()
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        task = Task(task.name, task.tags, (task.time_span[0], now))
        end = task.time_span[0] - timedelta
        with self.assertRaises(ValueError):
            timer.edit(task, "end", end)

    def test_remove(self):
        """Test removing task.

        Trying: removing task
        Expecting: task has been removed
        """
        timer = src.timer.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        timer.start(full_name=FullName("foo", {"bar"}))
        task = timer.task
        timer.stop()
        timer.remove(task=task)
        for table in ("time_span", "running", "tagged"):
            self.assertFalse(
                connection.execute(
                    f"SELECT 1 FROM {table} WHERE start=?", (task.time_span[0],)
                ).fetchall()
            )

    def test_remove_running(self):
        """Test removing task.

        Trying: removing running task
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(full_name=FullName("foo"))
        with self.assertRaises(ValueError):
            timer.remove(task=timer.task)

    def test_clean_up(self):
        """Test cleaning up tasks.

        Trying: cleaning up tasks
        Expecting: tasks to clean up
        """
        timer = src.timer.Timer(self.DATABASE)
        now = datetime.datetime.now()
        values = (
            ("foo", {"bar"}, (now, None)),
            ("baz", frozenset(), (now + datetime.timedelta(hours=1), None)),
            ("foobar", {"toto", "tata"}, (now - datetime.timedelta(hours=1), now)),
        )
        self._insert(values)
        self.assertCountEqual(
            timer.clean_up(),
            (Task(name, tags, time_span) for name, tags, time_span in values[:-1]),
        )

    def test_add(self):
        """Test adding task.

        Trying: adding task
        Expecting: task has been added
        """
        timer = src.timer.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        start = datetime.datetime.now()
        end = start + datetime.timedelta(days=1)
        timer.add(FullName("foo", {"bar"}), start, end)
        for table in ("time_span", "running", "tagged"):
            self.assertTrue(
                connection.execute(
                    f"SELECT 1 FROM {table} WHERE start=?", (start,)
                ).fetchall()
            )

    def test_add_same_start(self):
        """Test adding task.

        Trying: add task starting at the same time as existing task
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        timer.start(full_name=FullName("foo"))
        start, _ = timer.task.time_span
        timer.stop()
        end = start + datetime.timedelta(minutes=1)
        with self.assertRaises(ValueError):
            timer.add(FullName("foo", frozenset()), start, end)

    def test_add_start_after_end(self):
        """Test adding task.

        Trying: add task starting after its end
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        end = datetime.datetime.now()
        start = end + datetime.timedelta(days=1)
        with self.assertRaises(ValueError):
            timer.add(FullName("foo", {"bar"}), start, end)

    def test_add_end_before_start(self):
        """Test adding task.

        Trying: add task ending before its start
        Expecting: ValueError
        """
        timer = src.timer.Timer(self.DATABASE)
        start = datetime.datetime.now()
        end = start - datetime.timedelta(days=1)
        with self.assertRaises(ValueError):
            timer.add(FullName("foo", {"bar"}), start, end)

    def test_list(self):
        """Test listing tasks.

        Trying: listing tasks
        Expecting: list of tasks
        """
        timer = src.timer.Timer(self.DATABASE)
        now = datetime.datetime.now()
        from_ = now - datetime.timedelta(days=now.weekday())
        values = (
            ("foo", {"bar"}, (now, now + datetime.timedelta(hours=1))),
            ("baz", frozenset(), (from_, now)),
            ("foobar", {"toto", "tata"}, (from_ - datetime.timedelta(days=1), now)),
        )
        self._insert(values)
        expected = (
            Task(name, tags, (start, end)) for name, tags, (start, end) in values[:2]
        )
        self.assertCountEqual(
            timer.list(
                from_.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"), full_match=False
            ),
            expected,
        )

    def test_sum_name(self):
        """Test summing total time up.

        Trying: summing up total time with a given name
        Expecting: list of sums
        """
        timer = src.timer.Timer(self.DATABASE)
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        values = (
            ("foo", {"bar"}, (now, now + timedelta)),
            ("foo", {}, (now + timedelta, now + 2 * timedelta)),
            ("bar", {}, (now + 2 * timedelta, now + 3 * timedelta)),
        )
        self._insert(values)
        expected = ((("foo", ("",)), int(2 * timedelta.total_seconds())),)
        self.assertCountEqual(
            timer.sum(
                now.strftime("%Y-%m-%d"),
                now.strftime("%Y-%m-%d"),
                full_name=FullName("foo", frozenset()),
                full_match=False,
            ),
            expected,
        )

    def test_sum_tags(self):
        """Test summing total time up.

        Trying: summing up total time with given tags
        Expecting: list of sums
        """
        timer = src.timer.Timer(self.DATABASE)
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        values = (
            ("foo", {"bar"}, (now, now + timedelta)),
            ("baz", {"bar"}, (now + timedelta, now + 2 * timedelta)),
            ("foobar", {"toto"}, (now + 2 * timedelta, now + 3 * timedelta)),
        )
        self._insert(values)
        expected = ((("", ("bar",)), int(2 * timedelta.total_seconds())),)
        self.assertCountEqual(
            timer.sum(
                now.strftime("%Y-%m-%d"),
                now.strftime("%Y-%m-%d"),
                full_name=FullName("", {"bar"}),
                full_match=False,
            ),
            expected,
        )

    def test_sum_full_name(self):
        """Test summing total time up.

        Trying: summing up total time with given full name
        Expecting: list of sums
        """
        timer = src.timer.Timer(self.DATABASE)
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        values = (
            ("foo", frozenset(), (now, now + timedelta)),
            ("foo", frozenset(), (now + timedelta, now + 2 * timedelta)),
            ("foo", {"foobar"}, (now + 2 * timedelta, now + 3 * timedelta)),
        )
        self._insert(values)
        expected = ((("foo", ("foobar",)), int(timedelta.total_seconds())),)
        self.assertCountEqual(
            timer.sum(
                now.strftime("%Y-%m-%d"),
                now.strftime("%Y-%m-%d"),
                full_name=FullName("foo", {"foobar"}),
                full_match=True,
            ),
            expected,
        )

    def test_export_to_csv(self):
        """Test exporting tasks.

        Trying: export to CSV file
        Expecting: tasks have been exported to CSV file
        """
        timer = src.timer.Timer(self.DATABASE)
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        values = (
            ("foo", {"bar", "baz"}, (now, now + timedelta)),
            ("foobar", frozenset(), (now + timedelta, now + 2 * timedelta)),
            ("toto", frozenset(), (now - timedelta, now)),
        )
        self._insert(values)
        filename = timer.export(
            "csv", now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        )
        with open(filename) as fp:
            self.assertEqual(
                list(row for row in csv.reader(fp)),
                sorted(
                    (
                        [
                            name,
                            tag,
                            start.isoformat(timespec="seconds"),
                            end.isoformat(timespec="seconds"),
                        ]
                        for name, tags, (start, end) in values
                        for tag in sorted(tags) or {""}
                    ),
                    key=lambda x: x[2],
                ),
            )

    def test_export_to_json(self):
        """Test exporting tasks.

        Trying: export to JSON file
        Expecting: tasks have been exported to JSON file
        """
        timer = src.timer.Timer(self.DATABASE)
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        values = (
            ("foo", {"bar", "baz"}, (now, now + timedelta)),
            ("foobar", frozenset(), (now + timedelta, now + 2 * timedelta)),
            ("toto", frozenset(), (now - timedelta, now)),
        )
        self._insert(values)
        filename = timer.export(
            "json", now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        )
        with open(filename) as fp:
            self.assertEqual(
                json.load(fp),
                sorted(
                    (
                        [
                            name,
                            list(tags),
                            start.isoformat(timespec="seconds"),
                            end.isoformat(timespec="seconds"),
                        ]
                        for name, tags, (start, end) in values
                    ),
                    key=lambda x: x[2],
                ),
            )

    def test_export_to_csv_full_name(self):
        """Test exporting tasks.

        Trying: export tasks with given full name to CSV file
        Expecting: tasks with given full name have been exported to CSV file
        """
        timer = src.timer.Timer(self.DATABASE)
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        values = (
            ("foo", {"bar", "baz"}, (now, now + timedelta)),
            ("foobar", frozenset(), (now + timedelta, now + 2 * timedelta)),
            ("toto", frozenset(), (now - timedelta, now)),
            ("toto", frozenset(), (now + 2 * timedelta, now + 3 * timedelta)),
        )
        self._insert(values)
        filename = timer.export(
            "csv",
            now.strftime("%Y-%m-%d"),
            now.strftime("%Y-%m-%d"),
            full_name=FullName("toto", frozenset()),
        )
        with open(filename) as fp:
            self.assertEqual(
                list(row for row in csv.reader(fp)),
                sorted(
                    (
                        [
                            name,
                            tag,
                            start.isoformat(timespec="seconds"),
                            end.isoformat(timespec="seconds"),
                        ]
                        for name, tags, (start, end) in values[2:]
                        for tag in sorted(tags) or {""}
                    ),
                    key=lambda x: x[2],
                ),
            )
