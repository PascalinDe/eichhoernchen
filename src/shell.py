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
import re
import cmd
import collections
import os.path
import pathlib
import readline
from datetime import datetime

# third party imports
# library specific imports
import src.timing


TAG_PATTERN = re.compile(r"\[(\w+)\]")
PERIOD_PATTERN = re.compile(r"all|year|month|week|yesterday|today")
KEY_WORD_PATTERN = re.compile(r"task|tag")


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
            tags = "".join(f"[{tag}]" for tag in self.timer.task.tags)
            start, _ = self.timer.task.time_span
            start = datetime.strftime(start, "%H:%M")
            self.prompt = f"{self.timer.task.name}{tags} ({start}-) ~> "
        else:
            self.prompt = "~> "

    @staticmethod
    def _return_total(total):
        """Return representation of run time.

        :param int total: run time (in seconds)

        :returns: representation
        :rtype: str
        """
        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        return f"total: {hours}h{minutes}m"

    def do_start(self, args):
        """Start task."""
        try:
            if not args:
                task = self.task.name
                tags = self.task.tags
                print("restarting last task")
            else:
                task = TAG_PATTERN.sub("", args).strip()
                tags = TAG_PATTERN.findall(args)
            self.timer.start(task, tags=tags)
        except Warning as warning:
            print(warning)
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
        match = PERIOD_PATTERN.match(args)
        if match:
            period = match.group()
        else:
            period = "today"
        tasks = self.timer.list_tasks(period=period)
        if not tasks:
            print("no tasks")
        else:
            tasks.sort(key=lambda x: x.time_span[0])
            for task in tasks:
                start, end = task.time_span
                if period == "today":
                    start = datetime.strftime(start, "%H:%M")
                    end = datetime.strftime(end, "%H:%M")
                else:
                    if (end.month, end.day) != (start.month, start.day):
                        end = datetime.strftime(end, "%H:%M %Y-%m-%d")
                    else:
                        end = datetime.strftime(end, "%H:%M")
                    start = datetime.strftime(start, "%H:%M %Y-%m-%d")
                tags = "".join(f"[{tag}]" for tag in task.tags)
                total = self._return_total(task.total)
                print(f"{start}-{end} ({total}) {task.name}{tags}")

    def do_sum(self, args):
        """Sum up total time."""
        match = KEY_WORD_PATTERN.findall(args.lower())
        tasks = "task" in match
        tags = "tag" in match
        match = PERIOD_PATTERN.match(args)
        if match:
            period = match.group()
        else:
            period = "today"
        try:
            sum_total = self.timer.sum_total(
                tasks=tasks, tags=tags, period=period
            )
        except ValueError as exception:
            print(exception)
            return
        sum_total.sort(key=lambda x: len(x[0][0]), reverse=True)
        try:
            i = [name for (name, _), _ in sum_total].index("")
        except ValueError:
            i = len(sum_total)
        sorted_sublist = sorted(sum_total[:i], key=lambda x: (x[1], x[0][0]))
        for ((name, tags), total) in sorted_sublist:
            tags = "".join(f"[{tag}]" for tag in tags)
            total = self._return_total(total)
            print(f"{name}{tags} {total}")
        sorted_sublist = sorted(
            sum_total[i:], key=lambda x: (x[1], x[0][1])
        )
        for ((_, tags), total) in sorted_sublist:
            tags = f"[{tags[0]}]"
            total = self._return_total(total)
            print(f"{tags} {total}")

    def do_bye(self, args):
        """Close task shell."""
        if self.timer.task.name:
            self.timer.stop()
            print("stopped running task")
        return True
