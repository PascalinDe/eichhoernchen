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
:synopsis: Command-line interpreter test cases.
"""


# standard library imports
import os
import datetime
import unittest
from itertools import product

# third party imports
# library specific imports
from src.interpreter.interpreter import Interpreter


ARGS = {
    "full_name": ("foo", "foo bar", "foo bar[baz]", "foo bar[baz][foobar]"),
    "to": (
        "@year",
        "@month",
        "@week",
        "@yesterday",
        "@today",
        f"@{datetime.datetime.now().strftime('%Y-%m-%d')}",
    ),
    "start": (
        f"@{datetime.datetime.now().strftime('%H:%M')}",
        f"@{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ),
    "end": (
        f"@{datetime.datetime.now().strftime('%H:%M')}",
        f"@{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ),
    "summand": ("foo bar", "foo bar[baz]", "[foobar]"),
    "ext": ("csv", "json"),
}
ARGS["from_"] = ("@all", *ARGS["to"])


def _product(largs, rargs):
    """Product.

    :param tuple largs: left-hand command arguments
    :param tuple rargs: right-hand command arguments

    :returns: command arguments
    :rtype: dict
    """
    return {
        "line": tuple(
            " ".join(line) for line in sorted(product(largs["line"], rargs["line"]))
        ),
        "expected": tuple(
            expected[0] + expected[1]
            for expected in sorted(product(largs["expected"], rargs["expected"]))
        ),
    }


def _get_args(cmd):
    """Get command arguments.

    :param str cmd: command

    :returns: command arguments
    :rtype: dict
    """
    full_name = {
        "line": ARGS["full_name"],
        "expected": tuple((full_name,) for full_name in ARGS["full_name"]),
    }
    from_ = {
        "line": ARGS["from_"],
        "expected": tuple((from_,) for from_ in ARGS["from_"]),
    }
    to = {"line": ARGS["to"], "expected": tuple((to,) for to in ARGS["to"])}
    if cmd == "start":
        return full_name
    if cmd in ("stop", "clean_up", "aliases"):
        return {"line": ((""),), "expected": tuple()}
    if cmd == "add":
        return _product(
            full_name,
            _product(
                {
                    "line": ARGS["start"],
                    "expected": tuple((start,) for start in ARGS["start"]),
                },
                {"line": ARGS["end"], "expected": tuple((end,) for end in ARGS["end"])},
            ),
        )
    if cmd == "remove":
        from_["line"] = (*from_["line"], "")
        from_["expected"] += (tuple(),)
        return _product(full_name, from_)
    if cmd in ("edit", "list", "sum", "export", "show_stats"):
        to["line"] = (*to["line"], "")
        to["expected"] += (tuple(),)
        rargs = _product(from_, to)
        rargs["line"] = (*rargs["line"], "")
        rargs["expected"] += (tuple(),)
        if cmd == "show_stats":
            return rargs
        if cmd == "sum":
            args = _product(
                {
                    "line": ARGS["summand"],
                    "expected": tuple((summand,) for summand in ARGS["summand"]),
                },
                rargs,
            )
        else:
            args = _product(full_name, rargs)
        if cmd in ("list", "export"):
            full_name["line"] = (*full_name["line"], "")
            full_name["expected"] += (("",),)
            if cmd == "export":
                largs = _product(
                    {
                        "line": ARGS["ext"],
                        "expected": tuple((ext,) for ext in ARGS["ext"]),
                    },
                    full_name,
                )
                args = _product(largs, rargs)
            if cmd == "list":
                args = _product(full_name, rargs)
                args["line"] = (*args["line"], "")
                args["expected"] += (("",),)
        return args
    if cmd in ("help", "?"):
        cmds = (
            "start",
            "stop",
            "add",
            "remove",
            "edit",
            "list",
            "clean_up",
            "sum",
            "export",
            "show_stats",
            "help",
            "?",
            "aliases",
        )
        return {"line": cmds, "expected": tuple((cmd,) for cmd in cmds)}


class TestInterpreter(unittest.TestCase):
    """Command-line interpreter test cases."""

    DATABASE = "test.db"

    def setUp(self):
        """Set up test cases."""
        self.interpreter = Interpreter(
            {"database": {"path": "", "dbname": self.DATABASE}, "aliases": {}}
        )

    def tearDown(self):
        """Tear down test cases."""
        try:
            os.remove(self.DATABASE)
        except FileNotFoundError:
            pass

    def test_split_args(self):
        """Test splitting arguments."""
        for cmd in (
            "start",
            "stop",
            "add",
            "remove",
            "edit",
            "list",
            "clean_up",
            "sum",
            "export",
            "show_stats",
            "help",
            "?",
            "aliases",
        ):
            args = _get_args(cmd)
            for line, expected in zip(args["line"], args["expected"]):
                self.assertEqual(self.interpreter.split_args(cmd, line), expected)
