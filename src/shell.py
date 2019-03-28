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
        self.intro = "Task shell.\t Type help or ? to list commands.\n"
        database = os.path.join(
            pathlib.Path.home(), ".local/share/eichhoernchen.db"
        )
        self.timer = src.timing.Timer(database)
        self._reset_prompt()
        return

    def _reset_prompt(self):
        """Reset prompt."""
        if self.timer.current_task.name:
            self.prompt = f"{self.timer.current_task.name} ~> "
        else:
            self.prompt = "~> "

    def _return_total_attr(self, total):
        """Return string representation of total attribute.

        :param int total: total

        :returns: total
        :rtype: str
        """
        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        return f"total: {hours}h{minutes}m"

    def _return_task_object(self, task):
        """Return string representation of Task object.

        :param Task task: task

        :returns: task
        :rtype: str
        """
        start = task.start.strftime("%H:%M")
        now = datetime.datetime.now()
        if task.name == self.timer.current_task.name:
            total = task.total + (now - task.start).seconds
            end = now.strftime("%H:%M")
        else:
            total = task.total
            end = task.end.strftime("%H:%M")
        total = self._return_total_attr(total)
        return f"{task.name} {start}-{end} ({total})"

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
        if self.timer.current_task.name:
            self.timer.stop()
            self._reset_prompt()
        else:
            print("no running task")

    def do_show(self, args):
        """Show current task."""
        current_task = self.timer.current_task
        if current_task.name:
            print(self._return_task_object(current_task))
        else:
            print("no running task")

    def do_list(self, args):
        """List tasks."""
        tasks = self.timer.list()
        tasks.sort(key=lambda x: x.start)
        if not tasks:
            print("no tasks")
        else:
            tasks = "\n".join(
                f"{self._return_task_object(task)}" for task in tasks
            )
            print(tasks)

    def do_sum(self, args):
        """Sum up tasks (comma-separated)."""
        names = args.split(",")
        try:
            total = self._return_total_attr(self.timer.sum(names))
        except ValueError as exception:
            print(exception)
        print(total)

    def do_bye(self, args):
        """Close task shell."""
        if self.timer.current_task.name:
            self.timer.stop()
        return True
