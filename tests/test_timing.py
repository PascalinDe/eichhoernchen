#    This file is part of Eichhörnchen 1.2.
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
:synopsis: Timing test cases.
"""


# standard library imports
import datetime
import unittest
import os
import os.path

# third party imports
# library specific imports
import src.sqlite
import src.timing
from src import FullName, Task


class TestTiming(unittest.TestCase):
    """Timing test cases.

    :cvar str DATABASE: Eichhörnchen SQLite3 database
    """
    DATABASE = "test.db"

    def tearDown(self):
        """Tear down test cases."""
        if os.path.exists(self.DATABASE):
            os.remove(self.DATABASE)

    def test_start(self):
        """Test starting task.

        Trying: starting task
        Expecting: task is initialized and 'time_span' contains start and
        'running' table contains task name
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        full_name = FullName("foo", set())
        timer.start(full_name)
        self.assertEqual(timer.task.name, full_name.name)
        rows = connection.execute(
            "SELECT start,end FROM time_span WHERE start = ?",
            (timer.task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        time_span = rows[0]
        rows = connection.execute(
            "SELECT name FROM running WHERE start = ?",
            (timer.task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        name = rows[0][0]
        self.assertEqual(time_span, timer.task.time_span)
        self.assertEqual(full_name.name, timer.task.name)

    def test_start_tagged(self):
        """Test starting task.

        Trying: starting tagged task
        Expecting: task is initialized and 'running' table contains
        task name and 'tagged' table contains tag(s)
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        full_name = FullName("foo", {"bar"})
        timer.start(full_name)
        self.assertEqual(timer.task.tags, full_name.tags)
        rows = connection.execute(
            "SELECT tag FROM tagged WHERE start = ?",
            (timer.task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        tags = rows[0]
        self.assertEqual(set(tags), timer.task.tags)

    def test_start_running(self):
        """Test starting task.

        Trying: starting task when there is a running task
        Expecting: Warning
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start(FullName("foo", set()))
        with self.assertRaises(Warning):
            timer.start("bar")

    def test_stop(self):
        """Test stopping task.

        Trying: stopping task
        Expecting: table 'time_span' has been updated
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        full_name = FullName("foo", set())
        timer.start(full_name)
        timer.stop()
        rows = connection.execute(
            """SELECT time_span.start,end
            FROM time_span JOIN running ON time_span.start=running.start
            WHERE name=?""",
            (full_name.name,)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        start, end = rows.pop(0)
        self.assertTrue(end > start)

    def test_list_tasks_today(self):
        """Test listing today's tasks.

        Trying: listing today's tasks
        Expecting: list of today's tasks
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        maxdatetime = datetime.datetime(datetime.MAXYEAR, 12, 31)
        values = [
            ("foo", (now, maxdatetime)),
            ("bar", (now - datetime.timedelta(days=1), maxdatetime))
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [(start, end) for _, (start, end) in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for name, (start, _) in values]
        )
        connection.commit()
        expected = [
            Task(name, set(), (start, end))
            for name, (start, end) in values[:1]
        ]
        self.assertCountEqual(
            timer.list_tasks(from_="today", to="today"), expected
        )

    def test_list_tasks_yesterday(self):
        """Test listing all tasks since yesterday.

        Trying: listing all tasks since yesterday
        Expecting: list of all tasks since yesterday
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        maxdatetime = datetime.datetime(datetime.MAXYEAR, 12, 31)
        values = [
            ("foo", (now, maxdatetime)),
            ("bar", (now - datetime.timedelta(days=1), maxdatetime)),
            ("baz", (now - datetime.timedelta(days=2), maxdatetime))
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [(start, end) for _, (start, end) in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for name, (start, _) in values]
        )
        connection.commit()
        expected = [
            Task(name, set(), (start, end))
            for name, (start, end) in values[:2]
        ]
        self.assertCountEqual(
            timer.list_tasks(from_="yesterday", to="today"), expected
        )

    def test_list_tasks_week(self):
        """Test listing all tasks since the beginning of the week.

        Trying: listing all tasks since the beginning of the week
        Expecting: list of all tasks since the beginning of the week
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        maxdatetime = datetime.datetime(datetime.MAXYEAR, 12, 31)
        values = [
            ("foo", (now, maxdatetime)),
            ("bar", (now - datetime.timedelta(days=1), maxdatetime)),
            ("baz", (now - datetime.timedelta(days=7), maxdatetime))
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [(start, end) for _, (start, end) in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for name, (start, _) in values]
        )
        connection.commit()
        if now.weekday() == 0:
            i = 1
        else:
            i = 2
        expected = [
            Task(name, set(), (start, end))
            for name, (start, end) in values[:i]
        ]
        self.assertEqual(
            timer.list_tasks(from_="week", to="today"), expected
        )

    def test_list_tasks_month(self):
        """Test listing all tasks since the beginning of the month.

        Trying: listing all tasks since the beginning of the month
        Expecting: list of all tasks since the beginning of the month
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        start_of_month = now.replace(day=1)
        maxdatetime = datetime.datetime(datetime.MAXYEAR, 12, 31)
        values = [
            ("foo", (now, maxdatetime)),
            ("bar", (now - datetime.timedelta(days=1), maxdatetime)),
            ("baz", (start_of_month - datetime.timedelta(days=2), maxdatetime))
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [(start, end) for _, (start, end) in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for name, (start, _) in values]
        )
        connection.commit()
        if now == start_of_month:
            i = 1
        else:
            i = 2
        expected = [
            Task(name, set(), (start, end))
            for name, (start, end) in values[:i]
        ]
        self.assertEqual(timer.list_tasks(from_="month", to="today"), expected)

    def test_list_tasks_year(self):
        """Test listing all tasks since the beginning of the year.

        Trying: listing all tasks since the beginning of the year
        Expecting: list of all tasks since the beginning of the year
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        start_of_year = now.replace(month=1, day=1)
        maxdatetime = datetime.datetime(datetime.MAXYEAR, 12, 31)
        values = [
            ("foo", (now, maxdatetime)),
            ("bar", (now - datetime.timedelta(days=1), maxdatetime)),
            ("baz", (start_of_year - datetime.timedelta(days=2), maxdatetime))
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [(start, end) for _, (start, end) in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for name, (start, _) in values]
        )
        connection.commit()
        if now == start_of_year:
            i = 1
        else:
            i = 2
        expected = [
            Task(name, set(), (start, end))
            for name, (start, end) in values[:i]
        ]
        self.assertEqual(timer.list_tasks(from_="year", to="today"), expected)

    def test_list_tasks_all(self):
        """Test listing all tasks.

        Trying: listing all tasks
        Expecting: list of all tasks
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        start_of_month = now.replace(day=1)
        start_of_year = now.replace(month=1, day=1)
        maxdatetime = datetime.datetime(datetime.MAXYEAR, 12, 31)
        values = [
            ("foo", (now, maxdatetime)),
            ("bar",
             (start_of_month - datetime.timedelta(days=1), maxdatetime)),
            ("baz", (start_of_year - datetime.timedelta(days=2), maxdatetime))
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [(start, end) for _, (start, end) in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for name, (start, _) in values]
        )
        connection.commit()
        expected = [
            Task(name, set(), (start, end)) for name, (start, end) in values
        ]
        self.assertEqual(timer.list_tasks(from_="all", to="today"), expected)

    def test_list_tasks_up_to_date(self):
        """Test listing tasks up to date.

        Trying: listing tasks up to date
        Expecting: list of tasks up to date (included)
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        day_before_yesterday = now - datetime.timedelta(days=2)
        maxdatetime = datetime.datetime(datetime.MAXYEAR, 12, 31)
        values = [
            ("foo", (now, maxdatetime)),
            ("bar", (yesterday, maxdatetime)),
            ("baz", (day_before_yesterday, maxdatetime))
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [(start, end) for _, (start, end) in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for name, (start, _) in values]
        )
        connection.commit()
        expected = [
            Task(name, set(), (start, end))
            for name, (start, end) in values[1:]
        ]
        self.assertCountEqual(
            timer.list_tasks(
                from_="all", to=yesterday.strftime("%Y-%m-%d")
            ),
            expected
        )

    def test_list_full_name(self):
        """Test listing tasks having given full name.

        Trying: listing tasks having given full name
        Expecting: list of tasks having given full name
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        maxdatetime = datetime.datetime(datetime.MAXYEAR, 12, 31)
        yesterday = now - datetime.timedelta(days=1)
        day_before_yesterday = now - datetime.timedelta(days=2)
        values = [
            ("foo", "bar", (now, maxdatetime)),
            ("foo", "bar", (yesterday, maxdatetime)),
            ("foo", "bar", (day_before_yesterday, maxdatetime)),
            ("baz", "bar", (now - datetime.timedelta(days=3), maxdatetime)),
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [(start, end) for _, _, (start, end) in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for name, _, (start, _) in values]
        )
        connection.commit()
        sql = "INSERT INTO tagged (tag,start) VALUES (?,?)"
        connection.executemany(
            sql, [(tag, start) for _, tag, (start, _) in values]
        )
        connection.commit()
        expected = [
            Task(name, {tag}, (start, end))
            for name, tag, (start, end) in values[:-1]
        ]
        self.assertCountEqual(
            timer.list_tasks(
                full_name=FullName("foo", {"bar"}), from_="all"
            ),
            expected
        )

    def test_sum_total_full_name(self):
        """Test summing total time up.

        Trying: summing total time up
        Expecting: list of sums of total time (full name)
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        values = [
            ("foo", "", (now, now + timedelta)),
            ("foo", "", (now + timedelta, now + 2*timedelta)),
            ("foo", "foobar", (now + 2*timedelta, now + 3*timedelta))
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [time_span for _, _, time_span in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for (name, _, (start, _)) in values]
        )
        connection.commit()
        sql = "INSERT INTO tagged (tag,start) VALUES (?,?)"
        _, tag, (start, _) = values[-1]
        connection.execute(sql, (tag, start))
        connection.commit()
        expected = [
            (("foo", ()), int(2*timedelta.total_seconds())),
            (("foo", ("foobar",)), int(timedelta.total_seconds()))
        ]
        self.assertCountEqual(timer.sum_total(from_="all"), expected)

    def test_sum_total_name(self):
        """Test summing total time up.

        Trying: summing total time up
        Expecting: list of sums of total time (name)
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        values = [
            ("foo", "bar", (now, now + timedelta)),
            ("foo", "baz", (now + timedelta, now + 2*timedelta)),
            ("foo", "foobar", (now + 2*timedelta, now + 3*timedelta))
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [time_span for _, _, time_span in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for (name, _, (start, _)) in values]
        )
        sql = "INSERT INTO tagged (tag,start) VALUES (?,?)"
        connection.executemany(
            sql, [(tag, start) for (_, tag, (start, _)) in values]
        )
        connection.commit()
        expected = [(("foo", ("",)), int(3*timedelta.total_seconds()))]
        self.assertCountEqual(
            timer.sum_total(summand="name", from_="all"),
            expected
        )

    def test_sum_total_tag(self):
        """Test summing total time up.

        Trying: summing total time up
        Expecting: list of sums of total time (tag)
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        timedelta = datetime.timedelta(minutes=1)
        values = [
            ("foo", "bar", (now, now + timedelta)),
            ("foo", "bar", (now + timedelta, now + 2*timedelta)),
            ("foo", "baz", (now + 2*timedelta, now + 3*timedelta))
        ]
        sql = "INSERT INTO time_span (start,end) VALUES (?,?)"
        connection.executemany(
            sql, [time_span for _, _, time_span in values]
        )
        connection.commit()
        sql = "INSERT INTO running (name,start) VALUES (?,?)"
        connection.executemany(
            sql, [(name, start) for (name, _, (start, _)) in values]
        )
        sql = "INSERT INTO tagged (tag,start) VALUES (?,?)"
        connection.executemany(
            sql, [(tag, start) for (_, tag, (start, _)) in values]
        )
        connection.commit()
        expected = [
            (("", ("bar",)), int(2*timedelta.total_seconds())),
            (("", ("baz",)), int(timedelta.total_seconds()))
        ]
        self.assertCountEqual(
            timer.sum_total(summand="tag", from_="all"), expected
        )

    def test_edit_name(self):
        """Test editing task.

        Trying: editing name
        Expecting: updated name
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        task = Task("foo", set(), (now, now + datetime.timedelta(minutes=1)))
        connection.execute(
            "INSERT INTO time_span (start,end) VALUES (?,?)",
            task.time_span
        )
        connection.execute(
            "INSERT INTO running (name,start) VALUES (?,?)",
            (task.name, task.time_span[0])
        )
        connection.commit()
        name = "foobar"
        timer.edit(task, "name", name)
        row = connection.execute(
            "SELECT name FROM running WHERE start=?",
            (task.time_span[0],)
        ).fetchone()
        actual, = row
        self.assertEqual(actual, name)

    def test_edit_tags(self):
        """Test editing task.

        Trying: editing tags
        Expecting: updated tags
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        task = Task("foo", {"bar"}, (now, now + datetime.timedelta(minutes=1)))
        connection.execute(
            "INSERT INTO time_span (start,end) VALUES (?,?)",
            task.time_span
        )
        connection.execute(
            "INSERT INTO running (name,start) VALUES (?,?)",
            (task.name, task.time_span[0])
        )
        connection.execute(
            "INSERT INTO tagged (tag,start) VALUES (?,?)",
            (list(task.tags)[0], task.time_span[0])
        )
        connection.commit()
        tags = {"baz"}
        timer.edit(task, "tags", tags)
        rows = connection.execute(
            "SELECT tag FROM tagged WHERE start=?",
            (task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        actual = set(rows[0])
        self.assertEqual(actual, tags)

    def test_edit_start(self):
        """Test editing task.

        Trying: editing start
        Expecting: updated start
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        task = Task("foo", set(), (now, now + datetime.timedelta(minutes=1)))
        connection.execute(
            "INSERT INTO time_span (start,end) VALUES (?,?)",
            task.time_span
        )
        connection.execute(
            "INSERT INTO running (name,start) VALUES (?,?)",
            (task.name, task.time_span[0])
        )
        connection.commit()
        start = now - datetime.timedelta(minutes=1)
        timer.edit(task, "start", start)
        rows = connection.execute(
            "SELECT start FROM time_span WHERE start=?",
            (task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 0)
        rows = connection.execute(
            "SELECT name FROM running WHERE start=?",
            (task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 0)
        rows = connection.execute(
            "SELECT start FROM time_span WHERE start=?",
            (start,)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        rows = connection.execute(
            "SELECT name FROM running WHERE start=?",
            (start,)
        ).fetchall()
        self.assertEqual(len(rows), 1)

    def test_edit_end(self):
        """Test editing task.

        Trying: editing end
        Expecting: updated end
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        now = datetime.datetime.now()
        task = Task("foo", set(), (now, now + datetime.timedelta(minutes=1)))
        connection.execute(
            "INSERT INTO time_span (start,end) VALUES (?,?)",
            task.time_span
        )
        connection.execute(
            "INSERT INTO running (name,start) VALUES (?,?)",
            (task.name, task.time_span[0])
        )
        connection.commit()
        end = now + datetime.timedelta(minutes=2)
        timer.edit(task, "end", end)
        rows = connection.execute(
            "SELECT end FROM time_span WHERE start=?",
            (task.time_span[0],)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        actual, = rows[0]
        self.assertEqual(actual, end)

    def test_edit_start_running(self):
        """Test editing task.

        Trying: editing start of a running task
        Expecting: ValueError
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start(FullName("foo", set()))
        now = datetime.datetime.now()
        with self.assertRaises(ValueError):
            timer.edit(timer.task, "start", now)

    def test_remove(self):
        """Test removing task.

        Trying: removing task
        Expecting: task is removed
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start(FullName("foo", set()))
        task = timer.task
        start, _ = task.time_span
        timer.stop()
        timer.remove(task)
        connection = timer.sqlite.connect()
        rows = connection.execute(
            "SELECT start,end FROM time_span WHERE start=?", (start,)
        ).fetchall()
        self.assertEqual(len(rows), 0)
        rows = connection.execute(
            "SELECT name FROM running WHERE start=?", (start,)
        ).fetchall()
        self.assertEqual(len(rows), 0)

    def test_remove_running(self):
        """Test removing task.

        Trying: removing running task
        Expecting: ValueError
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start(FullName("foo", set()))
        with self.assertRaises(ValueError):
            timer.remove(timer.task)

    def test_add(self):
        """Test adding task.

        Trying: adding task
        Expecting: task is added
        """
        timer = src.timing.Timer(self.DATABASE)
        connection = timer.sqlite.connect()
        start = datetime.datetime.strptime(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "%Y-%m-%d %H:%M"
        )
        end = start + datetime.timedelta(days=1)
        task = Task("foo", set(), (start, end))
        timer.add(
            full_name=FullName("foo", set()),
            start=start.strftime("%Y-%m-%d %H:%M"),
            end=end.strftime("%Y-%m-%d %H:%M")
        )
        rows = connection.execute(
            "SELECT 1 FROM time_span WHERE start=?", (start,)
        ).fetchall()
        self.assertTrue(rows)
        rows = connection.execute(
            "SELECT 1 FROM running WHERE start=?", (start,)
        ).fetchall()
        self.assertTrue(rows)

    def test_add_existing(self):
        """Test adding task.

        Trying: add task started at same time as existing task
        Expecting: ValueError
        """
        timer = src.timing.Timer(self.DATABASE)
        timer.start(FullName("foo", set()))
        start, _ = timer.task.time_span
        end = datetime.timedelta(days=1)
        task = Task("bar", set(), (start, end))
        with self.assertRaises(ValueError):
            timer.add(task)
