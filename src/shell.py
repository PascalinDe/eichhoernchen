#    This file is part of Eichhörnchen 1.1.
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
import os.path
import pathlib
import readline  # noqa
from datetime import datetime

# third party imports
# library specific imports
import src.timing
import src.argument_parser
import src.output_formatter


class UserQuit(Exception):
    """Raised when user quits menu."""
    pass


class TaskShell(cmd.Cmd):
    """Task shell.

    :ivar Timer timer: timer
    :ivar OutputFormatter output_formatter: output formatter
    :ivar ArgumentParser argument_parser: argument parser
    """

    def __init__(self):
        """Initialize task shell."""
        super().__init__()
        self.intro = "Task shell.\tType help or ? to list commands.\n"
        database = os.path.join(
            pathlib.Path.home(), ".local/share/eichhoernchen.db"
        )
        self.timer = src.timing.Timer(database)
        self.output_formatter = src.output_formatter.OutputFormatter()
        self.argument_parser = src.argument_parser.ArgumentParser()
        self._reset_prompt()

    def _reset_prompt(self):
        """Reset prompt."""
        self.prompt = self.output_formatter.pprint_prompt(self.timer.task)

    def do_start(self, args):
        """Start task.

        usage: start FULL_NAME

        FULL_NAME is name of task followed by 0 or more tags
        enclosed in brackets

        example: start 'foo[bar]' to start task 'foo[bar]'
        """
        if not args:
            print("usage: start FULL_NAME")
            return
        full_name, _ = self.argument_parser.find_full_name(args)
        if full_name.name:
            try:
                self.timer.start(full_name.name, tags=full_name.tags)
            except Warning as warning:
                print(warning)
                stop = ""
                while stop not in ("y", "n"):
                    stop = input("replace running task [yn]?").lower()
                if stop == "y":
                    self.timer.stop()
                    self.timer.start(full_name.name, tags=full_name.tags)
            self._reset_prompt()
        else:
            print(f"{args} is not valid FULL_NAME")

    def do_stop(self, args):
        """Stop task.

        usage: stop
        """
        if self.timer.task.name:
            self.timer.stop()
            self._reset_prompt()
        else:
            print("no running task")

    def do_list(self, args):
        """List tasks.

        usage: list [FULL_NAME] [FROM [TO]]

        FULL_NAME is name of task followed by 0 or more tags
        enclosed in brackets

        FROM and TO are at sign followed by either ISO 8601 date
        (e.g. '2019-07-27') or any of the key words 'year', 'month',
        'week', 'yesterday' and 'today'
        in addition to the key words above, FROM can also be 'all'
        FROM and TO default to 'today'

        example: 'list foo[bar] @year' to list all occurrences of the
        task 'foo[bar]' in the current year
        """
        full_name, args = self.argument_parser.find_full_name(args)
        from_, args = self.argument_parser.find_from(args)
        from_ = from_ or "today"
        to, _ = self.argument_parser.find_to(args)
        to = to or "today"
        tasks = self.timer.list_tasks(full_name=full_name, from_=from_, to=to)
        if not tasks:
            print("no tasks")
            return
        tasks.sort(key=lambda x: x.time_span[0])
        for task in tasks:
            date = from_ != "today"
            start_of_day = datetime.now().replace(hour=0, minute=0)
            colour = task.time_span[0] >= start_of_day
            pprint = self.output_formatter.pprint_task(
                task, date=date, colour=colour
            )
            print(pprint)

    def do_sum(self, args):
        """Sum up total time.

        usage: sum [FROM [TO]] [SUMMAND]

        FROM and TO are at sign followed by either ISO 8601 date
        (e.g. '2019-07-27') or any of the key words 'year', 'month',
        'week', 'yesterday' and 'today'
        in addition to the key words above, FROM can also be 'all'
        FROM and TO default to 'today'

        SUMMAND is any of the key words 'full name', 'name' and 'tag'
        SUMMAND defaults to 'full name'

        example: 'sum @yesterday tag' to sum up total time of the individual
        tags since yesterday
        """
        from_, args = self.argument_parser.find_from(args)
        from_ = from_ or "today"
        to, args = self.argument_parser.find_to(args)
        to = to or "today"
        summand, _ = self.argument_parser.find_summand(args)
        summand = summand or "full name"
        full_name = summand == "full name"
        name = summand == "name"
        tag = summand == "tag"
        try:
            sum_total = self.timer.sum_total(
                full_name=full_name, name=name, tag=tag,
                from_=from_, to=to
            )
        except ValueError as exception:
            print(exception)
            return
        if not sum_total:
            print("no tasks")
            return
        sum_total.sort(key=lambda x: (x[1], x[0][0]))
        for (full_name, total) in sum_total:
            pprint = self.output_formatter.pprint_sum(
                full_name, total, colour=True
            )
            print(pprint)

    def _edit_prompt(self, tasks):
        """Provide editing menu.

        :param list tasks: list of tasks

        :returns: task to edit, action to take and its arguments
        :rtype: tuple
        """
        tasks.sort(key=lambda x: x.time_span[0])
        for i, task in enumerate(tasks, start=1):
            pprint_task = self.output_formatter.pprint_task(task, date=True)
            print(f"{i}: {pprint_task}")
        nums = tuple(str(i) for i in range(1, len(tasks)+1))
        num = ""
        while num not in nums and num != "q":
            num = input(
                f"edit task [1 ... {len(tasks) if len(tasks) > 1 else ''}q]"
            )
        if num == "q":
            raise UserQuit
        task = tasks[int(num)-1]
        actions = {
            "n": "name", "t": "tags", "s": "start", "e": "end", "q": "quit"
        }
        action = ""
        while action not in actions.keys() and action not in actions.values():
            pprint_full_name = self.output_formatter.pprint_full_name(
                task.name, task.tags
            )
            print("\n".join(f"{k}: {v}" for k, v in actions.items()))
            action = input(f"edit {pprint_full_name}'s ... ? ~> ")
        if action in actions.keys():
            action = actions[action]
        if action == "quit":
            raise UserQuit
        args = ""
        while not args:
            args = input(f"enter new {action} ~> ")
        if action == "name":
            if not self.argument_parser.NAME_PATTERN.fullmatch(args):
                print(f"{args} is not a valid name")
                raise UserQuit
        elif action == "tags":
            if self.argument_parser.TAG_PATTERN.sub(args, ""):
                print(f"{args} is not a valid list of tags")
                raise UserQuit
            args = self.argument_parser.TAG_PATTERN.findall(args)
        elif action in ("start", "end"):
            try:
                args = self.argument_parser.cast_to_datetime(args)
            except ValueError as exception:
                print(exception)
                raise UserQuit
        return task, action, args

    def do_edit(self, args):
        """Edit task.

        usage: edit FULL_NAME [FROM [TO]]

        FULL_NAME is name of task followed by 0 or more tags
        enclosed in brackets

        FROM and TO are at sign followed by either ISO 8601 date
        (e.g. '2019-07-27') or any of the key words 'year', 'month',
        'week', 'yesterday' and 'today'
        in addition to the key words above, FROM can also be 'all'
        FROM and TO default to 'today'

        example: 'edit foo[bar] yesterday yesterday' to edit
        one of yesterday's 'foo[bar]' tasks
        """
        full_name, args = self.argument_parser.find_full_name(args)
        if not full_name.name:
            print("usage: edit FULL_NAME [FROM [TO]]")
            return
        from_, args = self.argument_parser.find_from(args)
        from_ = from_ or "today"
        to, _ = self.argument_parser.find_to(args)
        to = to or "today"
        tasks = self.timer.list_tasks(
            full_name=full_name, from_=from_, to=to
        )
        if not tasks:
            print("no tasks")
            return
        try:
            task, action, args = self._edit_prompt(tasks)
        except UserQuit:
            return
        try:
            task = self.timer.edit(task, action, args)
        except ValueError as exception:
            pprint_full_name = self.output_formatter.pprint_full_name(
                task.name, task.tags
            )
            print(f"failed to edit task {pprint_full_name}: {exception}")
            return
        self._reset_prompt()
        print(
            self.output_formatter.pprint_task(task, date=True, colour=True)
        )

    def do_bye(self, args):
        """Close task shell."""
        if self.timer.task.name:
            self.timer.stop()
            print("stopped running task")
        return True
