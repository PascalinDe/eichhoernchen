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
    get_menu_dims,
    mk_menu,
    mk_panel,
    mk_stats,
    ResizeError,
    WindowManager,
)


def get_name(args):
    """Get name.

    :param str args: command-line arguments

    :raises: ArgumentTypeError when an error is found

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

    :raises: ArgumentTypeError when an error is found

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

    :raises: ArgumentTypeError when an error is found

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

    :raises: ArgumentTypeError when an error is found

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

    :raises: ArgumentTypeError when an error is found

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

    :raises: ArgumentTypeError when an error is found

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

    :raises: ArgumentTypeError when an error is found

    :returns: end point
    :rtype: datetime
    """
    try:
        return src.parser.parse_time(args)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{args}' is not ISO 8601 string")


ARGS = {
    "full_name": {
        "type": get_full_name,
        "help": "name followed by 0 or more tags, e.g. 'foo[bar]'",
        "metavar": "full name",
    },
    "from_": {
        "type": get_from,
        "metavar": "from",
        "help": "@([YYYY-MM-DD] [hh:mm]|{all,year,month,week,yesterday,today})",
    },
    "to": {
        "type": get_to,
        "help": "@([YYYY-MM-DD] [hh:mm]|{year,month,week,yesterday,today})",
    },
    "start": {"type": get_end_point, "help": "@YYYY-MM-DD [hh:mm]"},
    "end": {"type": get_end_point, "help": "@YYYY-MM-DD [hh:mm]"},
}


class InterpreterError(Exception):
    """Raised when shell input cannot be parsed."""

    pass


