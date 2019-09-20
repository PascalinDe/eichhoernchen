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
import os
import os.path
import readline  # noqa
from datetime import datetime


# third party imports
# library specific imports
import src.config
import src.timing
import src.output_formatter
from src import argument_parser, Task


class UserQuit(Exception):
    """Raised when user quits menu."""
    pass


class TaskShell(cmd.Cmd):
    """Task shell.

    :ivar Timer timer: timer
    :ivar OutputFormatter output_formatter: output formatter
    """

    def __init__(self, path=None):
        """Initialize task shell."""
        super().__init__()
        self.intro = "Task shell.\tType help or ? to list commands.\n"
        if not path:
            try:
                src.config.create_config()
            except src.config.ConfigFound:
                pass
            path = os.path.join(
                os.environ["HOME"], ".config/eichhoernchen.ini"
            )
        try:
            config = src.config.read_config(path)
        except src.config.BadConfig as exception:
            raise Exception(f"configuration file contains errors: {exception}")
        self.timer = src.timing.Timer(
            os.path.join(config["path"], config["database"])
        )
        self.output_formatter = src.output_formatter.OutputFormatter(
            config["colour_scheme"]
        )
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
        full_name, _ = argument_parser.find_full_name(args)
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
        full_name, args = argument_parser.find_full_name(args)
        from_, args = argument_parser.find_from(args)
        from_ = from_ or "today"
        to, _ = argument_parser.find_to(args)
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
        from_, args = argument_parser.find_from(args)
        from_ = from_ or "today"
        to, args = argument_parser.find_to(args)
        to = to or "today"
        summand, _ = argument_parser.find_summand(args)
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

    def _select_prompt(self, tasks):
        """Provide select menu.

        :param list tasks: list of tasks

        :returns: selected task
        :rtype: task
        """
        tasks.sort(key=lambda x: x.time_span[0])
        for i, task in enumerate(tasks, start=1):
            print(
                f"{i}: {self.output_formatter.pprint_task(task, date=True)}"
            )
        nums = tuple(str(i) for i in range(1, len(tasks)+1))
        num = ""
        while num not in nums and num != "q":
            num = input(
                f"select task [1 ... {len(tasks) if len(tasks) > 1 else ''}q]"
            )
        if num == "q":
            raise UserQuit
        return tasks[int(num)-1]

    def _edit_prompt(self, tasks):
        """Provide editing menu.

        :param list tasks: list of tasks

        :returns: task to edit, action to take and its arguments
        :rtype: tuple
        """
        task = self._select_prompt(tasks)
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
            if not argument_parser.NAME_PATTERN.fullmatch(args):
                print(f"{args} is not a valid name")
                raise UserQuit
        elif action == "tags":
            if argument_parser.TAG_PATTERN.sub(args, ""):
                print(f"{args} is not a valid list of tags")
                raise UserQuit
            args = argument_parser.TAG_PATTERN.findall(args)
        elif action in ("start", "end"):
            try:
                args = argument_parser.cast_to_datetime(args)[0]
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
        full_name, args = argument_parser.find_full_name(args)
        if not full_name.name:
            print("usage: edit FULL_NAME [FROM [TO]]")
            return
        from_, args = argument_parser.find_from(args)
        from_ = from_ or "today"
        to, _ = argument_parser.find_to(args)
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

    def do_add(self, args):
        """Add task.

        usage: FULL_NAME FROM TO

        FULL_NAME is name of task followed by 0 or more tags
        enclosed in brackets

        FROM and TO are ISO 8601 date
        (e.g. '2019-07-27 15:38')
        FROM and TO's day defaults to today

        example: 'add foo[bar] @10:00 @11:00' to add task 'foo[bar]'
        running from 10:00 to 11:00
        """
        full_name, args = argument_parser.find_full_name(args)
        if not full_name.name:
            print("usage: FULL_NAME FROM TO")
            return
        try:
            from_, to = argument_parser.cast_to_datetime(args)
        except ValueError as exception:
            print(exception)
            return
        self.timer.add(Task(full_name.name, full_name.tags, (from_, to)))

    def do_remove(self, args):
        """Remove task.

        usage: remove FULL_NAME [FROM [TO]]

        FULL_NAME is name of task followed by 0 or more tags
        enclosed in brackets

        FROM and TO are at sign followed by either ISO 8601 date
        (e.g. '2019-07-27') or any of the key words 'year', 'month',
        'week', 'yesterday' and 'today'
        in addition to the key words above FROM can also be 'all'
        FROM and TO default to 'today'

        example: 'remove foo[bar] @yesterday @yesterday' to remove
        one of yesterday's 'foo[bar]' tasks
        """
        full_name, args = argument_parser.find_full_name(args)
        if not full_name.name:
            print("usage: add FULL_NAME [FROM [TO]]")
            return
        from_, args = argument_parser.find_from(args)
        from_ = from_ or "today"
        to, _ = argument_parser.find_to(args)
        to = to or "today"
        tasks = self.timer.list_tasks(full_name=full_name, from_=from_, to=to)
        if not tasks:
            print("no tasks")
            return
        try:
            task = self._select_prompt(tasks)
        except UserQuit:
            return
        pprint_task = self.output_formatter.pprint_task(
            task, date=True, colour=True
        )
        remove = ""
        while remove not in ("y", "n"):
            remove = input(f"remove {pprint_task} [yn]?").lower()
        if remove == "y":
            try:
                self.timer.remove(task)
                print(f"removed task {pprint_task}")
            except ValueError as exception:
                print(f"failed to remove task {pprint_task}: {exception}")
                return
        else:
            return

    def do_generate(self, args):
        """Generate default configuration file.

        Discards configuration file at $HOME/.config/eichhoernchen.ini.
        Any changes will be lost.
        """
        try:
            src.config.create_config()
        except src.config.ConfigFound as exception:
            print(exception)
            create = ""
            while create not in ("y", "n"):
                create = input(
                    "replace configuration file [yn]? ~> "
                ).lower()
            if create == "y":
                src.config.create_config(force=True)
                print("generated default configuration file")
            else:
                print("aborted generating default configuration file")
                print("no changes have been made")

    def do_bye(self, args):
        """Close task shell."""
        if self.timer.task.name:
            self.timer.stop()
            print("stopped running task")
        return True
