#    This file is part of Eichhoernchen 2.2.
#    Copyright (C) 2018-2021  Carine Dengler
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
import src.timer

from src import FullName
from src.cutils import mk_menu, mk_stats, readline


def _name(name):
    """Name.

    :param str name: string containing name

    :raises ArgumentTypeError: when string does not contain name

    :returns: name
    :rtype: str
    """
    match = re.match(r"(?:\w|\s|[!#'+-?])+", name)
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
    matches = re.findall(r"\[((?:\w|\s|[!#'+-?])+)\]", tags)
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

    :raises ArgumentTypeError: when string does not contain to

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
            date_string = f"{now.year:04}-{now.month:02}-{now.day:02} {date_string}"
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
        self.timer = src.timer.Timer(database)
        self.subcommands = {
            "start": {
                "description": "start task",
                "aliases": aliases.get("start", tuple()),
                "func": self.start,
                "args": {"full_name": self.ARGS["full_name"]},
            },
            "stop": {
                "description": "stop task",
                "aliases": aliases.get("stop", tuple()),
                "func": self.stop,
                "args": {},
            },
            "add": {
                "description": "add task",
                "aliases": aliases.get("add", tuple()),
                "func": self.add,
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
                "args": {
                    "full_name": self.ARGS["full_name"],
                    "from_": {
                        **self.ARGS["from_"],
                        **{"nargs": "?", "default": "today"},
                    },
                },
            },
            "clean_up": {
                "description": "list buggy tasks to clean up",
                "aliases": aliases.get("clean_up", tuple()),
                "func": self.clean_up,
                "args": {},
            },
            "edit": {
                "description": "edit task",
                "aliases": aliases.get("edit", tuple()),
                "func": self.edit,
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
            "list": {
                "description": "list tasks",
                "aliases": aliases.get("list", tuple()),
                "func": self.list,
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
            "sum": {
                "description": "sum up total time",
                "aliases": aliases.get("sum", tuple()),
                "func": self.sum,
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
            "export": {
                "description": "export tasks",
                "aliases": aliases.get("export", tuple()),
                "func": self.export,
                "args": {
                    "ext": {"choices": ("csv", "json"), "metavar": "format"},
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
                "args": {
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
            "aliases": {
                "description": "list aliases",
                "aliases": aliases.get("aliases", tuple()),
                "func": lambda *args, **kwargs: self.aliases(aliases),
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
            subcommands[prog].set_defaults(func=subcommand["func"])
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
            func=lambda *args, **kwargs: self.help(
                kwargs["command"], subcommands, aliases
            )
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
        if splits[0] == "export":
            splits = [splits[0], *splits[1].split(maxsplit=1), *splits[2:]]
        if splits[0] == "show_stats":
            splits = [split for split in splits if split]
        try:
            fp = StringIO()
            with redirect_stderr(fp):
                args = self._parser.parse_args(splits)
        except SystemExit:
            fp.seek(0)
            raise InterpreterError("\t".join(line.strip() for line in fp.readlines()))
        return args.func(**{k: v for k, v in vars(args).items() if k != "func"})

    def start(self, full_name=FullName("", frozenset())):
        """Start task.

        :param FullName full_name: full name

        :returns: empty line or error message
        :rtype: tuple
        """
        if self.timer.task.name:
            return (src.output_formatter.pprint_error("a task is already running"),)
        self.timer.start(full_name)
        return tuple()

    def stop(self):
        """Stop task.

        :returns: confirmation or error message
        :rtype: tuple
        """
        if self.timer.task.name:
            self.timer.stop()
            return tuple()
        return (src.output_formatter.pprint_error("no task is running"),)

    def add(self, full_name=FullName("", frozenset()), start="", end=""):
        """Add task.

        :param FullName full_name: full name
        :param str start: start of time period
        :param str end: end of time period

        :returns: confirmation or error message
        :rtype: tuple
        """
        try:
            task = self.timer.add(
                full_name,
                datetime.datetime.strptime(start, "%Y-%m-%d %H:%M"),
                datetime.datetime.strptime(end, "%Y-%m-%d %H:%M"),
            )
            return (src.output_formatter.pprint_task(task),)
        except ValueError as exception:
            return (src.output_formatter.pprint_error(str(exception)),)

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

        :raises RuntimeError: if task does not exist or operation has been aborted

        :returns: task and pretty-printed task
        :rtype: tuple
        """
        tasks = list(
            self.timer.list(
                self._convert_to_date_string(from_),
                self._convert_to_date_string(to),
                full_name=full_name,
            )
        )
        pprint_full_name = "".join(
            x[0] for x in src.output_formatter.pprint_full_name(full_name)
        )
        if not tasks:
            raise RuntimeError(f"no task '{pprint_full_name}'")
        items = list(
            self._flatten_items(src.output_formatter.pprint_task(task))
            for task in tasks
        )
        i = mk_menu(items)
        if i < 0:
            raise RuntimeError(f"abort removing task '{pprint_full_name}'")
        return tasks[i], items[i]

    def _convert_to_date_string(self, endpoint):
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
            return f"{today.year:04}-{today.month:02}-01"
        if endpoint == "year":
            return f"{today.year:04}-01-01"
        if endpoint == "all":
            return "0000-01-01"
        return endpoint

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
            return (src.output_formatter.pprint_error(str(exception)),)
        self.timer.remove(task)
        return (src.output_formatter.pprint_info(f"removed {item}"),)

    def clean_up(self):
        """List buggy tasks to clean up."""
        return (
            src.output_formatter.pprint_task(task, date=True)
            for task in self.timer.clean_up()
        )

    def edit(self, full_name=FullName("", frozenset()), from_="today", to="today"):
        """Choose task to edit.

        :param FullName full_name: full name
        :param str from_: from
        :param str to: to

        :returns: confirmation or error message
        :rtype: tuple
        """
        pprint_full_name = "".join(
            x[0] for x in src.output_formatter.pprint_full_name(full_name)
        )
        try:
            task, item = self._pick_task(full_name=full_name, from_=from_, to=to)
        except RuntimeError as exception:
            return (src.output_formatter.pprint_error(exception),)
        if not task:
            return (src.output_formatter.pprint_error(f"no task '{pprint_full_name}'"),)
        actions = ("name", "tags", "start", "end")
        i = mk_menu(actions)
        if i < 0:
            return (
                src.output_formatter.pprint_error(
                    f"abort editing task '{pprint_full_name}'"
                ),
            )
        try:
            arg = (_name, _tags, _from, _to)[i](
                readline(prompt=((f"new {actions[i]} >", curses.color_pair(0)),))
            )
        except EOFError:
            return (
                src.output_formatter.pprint_error(
                    f"abort editing task '{pprint_full_name}'"
                ),
            )
        if actions[i] in ("start", "end"):
            arg = datetime.datetime.strptime(arg, "%Y-%m-%d %H:%M")
        try:
            return (
                src.output_formatter.pprint_task(
                    self.timer.edit(task, actions[i], arg)
                ),
            )
        except ValueError as exception:
            return (src.output_formatter.pprint_error(exception),)

    def list(self, full_name=FullName("", frozenset()), from_="today", to="today"):
        """List tasks.

        :param FullName full_name: full name
        :param str from_: start of time period
        :param str to: end of time period
        :param bool full_match: toggle matching full name on/off

        :returns: tasks
        :rtype: tuple
        """
        return tuple(
            src.output_formatter.pprint_task(
                task, date=from_ not in ("today", self._convert_to_date_string("today"))
            )
            for task in self.timer.list(
                self._convert_to_date_string(from_),
                self._convert_to_date_string(to),
                full_name=full_name,
                full_match=any(full_name),
            )
        )

    def sum(self, summand=FullName("", frozenset()), from_="today", to="today"):
        """Sum total time up.

        :param FullName summand: full name
        :param str from_: start of time period
        :param str to: end of time period

        :returns: summed up total time per task
        :rtype: tuple
        """
        return tuple(
            src.output_formatter.pprint_sum(FullName(*x), y)
            for x, y in self.timer.sum(
                self._convert_to_date_string(from_),
                self._convert_to_date_string(to),
                full_name=summand,
                full_match=any(summand),
            )
        )

    def export(
        self, ext="", full_name=FullName("", frozenset()), from_="today", to="today"
    ):
        """Export tasks.

        :param str ext: file format
        :param FullName full_name: full name
        :param str from_: start of time period
        :param str to: end of time period

        :returns: confirmation or error message
        :rtype: tuple
        """
        filename = self.timer.export(
            ext,
            self._convert_to_date_string(from_),
            self._convert_to_date_string(to),
            full_name=full_name,
        )
        return (src.output_formatter.pprint_info(f"exported tasks to {filename}"),)

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
            from_ = self._convert_to_date_string(from_)
        if to in ranges:
            to = self._convert_to_date_string(to)
        from_ = datetime.datetime.strptime(from_, "%Y-%m-%d").strftime("%a %d %b %Y")
        to = datetime.datetime.strptime(to, "%Y-%m-%d").strftime("%a %d %b %Y")
        if from_ != to:
            return ((f"overview {from_} - {to}".upper(), curses.color_pair(0)),)
        return ((f"overview {from_}".upper(), curses.color_pair(0)),)

    def show_stats(self, from_="today", to="today"):
        """Show statistics.

        :param str from_: from
        :param str to: to

        :returns: empty message
        :rtype: tuple
        """
        tasks = tuple(
            self.timer.list(
                self._convert_to_date_string(from_),
                self._convert_to_date_string(to),
                full_match=False,
            )
        )
        from_ = tasks[0].time_span[0].strftime("%Y-%m-%d") if tasks else from_
        heading = self.pprint_heading(from_, to)
        stats = (
            heading,
            ((f"{'—'*len(heading[0][0])}", curses.color_pair(0)),),
            (("", curses.color_pair(0)),),
        )
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
                for sum_ in self.timer.sum(
                    self._convert_to_date_string(from_),
                    self._convert_to_date_string(to),
                    full_name=FullName(name, set(tags)),
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
                for sum_ in self.timer.sum(
                    self._convert_to_date_string(from_),
                    self._convert_to_date_string(to),
                    full_name=FullName("", frozenset(tuple_)),
                    full_match=False,
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
        return tuple()

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
            return tuple(
                src.output_formatter.pprint_info(help)
                for help in subparser.format_help().split("\n")
            )
        return tuple(
            src.output_formatter.pprint_info(usage.strip())
            for usage in self._parser.format_usage().split("\n")
            if usage
        )

    def aliases(self, aliases):
        """List aliases.

        :param dict aliases: aliases

        :returns: aliases
        :rtype: list
        """
        if not aliases:
            return (src.output_formatter.pprint_error("no aliases have been defined"),)
        return (
            src.output_formatter.pprint_info("alias\tcommand"),
            tuple(),
            *(
                src.output_formatter.pprint_info(f"{alias}\t{k}")
                for k, v in aliases.items()
                for alias in v
            ),
        )
