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
import datetime
import os.path
import pathlib
import readline

# third party imports
# library specific imports
import src.timing


class TaskShell(cmd.Cmd):
    """Task shell.

    :ivar Timer timer: timer
    """

    def __init__(self):
        """Initialize task shell."""
        super().__init__()
        self.intro = "Task shell.\tType help or ? to list commands.\n"
        database = os.path.join(
            pathlib.Path.home(), ".local/share/eichhoernchen.db"
        )
        self.timer = src.timing.Timer(database)
        self._reset_prompt()

    def _reset_prompt(self):
        """Reset prompt."""
        if self.timer.task.name:
            start, _ = sorted(
                self.timer.task.time_span, key=lambda x: x[0], reverse=True
            ).pop(0)
            start = datetime.datetime.strftime(start, "%H:%M")
            self.prompt = f"{self.timer.task.name} ({start}-) ~> "
        else:
            self.prompt = "~> "

    def do_start(self, args):
        """Start task."""
        try:
            self.timer.start(args)
        except Warning as exception:
            print(exception)
            stop = ""
            while stop not in ["y", "n"]:
                stop = input("replace running task [yn]? ").lower()
            if stop == "y":
                self.timer.stop()
                self.timer.start(args)
        self._reset_prompt()

    def do_stop(self, args):
        """Stop task."""
        if self.timer.task.name:
            self.timer.stop()
            self._reset_prompt()
        else:
            print("no running task")

    def do_list(self, args):
        """List tasks."""
        tasks = self.timer.list()
        if not tasks:
            print("no tasks")
        else:
            print("\n".join(str(task) for task in tasks))

    def do_sum(self, args):
        """Sum up run times."""
        total = self.timer.sum(args=args)
        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        print(f"total: {hours}h{minutes}m")

    def do_bye(self, args):
        """Close task shell."""
        if self.timer.task.name:
            self.timer.stop()
        return True
