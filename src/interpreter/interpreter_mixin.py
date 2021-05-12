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
:synopsis: Command-line interpreter mixin.
"""


# standard library imports
import logging
import argparse

from io import StringIO
from contextlib import redirect_stderr

# third party imports

# library specific imports
import src.output_formatter

from src.interpreter.utils import search_datetime


class InterpreterError(Exception):
    """Raised when command-line input cannot be parsed."""

    pass


class InterpreterMixin:
    """Command-line interpreter mixin."""

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

    def split_args(self, cmd, line):
        """Split arguments.

        :param str cmd: command
        :param str line: rest of the line

        :returns: arguments
        :rtype: list
        """
        args = []
        positionals = {
            k: v for k, v in self.subcommands[cmd]["args"].items() if "nargs" not in v
        }
        optionals = {
            k: v for k, v in self.subcommands[cmd]["args"].items() if "nargs" in v
        }
        spans = tuple(search_datetime(line))
        for span in spans:
            args.append(line[span[0] : span[1]])
        # datetime arguments are at the end
        line = line[: spans[0][0]] if spans else line
        for k in ("from_", "to", "start", "end"):
            positionals.pop(k, None)
            optionals.pop(k, None)
        if "full_name" in positionals:
            # full_name is first required argument
            args = line.rsplit(maxsplit=len(positionals) + len(optionals) - 1) + args
        elif "full_name" in optionals:
            # full_name is first optional argument
            maxsplit = len(positionals)
            splits = line.split(maxsplit=maxsplit)[:maxsplit]
            (line,) = splits[maxsplit:]
            rsplits = line.rsplit(maxsplit=len(optionals) - 1)
            args = splits + rsplits + args
        else:
            args = line.split(maxsplit=len(positionals) + len(optionals)) + args
        return args

    def interpret_line(self, line):
        """Interpret line.

        :param str line: line

        :returns: output
        :rtype: tuple
        """
        logger = logging.getLogger(self.interpret_line.__name__)
        cmd, *args = line.split(maxsplit=1)
        if args:
            (args,) = args
            if cmd in self.subcommands:
                args = self.split_args(cmd, args)
        try:
            fp = StringIO()
            with redirect_stderr(fp):
                logger.debug(f"{cmd}: {','.join(args)}")
                args = self._parser.parse_args((cmd, *args))
        except SystemExit:
            fp.seek(0)
            raise InterpreterError("\t".join(line.strip() for line in fp.readlines()))
        return args.func(**{k: v for k, v in vars(args).items() if k != "func"})
