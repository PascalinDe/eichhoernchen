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
:synopsis: Command-line interpreter utils.
"""


# standard library imports
import re
import argparse
import datetime

from io import StringIO
from contextlib import redirect_stderr

# third party imports
# library specific imports
import src.output_formatter

from src import FullName


def match_name(name):
    """Match name.

    :param str name: string containing name

    :raises ArgumentTypeError: when string does not contain name

    :returns: name
    :rtype: str
    """
    if match := re.match(r"(?:\w|\s|[!#'+-?])+", name):
        return match.group(0).strip()
    raise argparse.ArgumentTypeError(f"'{name}' does not contain name")


def match_tags(tags):
    """Match tags.

    :param str tags: string containing tags

    :raises ArgumentTypeError: when string does not contain tags

    :returns: tags
    :rtype: set
    """
    if matches := re.findall(r"\[((?:\w|\s|[!#'+-?])+)\]", tags):
        return set(tag.strip() for tag in matches)
    raise argparse.ArgumentTypeError(f"'{tags}' does not contain any tags")


def match_full_name(full_name):
    """Match full name.

    :param str full_name: string containing full name

    :raises ArgumentTypeError: when string does not contain full name

    :returns: full name
    :rtype: FullName
    """
    if not full_name:
        return FullName("", frozenset())
    try:
        return FullName(match_name(full_name), match_tags(full_name))
    except argparse.ArgumentTypeError:
        return FullName(match_name(full_name), frozenset())


def match_summand(summand):
    """Match summand.

    :param str summand: string containing summand

    :raises ArgumentTypeError: when string does not contain summand

    :returns: summand
    :rtype: FullName
    """
    try:
        return match_full_name(summand)
    except argparse.ArgumentTypeError:
        return FullName("", match_tags(summand))


def match_from(from_):
    """Match from.

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


def match_to(to):
    """Match to.

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


def match_start(start):
    """Match start.

    :param str start: string containing start

    :raises ArgumentTypeError: when string does not contain start

    :returns: start
    :rtype: str
    """
    try:
        return parse_datetime(start)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{start}' does not contain start")


def match_end(end):
    """Match end.

    :param str end: string containing end

    :raises ArgumentTypeError: when string does not contain end

    :returns: end
    :rtype: str
    """
    return match_start(end)


def parse_datetime(date_string, keywords=tuple()):
    """Parse date string.

    :param str date_string: date string
    :param tuple keywords: keywords

    :raises ArgumentTypeError: when date string does not match
    any keyword or format string

    :returns: date string
    :rtype: str
    """
    if keywords:
        if match := re.match(f"@({r'|'.join(keywords)})", date_string):
            return match.group(1)
    for format_string in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%H:%M"):
        try:
            datetime.datetime.strptime(date_string, f"@{format_string}")
        except ValueError:
            continue
        date_string = date_string.lstrip("@")
        if format_string == "%H:%M":
            now = datetime.datetime.now()
            date_string = f"{now.year:04}-{now.month:02}-{now.day:02} {date_string}"
        return date_string
    raise argparse.ArgumentTypeError(
        f"{date_string} does not match any keyword or format string"
    )


class InterpreterError(Exception):
    """Raised when command-line cannot be interpreted."""

    pass


class NoSuchTask(Exception):
    """Raised when no task fits the description."""

    pass


class UserAbort(Exception):
    """Raised when the user aborted the operation."""

    pass


class InterpreterMixin:
    """Command-line interpreter mixin."""

    def __init__(self):
        """Initialize command-line interpreter mixin."""
        self.subcommands["help"] = {
            "description": "show help",
            "aliases": self.aliases.get("help", tuple()) + ("?",),
            "args": {},
        }
        self.subcommands["aliases"] = {
            "description": "list aliases",
            "aliases": self.aliases.get("aliases", tuple()),
            "func": lambda *args, **kwargs: self.list_aliases(),
            "args": {},
        }

    def _init_parser(self):
        """Initialize parser."""
        self._parser = argparse.ArgumentParser(prog="", add_help=False)
        self._init_subparsers()

    def _init_subparsers(self):
        """Initialize subparsers."""
        subparsers = self._parser.add_subparsers()
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
                + tuple(x for y in self.aliases.values() for x in y)
            ),
        )
        subcommands["help"].set_defaults(
            func=lambda *args, **kwargs: self.help(
                kwargs["command"],
                subcommands,
            )
        )

    def help(self, subcommand, subcommands):
        """Show help message.

        :param str subcommand: subcommand
        :param dict subcommands: subcommands

        :returns: help message
        :rtype: tuple
        """
        if subcommand:
            if subcommand not in subcommands:
                for k, v in self.aliases.items():
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

    def list_aliases(self):
        """List aliases.

        :returns: aliases
        :rtype: tuple
        """
        if not self.aliases:
            return (src.output_formatter.pprint_error("no aliases have been set"),)
        return (
            src.output_formatter.pprint_info("alias\tcommand"),
            tuple(),
            *(
                src.output_formatter.pprint_info(f"{alias}\t{command}")
                for command, aliases in self.aliases.items()
                for alias in aliases
            ),
        )

    def split_args(self, cmd, line):
        """Split arguments.

        :param str cmd: command
        :param str line: rest of the line

        :returns: arguments
        :rtype: tuple
        """
        return tuple(
            arg.strip() for arg in re.split(fr"(?={'|'.join(self.SEP)})", line) if arg
        )

    def interpret_line(self, line):
        """Interpret line.

        :param str line: line

        :returns: output
        :rtype: tuple
        """
        cmd, *args = line.split(maxsplit=1)
        if cmd in self.subcommands and args:
            args = self.split_args(cmd, *args)
        try:
            fp = StringIO()
            with redirect_stderr(fp):
                args = self._parser.parse_args((cmd, *args))
        except SystemExit:
            fp.seek(0)
            raise InterpreterError("\t".join(line.strip() for line in fp.readlines()))
        return args.func(**{k: v for k, v in vars(args).items() if k != "func"})
