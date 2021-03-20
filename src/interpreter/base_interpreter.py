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
:synopsis: Base command-line interpreter.
"""


# standard library imports
import argparse

# third party imports
# library specific imports
import src.output_formatter


class BaseInterpreter:
    """Base command-line interpreter."""

    def _init_parser(self, aliases):
        """Initialize parser.

        :param dict aliases: aliases
        """
        self._parser = argparse.ArgumentParser(prog="", add_help=False)
        self._init_subparsers(aliases)

    def _init_subparsers(self, aliases):
        """Initialize subparsers.

        :param dict aliases: aliases
        """
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
                + tuple(x for y in aliases.values() for x in y)
            ),
        )
        subcommands["help"].set_defaults(
            func=lambda *args, **kwargs: self.help(
                kwargs["command"],
                subcommands,
                aliases,
            )
        )

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
            src.ouput_formatter.pprint_info(usage.strip())
            for usage in self._parser.format_usage().split("\n")
            if usage
        )
