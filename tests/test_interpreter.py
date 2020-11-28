#    This file is part of Eichhoernchen 2.2.
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
:synopsis: Command-line interpreter test cases.
"""


# standard library imports
import argparse
import datetime
import unittest

from unittest.mock import patch

# third party imports
# library specific imports
import src.interpreter
import src.output_formatter

from src import FullName


class TestInterpreter(unittest.TestCase):
    """Command-line interpreter test cases.

    :cvar Interpreter interpreter: command-line interpreter
    """

    def test_name(self):
        """Test name.

        Trying: string is name
        Expecting: name
        """
        name = "foo"
        self.assertEqual(src.interpreter._name(name), name)

    def test_name_partial_name(self):
        """Test name.

        Trying: string contains name
        Expecting: partial name
        """
        name = "foob@r"
        self.assertEqual(src.interpreter._name(name), name[:-2])

    def test_name_no_name(self):
        """Test name.

        Trying: string does not contain name
        Expecting: ArgumentTypeError has been raised
        """
        name = "[foo]"
        with self.assertRaises(argparse.ArgumentTypeError):
            src.interpreter._name(name)

    def test_tags(self):
        """Test tags.

        Trying: string is tags
        Expecting: tags
        """
        tags = ("foo", "bar")
        self.assertCountEqual(
            src.interpreter._tags("".join(f"[{tag}]" for tag in tags)), tags
        )

    def test_tags_partial_tags(self):
        """Test tags.

        Trying: string contains tags
        Expecting: tags
        """
        tags = ("foo", "bar")
        self.assertCountEqual(
            src.interpreter._tags("foo" + "".join(f"[{tag}]" for tag in tags)), tags
        )

    def test_tags_no_tags(self):
        """Test tags.

        Trying: string does not contain tags
        Expecting: ArgumentTypeError has been raised
        """
        with self.assertRaises(argparse.ArgumentTypeError):
            src.interpreter._tags("")

    def test_full_name(self):
        """Test full name.

        Trying: string is full name
        Expecting: FullName
        """
        for full_name in (
            FullName("foo", {"bar", "baz"}),
            FullName("foo", frozenset()),
        ):
            self.assertEqual(
                src.interpreter._full_name(
                    full_name.name + "".join(f"[{tag}]" for tag in full_name.tags)
                ),
                full_name,
            )

    def test_full_name_no_full_name(self):
        """Test full name.

        Trying: string does not contain full name
        Expecting: ArgumentTypeError has been raised
        """
        with self.assertRaises(argparse.ArgumentTypeError):
            src.interpreter._full_name("[foo]")

    def test_full_name_empty_string(self):
        """Test full name.

        Trying: empty string
        Expecting: empty FullName
        """
        self.assertEqual(src.interpreter._full_name(""), FullName("", frozenset()))

    def test_summand(self):
        """Test summand.

        Trying: string is summand
        Expecting: FullName
        """
        for full_name in (
            FullName("foo", {"bar", "baz"}),
            FullName("foo", frozenset()),
            FullName("", {"bar", "baz"}),
            FullName("", frozenset()),
        ):
            self.assertEqual(
                src.interpreter._summand(
                    full_name.name + "".join(f"[{tag}]" for tag in full_name.tags)
                ),
                full_name,
            )

    def test_from(self):
        """Test from.

        Trying: from is keyword or matches format
        Expecting: from
        """
        keywords = (
            "all",
            "year",
            "month",
            "week",
            "yesterday",
            "today",
        )
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        for date_string in (*keywords, now):
            self.assertEqual(src.interpreter._from(date_string), date_string)

    def test_to(self):
        """Test to.

        Trying: to is keyword or matches format
        Expecting: to
        """
        keywords = (
            "year",
            "month",
            "week",
            "yesterday",
            "today",
        )
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        for date_string in (*keywords, now):
            self.assertEqual(src.interpreter._to(date_string), date_string)

    def test_start(self):
        """Test start.

        Trying: start matches format
        Expecting: start
        """
        now = datetime.datetime.now()
        for fmt_string in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%H:%M"):
            if fmt_string == "%H:%M":
                expected = now.strftime("%Y-%m-%d %H:%M")
            else:
                expected = now.strftime(fmt_string)
            self.assertEqual(src.interpreter._start(now.strftime(fmt_string)), expected)

    def test_parse_datetime(self):
        """Test parsing date string.

        Trying: date string is keyword or matches format
        Expecting: date string
        """
        keywords = (
            "all",
            "year",
            "month",
            "week",
            "yesterday",
            "today",
        )
        for keyword in keywords:
            self.assertEqual(
                src.interpreter.parse_datetime(keyword, keywords=keywords), keyword
            )
        now = datetime.datetime.now()
        for fmt_string in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%H:%M"):
            if fmt_string == "%H:%M":
                expected = now.strftime("%Y-%m-%d %H:%M")
            else:
                expected = now.strftime(fmt_string)
            self.assertEqual(
                src.interpreter.parse_datetime(now.strftime(fmt_string)), expected
            )

    def test_parse_datetime_no_keyword_or_format(self):
        """Test parsing date string.

        Trying: date string is not keyword or matches any format
        Expecting: ValueError has been raised
        """
        with self.assertRaises(ValueError):
            src.interpreter.parse_datetime("foo")

    def test_interpret_line(self):
        """Test interpreting line.

        Trying: interpreting line
        Expecting: appropriate method is called with correct arguments
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        full_name = FullName("foo", {"bar", "baz", "foobar"})
        subcommands = {
            "start": {"full_name": full_name},
            "stop": dict(),
            "add": {"full_name": full_name, "start": now, "end": now},
            "remove": {"full_name": full_name, "from_": now},
            "edit": {"full_name": full_name, "from_": now, "to": now},
            "list": {"full_name": full_name, "from_": now, "to": now},
            "sum": {"summand": full_name, "from_": now, "to": now},
            "export": {"ext": "csv", "full_name": full_name, "from_": now, "to": now},
            "show_stats": {"from_": now, "to": now},
            "help": {"command": "start"},
            "aliases": dict(),
        }
        for subcommand, kwargs in subcommands.items():
            with patch.object(src.interpreter.Interpreter, subcommand) as mock:
                interpreter = src.interpreter.Interpreter(":memory:", dict())
                line = subcommand
                for k, v in kwargs.items():
                    if k in ("full_name", "summand"):
                        line += f" {v.name}{''.join(f'[{tag}]' for tag in v.tags)}"
                    elif k in ("start", "end", "from_", "to"):
                        line += f" @{v}"
                    else:
                        line += f" {v}"
                interpreter.interpret_line(line)
                mock.assert_called()
                if kwargs:
                    if subcommand == "help":
                        self.assertEqual(kwargs["command"], mock.call_args[0][0])
                    else:
                        mock.assert_called_with(**kwargs)
