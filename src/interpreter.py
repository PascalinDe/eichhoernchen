#    This file is part of Eichhoernchen 2.1.
#    Copyright (C) 2020  Carine Dengler
#
#    Eichhoernchen is free software: you can redistribute it and/or modify
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
from src.cutils import mk_menu, mk_stats, readline


def _name(name):
    """Name.

    :param str name: string containing name

    :raises ArgumentTypeError: when string does not contain name

    :returns: name
    :rtype: str
    """
    match = re.match(r"(?:\w|\s|[!#+-?])+", name)
    if match:
        return match.group(0).strip()
    raise argparse.ArgumentTypeError(f"'{name}' does not contain name")


def _tags(tags):
    """Tags.

    :param str tags: string containing tags

    :raises ArgumentTypeError: when string does not contain tags

    :returns: tags
    :rtype: set
    """
    matches = re.findall(r"\[((?:\w|\s|[!#+-?])+)\]", tags)
    if matches:
        return set(tag.strip() for tag in matches)
    raise argparse.ArgumentTypeError(f"'{tags}' does not contain any tags")


def _full_name(full_name):
    """Full name.

    :param str full_name: string containing full name

    :raises ArgumentTypeError: when string does not contain full name

    :returns: full name
    :rtype: FullName
    """
    if not full_name:
        return FullName("", frozenset())
    try:
        return FullName(_name(full_name), _tags(full_name))
    except argparse.ArgumentTypeError:
        return FullName(_name(full_name), frozenset())


def _summand(summand):
    """Summand.

    :param str summand: string containing summand

    :raises ArgumentTypeError: when string does not contain summand

    :returns: summand
    :rtype: FullName
    """
    try:
        return _full_name(summand)
    except argparse.ArgumentTypeError:
        return FullName("", _tags(summand))


def _from(from_):
    """From.

    :param str from_: string containing from

    :raises ArgumentTypeError: when string does not contain from

    :returns: from
    :rtype: str
    """
    try:
        return parse_datetime(
            from_, keywords=("all", "year", "month", "week", "yesterday", "today")
        )
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{from_}' does not contain from")


def _to(to):
    """To.

    :param str to: string containing to

    :returns: to
    :rtype: str
    """
    try:
        return parse_datetime(
            to, keywords=("year", "month", "week", "yesterday", "today")
        )
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{to}' does not contain to")


def _start(start):
    """Start.

    :param str start: string containing start

    :raises ArgumentTypeError: when string does not contain start

    :returns: start
    :rtype: str
    """
    try:
        return parse_datetime(start)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{start}' does not contain start")


def _end(end):
    """End.

    :param str end: string containing end

    :raises ArgumentTypeError: when string does not contain end

    :returns: end
    :rtype: str
    """
    return _start(end)


def parse_datetime(date_string, keywords=tuple()):
    """Parse date string.

    :param str date_string: date string
    :param tuple keywords: keywords

    :raises ValueError: when date string does not match any format

    :returns: date string
    :rtype: str
    """
    if keywords:
        match = re.match(r"|".join(keywords), date_string)
        if match:
            return match.group(0)
    for format_string in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%H:%M"):
        try:
            datetime.datetime.strptime(date_string, format_string)
        except ValueError:
            continue
        if format_string == "%H:%M":
            now = datetime.datetime.now()
            date_string = f"{now.year}-{now.month}-{now.day} {date_string}"
        return date_string
    else:
        raise ValueError(f"'{date_string}' does not match any format")


class InterpreterError(Exception):
    """Raised when command-line input cannot be parsed."""

    pass


