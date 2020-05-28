#    This file is part of Eichhörnchen 2.0.
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
:synopsis: Command-line interpreter.
"""


# standard library imports
import re
import curses
import argparse
import datetime
from io import StringIO
from contextlib import redirect_stderr

# third party imports
# library specific imports
import src.timing
from src import FullName
from src.cutils import display_choices, mv_back, mv_front, readline


class InterpreterError(Exception):
    """Raised when command-line input cannot be parsed."""
    pass


class Interpreter():
    """Command-line interpreter."""
    RESERVED = "@"

    def __init__(self, database):
        """Initialize command-line interpreter.

        :param str database: Eichhörnchen SQLite3 database
        """
        self.timer = src.timing.Timer(database)
        self._init_parser()

    def _init_parser(self):
        """Initialize parser."""
        self._parser = argparse.ArgumentParser(prog="", add_help=False)
        subparsers = self._parser.add_subparsers()
        args = {
            "full_name": {
                "type": self.get_full_name,
                "help": "name followed by 0 or more tags, e.g. foo[bar]",
                "metavar": "full name"
            },
            "from_": {
                "type": self.get_from,
                "help": (
                    "@([YYYY-MM-DD] [hh:mm]|"
                    "{all,year,month,week,yesterday,today})"
                ),
                "metavar": "from"
            },
            "to": {
                "type": self.get_to,
                "help": (
                    "@([YYYY-MM-DD] [hh:mm]|"
                    "{year,month,week,yesterday,today})"
                )
            },
            "start": {
                "type": self.get_end_point,
                "help": "@YYYY-MM-DD[ hh:mm]"
            },
            "end": {
                "type": self.get_end_point,
                "help": "@YYYY-MM-DD[ hh:mm]"
            }
        }
        # 'start' command arguments parser
        parser_start = subparsers.add_parser(
            "start",
            description="start task",
            add_help=False
        )
        parser_start.add_argument("full_name", **args["full_name"])
        parser_start.set_defaults(
            func=self.timer.start, formatter=lambda *args, **kwargs: []
        )
        # 'stop' command arguments parser
        parser_stop = subparsers.add_parser(
            "stop",
            description="stop task",
            add_help=False
        )
        parser_stop.set_defaults(
            func=self.stop, formatter=lambda x: [x] if x[0][0] else []
        )
        # 'add' command arguments parser
        parser_add = subparsers.add_parser(
            "add",
            description="add task",
            add_help=False
        )
        parser_add.add_argument("full_name", **args["full_name"])
        parser_add.add_argument("start", **args["start"])
        parser_add.add_argument("end", **args["end"])
        parser_add.set_defaults(
            func=self.timer.add,
            formatter=lambda task: [
                src.output_formatter.pprint_task(task=task)
            ]
        )
        # 'remove' command arguments parser
        parser_remove = subparsers.add_parser(
            "remove",
            description="remove task",
            add_help=False
        )
        parser_remove.add_argument("full_name", **args["full_name"])
        parser_remove.add_argument(
            "from_",
            **args["from_"],
            nargs="?",
            default="today"
        )
        parser_remove.add_argument(
            "to", **args["to"], nargs="?", default="today"
        )
        parser_remove.set_defaults(
            func=self.remove,
            formatter=lambda line: [line]
        )
        # 'list' command arguments parser
        parser_list = subparsers.add_parser(
            "list",
            description="list tasks",
            add_help=False
        )
        parser_list.add_argument(
            "full_name",
            **args["full_name"],
            nargs="?",
            default=FullName("", set())
        )
        parser_list.add_argument(
            "from_",
            **args["from_"],
            nargs="?",
            default="today"
        )
        parser_list.add_argument(
            "to", **args["to"], nargs="?", default="today"
        )
        parser_list.set_defaults(
            func=self.timer.list_tasks,
            formatter=lambda tasks: [
                src.output_formatter.pprint_task(task=task, date=True)
                for task in tasks
            ]
        )
        # 'edit' command arguments parser
        parser_edit = subparsers.add_parser(
            "edit",
            description="edit task",
            add_help=False
        )
        parser_edit.add_argument("full_name", **args["full_name"])
        parser_edit.add_argument(
            "from_", **args["from_"], nargs="?", default="today"
        )
        parser_edit.add_argument(
            "to", **args["to"], nargs="?", default="today"
        )
        parser_edit.set_defaults(
            func=self.edit,
            formatter=lambda line: [line]
        )
        # 'sum' command arguments parser
        parser_sum = subparsers.add_parser(
            "sum",
            description="sum up total time",
            add_help=False
        )
        parser_sum.add_argument(
            "summand",
            choices=("full name", "name", "tag")
        )
        parser_sum.add_argument(
            "from_",
            **args["from_"],
            nargs="?",
            default="today"
        )
        parser_sum.add_argument(
            "to", **args["to"], nargs="?", default="today"
        )
        parser_sum.set_defaults(
            func=self.timer.sum_total,
            formatter=lambda sums: [
                src.output_formatter.pprint_sum(FullName(*full_name), total)
                for full_name, total in sums
            ]
        )
        # 'help' command arguments parsers
        parser_help = subparsers.add_parser(
            "help",
            description="show help",
            add_help=False
        )
        parser_question_mark = subparsers.add_parser(
            "?",
            description="show help",
            add_help=False
        )
        progs = {
            subparser.prog.strip(): subparser
            for subparser in (
                parser_start,
                parser_stop,
                parser_add,
                parser_remove,
                parser_list,
                parser_edit,
                parser_sum,
                parser_help,
                parser_question_mark
            )
        }
        parser_help.add_argument(
            "command", nargs="?", choices=tuple(progs.keys())
        )
        parser_help.set_defaults(
            func=lambda command: command or "",
            formatter=lambda command: [
                ((prog, curses.color_pair(4)),)
                for prog in progs[command].format_help().split("\n")
                if prog
            ] if command else [
                ((usage, curses.color_pair(4)),)
                for usage in self._parser.format_usage().split("\n")
                if usage
            ]
        )
        parser_question_mark.add_argument(
            "command", nargs="?", choices=tuple(progs.keys())
        )
        parser_question_mark.set_defaults(
            func=parser_help._defaults["func"],
            formatter=parser_help._defaults["formatter"]
        )

    def interpret_line(self, line):
        """Interpret line.

        :param list lines: lines

        :returns: output
        :rtype: list
        """
        args = line.split(maxsplit=1)
        if len(args) > 1:
            args = [
                args[0],
                *[arg.strip() for arg in args[1].split(sep=self.RESERVED)]
            ]
        try:
            fp = StringIO()
            with redirect_stderr(fp):
                args = self._parser.parse_args(args)
        except SystemExit:
            fp.seek(0)
            raise InterpreterError(
                "\t".join(line.strip() for line in fp.readlines())
            )
        return args.formatter(
            args.func(
                **{k: v for k, v in vars(args).items()
                   if k not in ("func", "formatter")}
            )
        )

    def get_time(self, args, time_periods=()):
        """Get time.

        :param str args: command-line arguments
        :param tuple time_periods: time periods

        :returns: time
        :rtype: ISO 8601 datetime string or time period keyword
        """
        if time_periods:
            time_period_pattern = re.compile(r"|".join(time_periods))
            match = time_period_pattern.match(args)
            if match:
                return match.group(0)
        for format_string in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%H:%M"):
            try:
                datetime.datetime.strptime(args, format_string)
            except ValueError:
                continue
            if format_string == "%H:%M":
                now = datetime.datetime.now()
                args = f"{now.year}-{now.month}-{now.day} {args}"
            break
        else:
            raise ValueError(f"time data {args} does not match any format")
        return args

    def get_from(self, args):
        """Get from.

        :param str args: command-line arguments

        :returns: from
        :rtype: ISO 8601 datetime string or time period keyword
        """
        try:
            return self.get_time(
                args,
                time_periods=(
                    "all", "year", "month", "week", "yesterday", "today")
            )
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"'{args}' is not ISO 8601 string or time period keyword"
            )

    def get_to(self, args):
        """Get to.

        :param str args: command-line arguments

        :returns: to
        :rtype: datetime
        """
        try:
            return self.get_time(
                args,
                time_periods=("year", "month", "week", "yesterday", "today")
            )
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"'{args}' is not ISO 8601 string or time period keyword"
            )

    def get_end_point(self, args):
        """Get end point.

        :param str args: command-line arguments

        :returns: end point
        :rtype: datetime
        """
        try:
            return self.get_time(args)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"'{args}' is not ISO 8601 string"
            )

    def get_tags(self, args):
        """Get list of tags.

        :param str args: command-line arguments

        :returns: list of tags
        :rtype: set
        """
        tag_pattern = re.compile(r"\[((?:\w|\s|[!#+-?])+)\]")
        matches = tag_pattern.findall(args)
        if matches:
            return set(tag.strip() for tag in matches)
        raise argparse.ArgumentTypeError(f"'{args}' does not contain tags")

    def get_name(self, args):
        """Get name.

        :param str args: command-line arguments

        :returns: name
        :rtype: str
        """
        name_pattern = re.compile(r"(?:\w|\s|[!#+-?])+")
        match = name_pattern.match(args)
        if match:
            return match.group(0).strip()
        raise argparse.ArgumentTypeError(f"'{args}' is not name")

    def get_full_name(self, args):
        """Get full name.

        :param str args: command-line arguments

        :returns: full name
        :rtype: FullName
        """
        if not args:
            return FullName("", set())
        name = self.get_name(args)
        try:
            tags = self.get_tags(args)
        except argparse.ArgumentTypeError:
            tags = set()
        return FullName(name, tags)

    def remove(self, full_name=FullName("", set()), from_="today", to="today"):
        """Choose task to remove.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to
        """
        tasks = self.timer.list_tasks(full_name=full_name, from_=from_, to=to)
        if not tasks:
            return (("no task", curses.color_pair(4)),)
        choices = [src.output_formatter.pprint_task(task) for task in tasks]
        i = display_choices(choices)
        if i < 0:
            return (
                (
                    "aborted removing task",
                    curses.color_pair(5)
                ),
            )
        task = tasks[i]
        self.timer.remove(task)
        return (
            (
                f"removed {''.join(x[0] for x in choices[i])}",
                curses.color_pair(4)
            ),
        )

    def edit(self, full_name=FullName("", set()), from_="today", to="today"):
        """Choose task to edit.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to
        """
        tasks = self.timer.list_tasks(full_name=full_name, from_=from_, to=to)
        if not tasks:
            return []
        choices = [src.output_formatter.pprint_task(task) for task in tasks]
        i = display_choices(choices)
        if i < 0:
            return (
                (
                    "aborted editing task",
                    curses.color_pair(5)
                ),
            )
        task = tasks[i]
        actions = ("name", "tags", "start", "end")
        j = display_choices(actions)
        if j < 0:
            return (
                (
                    "aborted editing task",
                    curses.color_pair(5)
                ),
            )
        action = actions[j]
        window = mv_front()
        window.box()
        line = readline(
            window, [], [], boxed=True, prompt=f"new {action} >", y=1
        )
        mv_back()
        args = {
            k: v for k, v in zip(
                actions,
                (self.get_name, self.get_tags, self.get_from, self.get_to)
            )
        }[action](line)
        if action in ("start", "end"):
            args = (datetime.datetime.strptime(args, "%Y-%m-%d %H:%M"))
        return src.output_formatter.pprint_task(
            self.timer.edit(task, action, args)
        ) if task else [(("no task", curses.color_pair(0)),)]

    def stop(self):
        """Stop task."""
        if self.timer.task.name:
            self.timer.stop()
            return (("", curses.color_pair(0)),)
        else:
            return (("no running task", curses.color_pair(0)),)
