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
:synopsis: Eichhörnchen shell.
"""


# standard library imports
import cmd
import readline
import datetime

# third party imports
# library specific imports
import src.sqlite


class Shell(cmd.Cmd):
    """Eichhörnchen shell."""

    class TaskShell(cmd.Cmd):
        """Task shell.

        :cvar str DATE_FORMAT: format string (date)
        :cvar str TIME_FORMAT: format string (time)
        :ivar Task task: task
        """

        prompt = "(task) "
        intro = "Task shell.\tType help or ? to list commands.\n"

        DATE_FORMAT = "%Y-%m-%d"
        TIME_FORMAT = "%H:%M"

        def __init__(self):
            """Initialize task shell."""
            super().__init__()
            self.task = src.sqlite.Task("", "", "", "", "")
            return

        def _replace(self, **kwargs):
            """Replace Task instance variable."""
            self.task = self.task._replace(**kwargs)
            return

        @staticmethod
        def _parse(args):
            """Parse argument(s).

            :param str args: argument(s)

            :returns: list of arguments
            :rtype: list
            """
            return args.split()

        def _get_time(self, string):
            """Get time.

            :param str string: string

            :returns: time
            :rtype: datetime.datetime
            """
            if string == "now":
                time = datetime.datetime.now()
            else:
                time = datetime.datetime.strptime(string, self.TIME_FORMAT)
            return time

        def _get_date(self, string):
            """Get date.

            :param str string: string

            :returns: date
            :rtype: datetime.datetime
            """
            now = datetime.datetime.now()
            try:
                date = datetime.datetime.strptime(string, "%Y-%m-%d")
                year = date.year
                month = date.month
                day = date.day
            except ValueError:
                try:
                    date = datetime.datetime.strptime(string, "%m-%d")
                    year = now.year
                    month = date.month
                    day = date.day
                except ValueError:
                    date = datetime.datetime.strptime(string, "%d")
                    year = now.year
                    month = now.month
                    day = date.day
            return datetime.datetime(year, month, day)

        def do_name(self, args):
            """Name task."""
            args = self._parse(args)
            if len(args) != 1:
                print("usage: name name")
            else:
                self._replace(name=args[0])
            return

        def do_start(self, args):
            """
            Set start time. Specify as hh:mm or use shortcut 'now' for
            current date.
            """
            args = self._parse(args)
            if len(args) != 1:
                print("usage: start hh:mm or use shortcut 'now'")
            else:
                try:
                    time = self._get_time(args[0])
                except ValueError:
                    print("usage: start hh:mm or use shortcut 'now'")
                self._replace(start=time)
            return

        def do_end(self, args):
            """
            Set end time. Specify as hh:mm or use shortcut 'now' for
            current date.
            """
            args = self._parse(args)
            if len(args) != 1:
                print("usage: end hh:mm or use shortcut 'now'")
            else:
                try:
                    time = self._get_time(args[0])
                except ValueError:
                    print("usage: end hh:mm or use shortcut 'now'")
                self._replace(end=time)
            return

        def do_total(self, args):
            """Set total time. Specify as hh:mm."""
            args = self._parse(args)
            if len(args) != 1:
                print("usage: total hh:mm")
            else:
                try:
                    time = self._get_time(args[0])
                except ValueError:
                    print("usage: total hh:mm")
                self._replace(total=time)
            return

        def do_due(self, args):
            """
            Set due date. Specify as [YYYY-][MM-]DD
            (leaving out either YYYY or MM assumes current).
            """
            args = self._parse(args)
            if len(args) != 1:
                print("usage: due [YYYY-][MM-]DD")
            else:
                try:
                    date = self._get_date(args[0])
                except ValueError:
                    print("usage: due [YYYY-][MM-]DD")
                self._replace(due=date)
            return

        def do_bye(self, args):
            """Close task shell."""
            return True

    prompt = "(eichhoernchen) "
    intro = "Eichhörnchen shell.\tType help or ? to list commands.\n"

    def do_add(self, args):
        """Add task."""
        task_shell = self.TaskShell()
        task_shell.cmdloop()
        sqlite = src.sqlite.SQLite()
        sqlite.insert((task_shell.task,))
        return

    def do_bye(self, args):
        """Close Eichhörnchen shell."""
        return True