class Interpreter:
    """Shell interpreter.

    :cvar str RESERVED: reserved characters
    :ivar Timer timer: timer
    :ivar dict subcommand_defs: subcommand definitions
    :ivar ArgumentParser _parser: parser
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
                "args": {"full_name": ARGS["full_name"]},
            },
            "stop": {
                "description": "stop task",
                "aliases": aliases.get("stop", []),
                "func": self.stop,
                "formatter": lambda x: [x] if x[0][0] else [],
                "args": {},
            },
            "add": {
                "description": "add task",
                "aliases": aliases.get("add", []),
                "func": self.timer.add,
                "formatter": lambda task: [src.output_formatter.pprint_task(task)],
                "args": {
                    "full_name": ARGS["full_name"],
                    "start": ARGS["start"],
                    "end": ARGS["end"],
                },
            },
            "remove": {
                "description": "remove task",
                "aliases": aliases.get("remove", []),
                "func": self.remove,
                "formatter": lambda line: [line],
                "args": {
                    "full_name": ARGS["full_name"],
                    "from_": {**ARGS["from_"], **{"nargs": "?", "default": "today"}},
                    "to": {**ARGS["to"], **{"nargs": "?", "default": "today"}},
                },
            },
            "list": {
                "description": "list tasks",
                "aliases": aliases.get("list", []),
                "func": self.timer.list_tasks,
                "formatter": lambda tasks: [
                    src.output_formatter.pprint_task(task, date=True) for task in tasks
                ],
                "args": {
                    "full_name": {
                        **ARGS["full_name"],
                        **{"nargs": "?", "default": FullName("", set())},
                    },
                    "from_": {**ARGS["from_"], **{"nargs": "?", "default": "today"}},
                    "to": {**ARGS["to"], **{"nargs": "?", "default": "today"}},
                },
            },
            "show_stats": {
                "description": "show statistics",
                "aliases": aliases.get("show_stats", []),
                "func": self.show_stats,
                "formatter": lambda *args, **kwargs: [],
                "args": {
                    "from_": {**ARGS["from_"], **{"nargs": "?", "default": "today"}},
                    "to": {**ARGS["to"], **{"nargs": "?", "default": "today"}},
                },
            },
            "edit": {
                "description": "edit task",
                "aliases": aliases.get("edit", []),
                "func": self.edit,
                "formatter": lambda line: [line],
                "args": {
                    "full_name": ARGS["full_name"],
                    "from_": {**ARGS["from_"], **{"nargs": "?", "default": "today"}},
                    "to": {**ARGS["to"], **{"nargs": "?", "default": "today"}},
                },
            },
            "sum": {
                "description": "sum up total time",
                "aliases": aliases.get("sum", []),
                "func": self.timer.sum_total,
                "formatter": lambda sums: [
                    src.output_formatter.pprint_sum(FullName(*full_name), total)
                    for full_name, total in sums
                ],
                "args": {
                    "summand": {
                        "type": get_summand,
                        "help": "full name, name or tag(s) to sum up",
                    },
                    "from_": {**ARGS["from_"], **{"nargs": "?", "default": "today"}},
                    "to": {**ARGS["to"], **{"nargs": "?", "default": "today"}},
                },
            },
            "aliases": {
                "description": "list aliases",
                "aliases": aliases.get("aliases", []),
                "func": lambda *args, **kwargs: self.list_aliases(aliases),
                "formatter": lambda multi_part_line: multi_part_line,
                "args": {},
            },
            "export": {
                "description": "export tasks",
                "aliases": aliases.get("export", []),
                "func": self.timer.export,
                "formatter": lambda line: (((line, curses.color_pair(4)),),),
                "args": {
                    "ext": {"choices": ("csv", "json"), "metavar": "format"},
                    "from_": {**ARGS["from_"], **{"nargs": "?", "default": "today"}},
                    "to": {**ARGS["to"], **{"nargs": "?", "default": "today"}},
                },
            },
            "help": {
                "description": "show help",
                "aliases": aliases.get("help", []) + ["?"],
                "args": {},
            },
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
                aliases=subcommand["aliases"],
            )
            if prog == "help":
                continue
            subcommands[prog].set_defaults(
                func=subcommand["func"], formatter=subcommand["formatter"]
            )
            for arg, kwargs in subcommand["args"].items():
                subcommands[prog].add_argument(arg, **kwargs)
        subcommands["help"].add_argument(
            "command",
            nargs="?",
            choices=(
                tuple(subcommands.keys())
                + tuple(x for y in aliases.values() for x in y)
            ),
        )
        subcommands["help"].set_defaults(
            func=lambda command: command or "",
            formatter=lambda command: self.show_help_message(
                command, subcommands, aliases
            ),
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
                    if split.strip()
                ],
            ]
        try:
            fp = StringIO()
            with redirect_stderr(fp):
                args = self._parser.parse_args(splits)
        except SystemExit:
            fp.seek(0)
            raise InterpreterError("\t".join(line.strip() for line in fp.readlines()))
        return args.formatter(
            args.func(
                **{
                    k: v
                    for k, v in vars(args).items()
                    if k not in ("func", "formatter")
                }
            )
        )

    def _flatten_items(self, items):
        """Flatten menu items.

        :param list items: items

        :returns: flattened items
        :rtype: str
        """
        return "".join(item[0] for item in items)

    def remove(self, full_name=FullName("", frozenset()), from_="today", to="today"):
        """Choose task to remove.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to

        :returns: confirmation/error message
        :rtype: tuple
        """
        tasks = list(self.timer.list_tasks(full_name=full_name, from_=from_, to=to))
        items = [
            self._flatten_items(src.output_formatter.pprint_task(task))
            for task in tasks
        ]
        if not items:
            return (("no task", curses.color_pair(4)),)
        i = mk_menu(items)
        if i < 0:
            return (("aborted removing task", curses.color_pair(5)),)
        self.timer.remove(tasks[i])
        return ((f"removed {''.join(x[0] for x in items[i])}", curses.color_pair(4)),)

    def edit(self, full_name=FullName("", frozenset()), from_="today", to="today"):
        """Choose task to edit.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to

        :returns: confirmation/error message
        :rtype: tuple
        """
        tasks = list(self.timer.list_tasks(full_name=full_name, from_=from_, to=to))
        items = [
            self._flatten_items(src.output_formatter.pprint_task(task))
            for task in tasks
        ]
        if not items:
            return (("no task", curses.color_pair(4)),)
        i = mk_menu(items)
        if i < 0:
            return (("aborted editing task", curses.color_pair(5)),)
        actions = ("name", "tags", "start", "end")
        j = mk_menu(actions)
        if j < 0:
            return (("aborted editing task", curses.color_pair(5)),)
        while True:
            try:
                panel = mk_panel(
                    *get_menu_dims(*curses.panel.top_panel().window().getmaxyx())
                )
                window = panel.window()
                window_mgr = WindowManager(window, box=True)
                line = window_mgr.readline(prompt=f"new {actions[j]} >", y=1)
            except KeyboardInterrupt:
                return (("aborted editing task", curses.color_pair(5)),)
            except ResizeError:
                panel.bottom()
                window.reinitialize()
                continue
            else:
                break
            finally:
                del panel
                curses.panel.update_panels()
        arg = (get_name, get_tags, get_from, get_to)[j](line)
        if actions[j] in ("start", "end"):
            arg = datetime.datetime.strptime(arg, "%Y-%m-%d %H:%M")
        return (
            src.output_formatter.pprint_task(self.timer.edit(tasks[i], actions[j], arg))
            if tasks[i]
            else (("no task", curses.color_pair(0)),)
        )

    def stop(self):
        """Stop task.

        :returns: confirmation/error message
        :rtype: tuple
        """
        if self.timer.task.name:
            self.timer.stop()
            return (("", curses.color_pair(0)),)
        return (("no running task", curses.color_pair(0)),)

    def show_help_message(self, subcommand, subcommands, aliases):
        """Show help message.

        :param str subcommand: subcommand
        :param dict subcommands: subcommands
        :param dict aliases: aliases

        :returns: help message
        :rtype: tuple
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
                ((help, curses.color_pair(4)),)
                for help in subparser.format_help().split("\n")
            ]
        return [
            ((usage.strip(), curses.color_pair(4)),)
            for usage in self._parser.format_usage().split("\n")
            if usage
        ]

    def list_aliases(self, aliases):
        """List aliases.

        :param dict aliases: aliases

        :returns: aliases
        :rtype: list
        """
        return [
            (("alias\tcommand", curses.color_pair(4)),),
            tuple(),
            *[
                ((f"{alias}\t{k}", curses.color_pair(4)),)
                for k, v in aliases.items()
                for alias in v
            ],
        ]

    def _get_date(self, endpoint):
        """Get date.

        :param str endpoint: endpoint

        :returns: date
        :rtype: str
        """
        today = datetime.datetime.today()
        if endpoint == "today":
            return today.strftime("%Y-%m-%d")
        if endpoint == "yesterday":
            return (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        if endpoint == "week":
            return (today - datetime.timedelta(days=today.weekday())).strftime(
                "%Y-%m-%d"
            )
        if endpoint == "month":
            return f"{today.year}-{today.month:02}-01"

    def _get_heading(self, from_, to):
        """Get heading.

        :param str from_: from
        :param str to: to

        :returns: heading
        :rtype: tuple
        """
        ranges = ("today", "yesterday", "week", "month")
        if from_ in ranges:
            from_ = self._get_date(from_)
        if to in ranges:
            to = self._get_date(to)
        from_ = datetime.datetime.strptime(from_, "%Y-%m-%d").strftime("%a %d %b %Y")
        to = datetime.datetime.strptime(to, "%Y-%m-%d").strftime("%a %d %b %Y")
        if from_ != to:
            return ((f"overview {from_} - {to}".upper(), curses.color_pair(0)),)
        return ((f"overview {from_}".upper(), curses.color_pair(0)),)

    def show_stats(self, from_="today", to="today"):
        """Show statistics.

        :param str from_: from
        :param str to: to
        """
        heading = self._get_heading(from_, to)
        stats = [
            heading,
            ((f"{'—'*len(heading[0][0])}", curses.color_pair(0)),),
            (("", curses.color_pair(0)),),
        ]
        tasks = list(self.timer.list_tasks(from_=from_, to=to))
        stats += [
            ((f"{len(tasks)} task(s)", curses.color_pair(0)),),
            *(
                src.output_formatter.pprint_task(task, date=(from_ != to))
                for task in tasks
            ),
        ]
        unique_tags = {tuple(task.tags) for task in tasks if task.tags}
        pprinted_tags = [
            src.output_formatter.pprint_tags(tags)
            for tags in sorted(unique_tags, key=lambda x: len(x))
        ]
        stats += [
            ((f"{len(pprinted_tags)} tag(s)", curses.color_pair(0)),),
            *pprinted_tags,
            (("", curses.color_pair(0)),),
        ]
        unique_tasks = {(task.name, tuple(task.tags)) for task in tasks}
        sums = sorted(
            (
                sum_
                for name, tags in unique_tasks
                for sum_ in self.timer.sum_total(
                    summand=FullName(name, set(tags)), from_=from_, to=to
                )
            ),
            key=lambda x: x[1],
            reverse=True,
        )
        stats += [
            (("Total runtime task(s)", curses.color_pair(0)),),
            *(
                src.output_formatter.pprint_sum(FullName(*full_name), total)
                for full_name, total in sums
            ),
        ]
        sums = sorted(
            (
                sum_
                for tags in unique_tags
                for sum_ in self.timer.sum_total(
                    summand=FullName("", set(tags)), from_=from_, to=to
                )
            ),
            key=lambda x: x[1],
            reverse=True,
        )
        stats += [
            (("Total runtime tag(s)", curses.color_pair(0)),),
            *(
                src.output_formatter.pprint_sum(FullName(*full_name), total)
                for full_name, total in sums
            ),
        ]
        mk_stats(stats)
