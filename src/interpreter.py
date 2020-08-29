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
import re
import argparse
import datetime
import curses.panel
from io import StringIO
from contextlib import redirect_stderr

# third party imports
# library specific imports
import src.parser
import src.timing
from src import FullName
from src.cutils import (
    mk_menu,
    readline,
    reinitialize_primary_window,
    ResizeError,
    get_window_pos,
    mk_panel
)


def get_name(args):
    """Get name.

    :param str args: command-line arguments

    :returns: name
    :rtype: str
    """
    try:
        return src.parser.parse_name(args)
    except ValueError as exception:
        raise argparse.ArgumentTypeError(str(exception))


def get_tags(args):
    """Get list of tags.

    :param str args: command-line arguments

    :returns: list of tags
    :rtype: set
    """
    try:
        return src.parser.parse_tags(args)
    except ValueError as exception:
        raise argparse.ArgumentTypeError(str(exception))


def get_full_name(args):
    """Get full name.

    :param str args: command-line arguments

    :returns: full name
    :rtype: FullName
    """
    if not args:
        return FullName("", frozenset())
    try:
        return FullName(get_name(args), get_tags(args))
    except argparse.ArgumentTypeError:
        return FullName(get_name(args), frozenset())


def get_summand(args):
    """Get summand.

    :param str args: command-line arguments

    :returns: summand
    :rtype: FullName
    """
    try:
        return get_full_name(args)
    except argparse.ArgumentTypeError:
        return FullName("", get_tags(args))


def get_from(args):
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


def get_to(args):
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


def get_end_point(args):
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


ARGS = {
    "full_name": {
        "type": get_full_name,
        "help": "name followed by 0 or more tags, e.g. 'foo[bar]'",
        "metavar": "full name"
    },
    "from_": {
        "type": get_from,
        "metavar": "from",
        "help": "@([YYYY-MM-DD] [hh:mm]|{all,year,month,week,yesterday,today})"
    },
    "to": {
        "type": get_to,
        "help": "@([YYYY-MM-DD] [hh:mm]|{year,month,week,yesterday,today})"
    },
    "start": {
        "type": get_end_point,
        "help": "@YYYY-MM-DD [hh:mm]"
    },
    "end": {
        "type": get_end_point,
        "help": "@YYYY-MM-DD [hh:mm]"
    }
}


class InterpreterError(Exception):
    """Raised when shell input cannot be parsed."""
    pass


