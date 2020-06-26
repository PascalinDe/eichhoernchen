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
:synopsis: Shell interpreter.
"""


# standard library imports
import argparse
import datetime
from io import StringIO
from contextlib import redirect_stderr

# third party imports
# library specific imports
import src.timing
import src.parser
from src import FullName
from src.cutils import display_choices, mv_back, mv_front, readline


class InterpreterError(Exception):
    """Raised when shell input cannot be parsed."""
    pass


class Interpreter():
    """Shell interpreter."""
    RESERVED = "@"

    def __init__(self, database, aliases):
        """Initialize shell interpreter.

        :param str database: Eichhörnchen SQLite3 database
        """
        self.timer = src.timing.Timer(database)
        self._init_parser(aliases)

    def _init_parser(self, aliases):
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
            add_help=False,
            aliases=aliases.get("add", [])
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
            add_help=False,
            aliases=aliases.get("remove", [])
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
            add_help=False,
            aliases=aliases.get("list", [])
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
            add_help=False,
            aliases=aliases.get("edit", [])
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
            add_help=False,
            aliases=aliases.get("sum", [])
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
        # 'aliases' command arguments parsers
        parser_aliases = subparsers.add_parser(
            "aliases",
            description="list aliases",
            add_help=False,
            aliases=aliases.get("aliases", [])
        )
        parser_aliases.set_defaults(
            func=lambda *args, **kwargs: self.list_aliases(aliases),
            formatter=lambda multi_part_line: multi_part_line
        )
        # 'export' command arguments parsers
        parser_export = subparsers.add_parser(
            "export",
            description="export tasks",
            add_help=False,
            aliases=aliases.get("aliases", [])
        )
        parser_export.add_argument(
            "ext", choices=("csv", "json"), metavar="format"
        )
        parser_export.add_argument(
            "from_",
            **args["from_"],
            nargs="?",
            default="today"
        )
        parser_export.add_argument(
            "to", **args["to"], nargs="?", default="today"
        )
        parser_export.set_defaults(
            func=self.timer.export,
            formatter=lambda line: [src.cutils.get_multi_part_line((line, 4))]
        )
        # 'help' command arguments parsers
        parser_help = subparsers.add_parser(
            "help",
            description="show help",
            add_help=False,
            aliases=aliases.get("help", [])+["?"]
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
                parser_aliases
            )
        }
        parser_help.add_argument(
            "command",
            nargs="?",
            choices=(
                tuple(progs.keys())
                + tuple(x for y in aliases.values() for x in y)
            )
        )
        parser_help.set_defaults(
            func=lambda command: command or "",
            formatter=lambda command: self.show_help_message(
                command, progs, aliases
            )
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

    def get_from(self, args):
        """Get from.

        :param str args: command-line arguments

        :returns: from
        :rtype: ISO 8601 datetime string or time period keyword
        """
        try:
            return src.parser.parse_from(args)
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
            return src.parser.parse_to(args)
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
            return src.parser.parse_time(args)
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
        try:
            return src.parser.parse_tags(args)
        except ValueError as exception:
            raise argparse.ArgumentTypeError(str(exception))

    def get_name(self, args):
        """Get name.

        :param str args: command-line arguments

        :returns: name
        :rtype: str
        """
        try:
            return src.parser.parse_name(args)
        except ValueError as exception:
            raise argparse.ArgumentTypeError(str(exception))

    def get_full_name(self, args):
        """Get full name.

        :param str args: command-line arguments

        :returns: full name
        :rtype: FullName
        """
        if not args:
            return FullName("", frozenset())
        name = self.get_name(args)
        try:
            return FullName(name, self.get_tags(args))
        except argparse.ArgumentTypeError:
            return FullName(name, frozenset())

    def remove(
            self,
            full_name=FullName("", frozenset()),
            from_="today",
            to="today"
    ):
        """Choose task to remove.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to
        """
        tasks = list(
            self.timer.list_tasks(full_name=full_name, from_=from_, to=to)
        )
        if not tasks:
            return src.cutils.get_multi_part_line(("no task", 4))
        choices = [src.output_formatter.pprint_task(task) for task in tasks]
        i = display_choices(choices)
        if i < 0:
            return src.cutils.get_multi_part_line(("aborted removing task", 5))
        task = tasks[i]
        self.timer.remove(task)
        return src.cutils.get_multi_part_line(
            (f"removed {''.join(x[0] for x in choices[i])}", 4)
        )

    def edit(self, full_name=FullName("", set()), from_="today", to="today"):
        """Choose task to edit.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to
        """
        tasks = list(
            self.timer.list_tasks(full_name=full_name, from_=from_, to=to)
        )
        if not tasks:
            return []
        choices = [src.output_formatter.pprint_task(task) for task in tasks]
        i = display_choices(choices)
        if i < 0:
            return src.cutils.get_multi_part_line(("aborted editing task", 5))
        task = tasks[i]
        actions = ("name", "tags", "start", "end")
        j = display_choices(actions)
        if j < 0:
            return src.cutils.get_multi_part_line(("aborted editing task", 5))
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
        ) if task else [src.cutils.get_multi_part_line(("no task", 0))]

    def stop(self):
        """Stop task."""
        if self.timer.task.name:
            self.timer.stop()
            return src.cutils.get_multi_part_line(("", 0))
        else:
            return src.cutils.get_multi_part_line(("no running task", 0))

    def show_help_message(self, command, progs, aliases):
        """Show help message.

        :param str command: command
        :param dict progs: mapping of command to subparser
        :param dict aliases: mapping of aliases to command
        """
        if command:
            if command not in progs:
                for k, v in aliases.items():
                    if command in v:
                        break
                subparser = progs[k]
            else:
                subparser = progs[command]
            multi_part_lines = [
                src.cutils.get_multi_part_line((help, 4))
                for help in subparser.format_help().split("\n")
            ]
        else:
            multi_part_lines = [
                src.cutils.get_multi_part_line(
                    *[
                        (usage, 4)
                        for usage in self._parser.format_usage().split("\n")
                        if usage
                    ]
                )
            ]
        return multi_part_lines

    def list_aliases(self, aliases):
        """List aliases.

        :param dict aliases: mapping of aliases to command

        :returns: multi-part line
        :rtype: list
        """
        return [
            src.cutils.get_multi_part_line(("alias\tcommand", 4)),
            tuple()
        ] + [
            src.cutils.get_multi_part_line((f"{alias}\t{k}", 4))
            for k, v in aliases.items() for alias in v
        ]