class Interpreter:
    """Command-line interpreter.

    :cvar dict ARGS: ArgumentParser arguments
    :cvar tuple RESERVED: reserved characters
    :ivar dict subcommands: subcommands
    :ivar Timer timer: timer
    """

    ARGS = {
        "full_name": {
            "type": _full_name,
            "help": "name followed by 0 or more tags, e.g. 'foo[bar]'",
            "metavar": "full name",
        },
        "from_": {
            "type": _from,
            "help": "@([YYYY-MM-DD] [hh:mm]|{all,year,month,week,yesterday,today})",
            "metavar": "from",
        },
        "to": {
            "type": _to,
            "help": "@([YYYY-MM-DD] [hh:mm]|{year,month,week,yesterday,today})",
        },
        "start": {"type": _start, "help": "@YYYY-MM-DD [hh:mm]"},
        "end": {"type": _end, "help": "@YYYY-MM-DD [hh:mm]"},
    }
    RESERVED = ("@",)

    def __init__(self, database, aliases):
        """Initialize command-line interpreter.

        :param str database: pathname of the database
        :param dict aliases: aliases
        """
        self.timer = src.timing.Timer(database)
        self.subcommands = {
            "start": {
                "description": "start task",
                "aliases": aliases.get("start", tuple()),
                "func": self.timer.start,
                "formatter": lambda *args, **kwargs: tuple(),
                "args": {"full_name": self.ARGS["full_name"]},
            },
            "stop": {
                "description": "stop task",
                "aliases": aliases.get("stop", tuple()),
                "func": self.stop,
                "formatter": lambda x: (x,) if x[0][0] else tuple(),
                "args": {},
            },
            "add": {
                "description": "add task",
                "aliases": aliases.get("add", tuple()),
                "func": self.add,
                "formatter": lambda x: (x,),
                "args": {
                    "full_name": self.ARGS["full_name"],
                    "start": self.ARGS["start"],
                    "end": self.ARGS["end"],
                },
            },
            "remove": {
                "description": "remove task",
                "aliases": aliases.get("remove", tuple()),
                "func": self.remove,
                "formatter": lambda x: (x,),
                "args": {
                    "full_name": self.ARGS["full_name"],
                    "from_": {
                        **self.ARGS["from_"],
                        **{"nargs": "?", "default": "today"},
                    },
                },
            },
            "list": {
                "description": "list tasks",
                "aliases": aliases.get("list", tuple()),
                "func": self.timer.list_tasks,
                "formatter": lambda x: (
                    src.output_formatter.pprint_task(y, date=False) for y in x
                ),
                "args": {
                    "full_name": {
                        **self.ARGS["full_name"],
                        **{"nargs": "?", "default": FullName("", set())},
                    },
                    "from_": {
                        **self.ARGS["from_"],
                        **{"nargs": "?", "default": "today"},
                    },
                    "to": {**self.ARGS["to"], **{"nargs": "?", "default": "today"}},
                },
            },
            "show_stats": {
                "description": "show statistics",
                "aliases": aliases.get("show_stats", tuple()),
                "func": self.show_stats,
                "formatter": lambda *args, **kwargs: tuple(),
                "args": {
                    "from_": {
                        **self.ARGS["from_"],
                        **{"nargs": "?", "default": "today"},
                    },
                    "to": {**self.ARGS["to"], **{"nargs": "?", "default": "today"}},
                },
            },
            "edit": {
                "description": "edit task",
                "aliases": aliases.get("edit", tuple()),
                "func": self.edit,
                "formatter": lambda x: (x,),
                "args": {
                    "full_name": self.ARGS["full_name"],
                    "from_": {
                        **self.ARGS["from_"],
                        **{"nargs": "?", "default": "today"},
                    },
                    "to": {
                        **self.ARGS["to"],
                        **{"nargs": "?", "default": "today"},
                    },
                },
            },
            "sum": {
                "description": "sum up total time",
                "aliases": aliases.get("sum", tuple()),
                "func": self.timer.sum_total,
                "formatter": lambda x: (
                    src.output_formatter.pprint_sum(FullName(*y), z) for y, z in x
                ),
                "args": {
                    "summand": {
                        "type": _summand,
                        "help": "full name, name or tag(s) to sum up",
                    },
                    "from_": {
                        **self.ARGS["from_"],
                        **{"nargs": "?", "default": "today"},
                    },
                    "to": {
                        **self.ARGS["to"],
                        **{"nargs": "?", "default": "today"},
                    },
                },
            },
            "aliases": {
                "description": "list aliases",
                "aliases": aliases.get("aliases", tuple()),
                "func": lambda *args, **kwargs: self.aliases(aliases),
                "formatter": lambda x: x,
                "args": {},
            },
            "export": {
                "description": "export tasks",
                "aliases": aliases.get("export", tuple()),
                "func": self.timer.export,
                "formatter": lambda x: (((x, curses.color_pair(4)),),),
                "args": {
                    "ext": {"choices": ("csv", "json"), "metavar": "format"},
                    "from_": {
                        **self.ARGS["from_"],
                        **{"nargs": "?", "default": "today"},
                    },
                    "to": {**self.ARGS["to"], **{"nargs": "?", "default": "today"}},
                },
            },
            "help": {
                "description": "show help",
                "aliases": aliases.get("help", tuple()) + ("?",),
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

        :param ArgumentParser parser: command-line interpreter
        :param dict aliases: aliases
        """
        subparsers = parser.add_subparsers()
        subcommands = {}
        for prog, subcommand in self.subcommands.items():
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
            func=lambda *args, **kwargs: kwargs["command"] or "",
            formatter=lambda x: self.help(x, subcommands, aliases),
        )

    def interpret_line(self, line):
        """Interpret line.

        :param str line: line

        :returns:
        :rtype:
        """
        splits = line.split(maxsplit=1)
        if len(splits) > 1:
            splits = [
                splits[0],
                *[
                    split.strip()
                    for split in re.split(r"|".join(self.RESERVED), splits[1])
                ],
            ]
        # FIXME
        if splits[0] == "show_stats":
            splits = [split for split in splits if split]
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

    def _pick_task(
        self, full_name=FullName("", frozenset()), from_="today", to="today"
    ):
        """Pick task.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to

        :returns: task and pretty-printed task
        :rtype: tuple
        """
        tasks = list(self.timer.list_tasks(full_name=full_name, from_=from_, to=to))
        if not tasks:
            raise RuntimeError("no task")
        items = list(
            self._flatten_items(src.output_formatter.pprint_task(task))
            for task in tasks
        )
        i = mk_menu(items)
        if i < 0:
            raise RuntimeError("aborted removing task")
        return tasks[i], items[i]

    def add(self, full_name=FullName("", frozenset()), start="", end=""):
        """Add task.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to

        :returns: confirmation or error message
        :rtype: tuple
        """
        try:
            task = self.timer.add(full_name=full_name, start=start, end=end)
            return src.output_formatter.pprint_task(task)
        except ValueError as exception:
            return ((str(exception), curses.color_pair(5)),)

    def remove(self, full_name=FullName("", frozenset()), from_="today", to="today"):
        """Choose task to remove.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to

        :returns: confirmation or error message
        :rtype: tuple
        """
        try:
            task, item = self._pick_task(full_name=full_name, from_=from_, to=to)
        except RuntimeError as exception:
            return ((str(exception), curses.color_pair(5)),)
        self.timer.remove(task)
        return ((f"removed {item}", curses.color_pair(4)),)

    def edit(self, full_name=FullName("", frozenset()), from_="today", to="today"):
        """Choose task to edit.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to

        :returns: confirmation or error message
        :rtype: tuple
        """
        try:
            task, item = self._pick_task(full_name=full_name, from_=from_, to=to)
        except RuntimeError as exception:
            return ((str(exception), curses.color_pair(5)),)
        if not task:
            return (("no task", curses.color_pair(0)),)
        actions = ("name", "tags", "start", "end")
        i = mk_menu(actions)
        if i < 0:
            return (("aborted editing task", curses.color_pair(5)),)
        arg = (_name, _tags, _from, _to)[i](readline(prompt=f"new {actions[i]} >"))
        if actions[i] in ("start", "end"):
            arg = datetime.datetime.strptime(arg, "%Y-%m-%d %H:%M")
        return src.output_formatter.pprint_task(self.timer.edit(task, actions[i], arg))

    def stop(self):
        """Stop task.

        :returns: confirmation or error message
        :rtype: tuple
        """
        if self.timer.task.name:
            self.timer.stop()
            return (("", curses.color_pair(0)),)
        return (("no running task", curses.color_pair(0)),)

    def help(self, subcommand, subcommands, aliases):
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
            return (
                ((help, curses.color_pair(4)),)
                for help in subparser.format_help().split("\n")
            )
        return (
            ((usage.strip(), curses.color_pair(4)),)
            for usage in self._parser.format_usage().split("\n")
            if usage
        )

    def aliases(self, aliases):
        """List aliases.

        :param dict aliases: aliases

        :returns: aliases
        :rtype: list
        """
        return (
            (("alias\tcommand", curses.color_pair(4)),),
            tuple(),
            *(
                ((f"{alias}\t{k}", curses.color_pair(4)),)
                for k, v in aliases.items()
                for alias in v
            ),
        )

    def convert_to_date_string(self, endpoint):
        """Convert to date string.

        :param str endpoint: endpoint

        :returns: date string
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
        if endpoint == "year":
            return f"{today.year}-01-01"

    def pprint_heading(self, from_, to):
        """Pretty-print heading.

        :param str from_: from
        :param str to: to

        :returns: heading
        :rtype: str
        """
        if from_ == "all":
            from_ = (
                sorted(
                    self.timer.list_tasks(from_=from_), key=lambda x: x.time_span[0]
                )[0]
                .time_span[0]
                .strftime("%Y-%m-%d")
            )
        ranges = ("year", "month", "week", "yesterday", "today")
        if from_ in ranges:
            from_ = self.convert_to_date_string(from_)
        if to in ranges:
            to = self.convert_to_date_string(to)
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
        heading = self.pprint_heading(from_, to)
        stats = (
            heading,
            ((f"{'—'*len(heading[0][0])}", curses.color_pair(0)),),
            (("", curses.color_pair(0)),),
        )
        tasks = tuple(self.timer.list_tasks(from_=from_, to=to))
        stats += (
            ((f"{len(tasks)} task(s)", curses.color_pair(0)),),
            *(
                src.output_formatter.pprint_task(task, date=(from_ != to))
                for task in tasks
            ),
        )
        tags = {tuple(task.tags) for task in tasks if task.tags}
        pprinted_tags = tuple(
            src.output_formatter.pprint_tags(tuple_)
            for tuple_ in sorted(tags, key=lambda x: len(x))
        )
        stats += (
            ((f"{len(pprinted_tags)} tag(s)", curses.color_pair(0)),),
            *pprinted_tags,
            (("", curses.color_pair(0)),),
        )
        tasks = {(task.name, tuple(task.tags)) for task in tasks}
        sums = sorted(
            (
                sum_
                for name, tags in tasks
                for sum_ in self.timer.sum_total(
                    summand=FullName(name, set(tags)), from_=from_, to=to
                )
            ),
            key=lambda x: x[1],
            reverse=True,
        )
        stats += (
            (("Total runtime task(s)", curses.color_pair(0)),),
            *(
                src.output_formatter.pprint_sum(FullName(*full_name), total)
                for full_name, total in sums
            ),
        )
        sums = sorted(
            (
                sum_
                for tuple_ in tags
                for sum_ in self.timer.sum_total(
                    summand=FullName("", frozenset(tuple_)), from_=from_, to=to
                )
            ),
            key=lambda x: x[1],
            reverse=True,
        )
        stats += (
            (("Total runtime tag(s)", curses.color_pair(0)),),
            *(
                src.output_formatter.pprint_sum(FullName(*full_name), total)
                for full_name, total in sums
            ),
        )
        mk_stats(list(stats))
