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
        self.timer = src.timing.Timer("eichhoernchen.db")
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
        hours = total // 3600
        minutes = (total % 3600) // 60
        return f"total: {hours}h{minutes}m"

    def _return_due_attr(self, due):
        """Return string representation of due attribute.

        :param datetime due: due date

        :returns: due date
        :rtype: str
        """
        if due != datetime.datetime(9999, 12, 31):
            due = datetime.datetime.strftime(due, "%Y-%m-%d")
            due = f", due: {due}"
        else:
            due = ""
        return due

    def _return_task_object(self, task, now=True):
        """Return string representation of Task object.

        :param Task task: task
        :param bool now: toggle end time is now on/off

        :returns: task
        :rtype: str
        """
        start = task.start.strftime("%H:%M")
        total = task.total + (datetime.datetime.now() - task.start).seconds
        if now:
            end = datetime.datetime.now().strftime("%H:%M")
        else:
            end = task.end.strftime("%H:%M")
        total = self._return_total_attr(task.total)
        due = self._return_due_attr(task.due)
        return f"{task.name} {start}-{end} ({total}{due})"

    def do_start(self, args):
        """Start task."""
        try:
            self.timer.start(args)
        except RuntimeError as exception:
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
            print("no current task")

    def do_show(self, args):
        """Show current task."""
        current_task = self.timer.current_task
        if current_task.name:
            print(self._return_task_object(current_task))
        else:
            print("no current task")

    def do_list(self, args):
        """List tasks."""
        tasks = self.timer.list()
        tasks.sort(key=lambda x: x.start)
        if not tasks:
            print("no tasks")
        else:
            for i, task in enumerate(tasks):
                print(f"{i+1} {self._return_task_object(task, now=False)}")

    def do_sum(self, args):
        """Sum up tasks (comma-separated)."""
        names = args.split(",")
        total = self._return_total_attr(self.timer.sum(names))
        print(total)

    def do_bye(self, args):
        """Close task shell."""
        if self.timer.current_task.name:
            self.timer.stop()
        return True