class Interpreter():
    """Shell interpreter.

    :cvar str RESERVED: reserved characters
    :ivar Timer timer: timer
    :ivar ArgumentParser parser: parser
    """
    RESERVED = ["@"]

    def __init__(self, database, aliases):
        """Initialize shell interpreter.

        :param str database: Eichhörnchen SQLite3 database
        :param dict aliases: aliases
        """
        self.timer = src.timing.Timer(database)
        self.subcommand_defs = {
            "start": {
                "description": "start task",
                "aliases": aliases.get("start", []),
                "func": self.timer.start,
                "formatter": lambda *args, **kwargs: [],
                "args": {
                    "full_name": ARGS["full_name"]
                }
            },
            "stop": {
                "description": "stop task",
                "aliases": aliases.get("stop", []),
                "func": self.stop,
                "formatter": lambda x: [x] if x[0][0] else [],
                "args": {}
            },
            "add": {
                "description": "add task",
                "aliases": aliases.get("add", []),
                "func": self.timer.add,
                "formatter": lambda task: [
                    src.output_formatter.pprint_task(task)
                ],
                "args": {
                    "full_name": ARGS["full_name"],
                    "start": ARGS["start"],
                    "end": ARGS["end"]
                }
            },
            "remove": {
                "description": "remove task",
                "aliases": aliases.get("remove", []),
                "func": self.remove,
                "formatter": lambda line: [line],
                "args": {
                    "full_name": ARGS["full_name"],
                    "from_": {
                        **ARGS["from_"],
                        **{"nargs": "?", "default": "today"}
                    },
                    "to": {
                        **ARGS["to"],
                        **{"nargs": "?", "default": "today"}
                    }
                }
            },
            "list": {
                "description": "list tasks",
                "aliases": aliases.get("list", []),
                "func": self.timer.list_tasks,
                "formatter": lambda tasks: [
                    src.output_formatter.pprint_task(task, date=True)
                    for task in tasks
                ],
                "args": {
                    "full_name": {
                        **ARGS["full_name"],
                        **{"nargs": "?", "default": FullName("", set())}
                    },
                    "from_": {
                        **ARGS["from_"],
                        **{"nargs": "?", "default": "today"}
                    },
                    "to": {
                        **ARGS["to"],
                        **{"nargs": "?", "default": "today"}
                    }
                }
            },
            "edit": {
                "description": "edit task",
                "aliases": aliases.get("edit", []),
                "func": self.edit,
                "formatter": lambda line: [line],
                "args": {
                    "full_name": ARGS["full_name"],
                    "from_": {
                        **ARGS["from_"],
                        **{"nargs": "?", "default": "today"}
                    },
                    "to": {
                        **ARGS["to"],
                        **{"nargs": "?", "default": "today"}
                    }
                }
            },
            "sum": {
                "description": "sum up total time",
                "aliases": aliases.get("sum", []),
                "func": self.timer.sum_total,
                "formatter": lambda sums: [
                    src.output_formatter.pprint_sum(
                        FullName(*full_name), total
                    )
                    for full_name, total in sums
                ],
                "args": {
                    "summand": {
                        "type": get_summand,
                        "help": "full name, name or tag(s) to sum up"
                    },
                    "from_": {
                        **ARGS["from_"],
                        **{"nargs": "?", "default": "today"}
                    },
                    "to": {
                        **ARGS["to"],
                        **{"nargs": "?", "default": "today"}
                    }
                }
            },
            "aliases": {
                "description": "list aliases",
                "aliases": aliases.get("aliases", []),
                "func": lambda *args, **kwargs: self.list_aliases(aliases),
                "formatter": lambda multi_part_line: multi_part_line,
                "args": {}
            },
            "export": {
                "description": "export tasks",
                "aliases": aliases.get("export", []),
                "func": self.timer.export,
                "formatter": lambda line: [
                    src.cutils.get_multi_part_line((line, 4))
                ],
                "args": {
                    "ext": {
                        "choices": ("csv", "json"),
                        "metavar": "format"
                    },
                    "from_": {
                        **ARGS["from_"],
                        **{"nargs": "?", "default": "today"}
                    },
                    "to": {
                        **ARGS["to"],
                        **{"nargs": "?", "default": "today"}
                    }
                }
            },
            "help": {
                "description": "show help",
                "aliases": aliases.get("help", [])+["?"],
                "args": {}
            }
        }
        self._init_parser(aliases)

    def _init_parser(self, aliases):
        """Initialize parser.

        :param dict aliases: aliases
        """
        self._parser = argparse.ArgumentParser(prog="", add_help=False)
        self._init_subparsers(self._parser, aliases)

    def _init_subparsers(self, parser, aliases):
        """Initialize subparsers.

        :param ArgumentParser parser: command-line parser
        :param dict aliases: aliases
        """
        subparsers = parser.add_subparsers()
        subcommands = {}
        for prog, subcommand in self.subcommand_defs.items():
            subcommands[prog] = subparsers.add_parser(
                prog,
                description=subcommand["description"],
                add_help=False,
                aliases=subcommand["aliases"]
            )
            if prog == "help":
                continue
            subcommands[prog].set_defaults(
                func=subcommand["func"],
                formatter=subcommand["formatter"]
            )
            for arg, kwargs in subcommand["args"].items():
                subcommands[prog].add_argument(arg, **kwargs)
        subcommands["help"].add_argument(
            "command",
            nargs="?",
            choices=(
                tuple(subcommands.keys())
                + tuple(x for y in aliases.values() for x in y)
            )
        )
        subcommands["help"].set_defaults(
            func=lambda command: command or "",
            formatter=lambda command: self.show_help_message(
                command, subcommands, aliases
            )
        )

    def interpret_line(self, line):
        """Interpret line.

        :param str line: line

        :returns: formatted output
        :rtype: str
        """
        splits = line.split(maxsplit=1)
        if len(splits) > 1:
            splits = [
                splits[0],
                *[
                    split.strip()
                    for split in re.split(r"|".join(self.RESERVED), splits[1])
                ]
            ]
        try:
            fp = StringIO()
            with redirect_stderr(fp):
                args = self._parser.parse_args(splits)
        except SystemExit:
            fp.seek(0)
            raise InterpreterError(
                "\t".join(line.strip() for line in fp.readlines())
            )
        return args.formatter(
            args.func(
                **{
                    k: v for k, v in vars(args).items()
                    if k not in ("func", "formatter")
                }
            )
        )

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
        choices = [src.output_formatter.pprint_task(task) for task in tasks]
        if not choices:
            return src.cutils.get_multi_part_line(("no task", 4))
        i = mk_menu(choices)
        if i < 0:
            return src.cutils.get_multi_part_line(("aborted removing task", 5))
        self.timer.remove(tasks[i])
        return src.cutils.get_multi_part_line(
            (f"removed {''.join(x[0] for x in choices[i])}", 4)
        )

    def edit(
            self,
            full_name=FullName("", frozenset()),
            from_="today",
            to="today"
    ):
        """Choose task to edit.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to
        """
        tasks = list(
            self.timer.list_tasks(full_name=full_name, from_=from_, to=to)
        )
        choices = [src.output_formatter.pprint_task(task) for task in tasks]
        if not choices:
            return src.cutils.get_multi_part_line(("no task", 4))
        i = mk_menu(choices)
        if i < 0:
            return src.cutils.get_multi_part_line(("aborted editing task", 5))
        actions = ("name", "tags", "start", "end")
        j = mk_menu(actions)
        if j < 0:
            return src.cutils.get_multi_part_line(("aborted editing task", 5))
        while True:
            try:
                panel = mk_panel(
                    *get_window_pos(*curses.panel.top_panel().getmaxyx())
                )
                window = panel.window()
                window.box()
                line = readline(
                    window, [], [],
                    boxed=True, prompt=f"new {actions[j]} >", y=1
                )
            except KeyboardInterrupt:
                return src.cutils.get_multi_part_line(
                    ("aborted editing task", 5)
                )
            except ResizeError:
                panel.bottom()
                reinitialize_primary_window()
                continue
            else:
                break
            finally:
                del panel
                curses.panel.update_panels()
        arg = (
            get_name, get_tags, get_from, get_to
        )[j](line)
        if actions[j] in ("start", "end"):
            arg = datetime.datetime.strptime(arg, "%Y-%m-%d %H:%M")
        return src.output_formatter.pprint_task(
            self.timer.edit(tasks[i], actions[j], arg)
        ) if tasks[i] else [src.cutils.get_multi_part_line(("no task", 0))]

    def stop(self):
        """Stop task."""
        if self.timer.task.name:
            self.timer.stop()
            return src.cutils.get_multi_part_line(("", 0))
        return src.cutils.get_multi_part_line(("no running task", 0))

    def show_help_message(self, subcommand, subcommands, aliases):
        """Show help message.

        :param str subcommand: subcommand
        :param dict subcommands: subcommands
        :param dict aliases: aliases
        """
        if subcommand:
            if subcommand not in subcommands:
                for k, v in aliases.items():
                    if subcommand in v:
                        subparser = subcommands[k]
                        break
            else:
                subparser = subcommands[subcommand]
            return [
                src.cutils.get_multi_part_line((help, 4))
                for help in subparser.format_help().split("\n")
            ]
        return [
            src.cutils.get_multi_part_line((usage.strip(), 4))
            for usage in self._parser.format_usage().split("\n")
            if usage
        ]

    def list_aliases(self, aliases):
        """List aliases.

        :param dict aliases: aliases

        :returns: multi-part lines
        :rtype: list
        """
        return [
            src.cutils.get_multi_part_line(("alias\tcommand", 4)),
            tuple(),
            *[
                src.cutils.get_multi_part_line((f"{alias}\t{k}", 4))
                for k, v in aliases.items() for alias in v
            ]
        ]
