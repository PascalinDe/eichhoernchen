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

# third party imports
# library specific imports
import src.sqlite


class Shell(cmd.Cmd):
    """Eichhörnchen shell."""

    class TaskShell(cmd.Cmd):
        """Task shell."""

        prompt = "(task) "
        intro = "Task shell.\tType help or ? to list commands.\n"

        def __init__(self):
            """Initialize task shell."""
            super().__init__()
            self.task = src.sqlite.Task("", "", "", "")
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

        def do_name(self, args):
            """Name task."""
            args = self._parse(args)
            if len(args) != 1:
                print("usage: name name")
            else:
                self._replace(name=args[0])
            return

        def do_start(self, args):
            """Set start time."""
            args = self._parse(args)
            if len(args) != 1:
                print("usage: start start_time")
            else:
                self._replace(start_time=args[0])
            return

        def do_end(self, args):
            """Set end time."""
            args = self._parse(args)
            if len(args) != 1:
                print("usage: end end_time")
            else:
                self._replace(end_time=args[0])
            return

        def do_priority(self, args):
            """Set priority."""
            args = self._parse(args)
            if len(args) != 1:
                print("usage: priority priority")
            else:
                self._replace(priority=args[0])
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
        print(task_shell.task)
        return True
