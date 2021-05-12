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
import datetime

from argparse import ArgumentTypeError

# third party imports
# library specific imports
from src import FullName


def match_name(name):
    """Match name.

    :param str name: string containing name

    :raises ArgumentTypeError: when string does not contain name

    :returns: name
    :rtype: str
    """
    match = re.match(r"(?:\w|\s|[!#'+-?])+", name)
    if match:
        return match.group(0).strip()
    raise ArgumentTypeError(f"'{name}' does not contain name")


def match_tags(tags):
    """Match tags.

    :param str tags: string containing tags

    :raises ArgumentTypeError: when string does not contain tags

    :returns: tags
    :rtype: set
    """
    matches = re.findall(r"\[((?:\w|\s|[!#'+-?])+)\]", tags)
    if matches:
        return set(tag.strip() for tag in matches)
    raise ArgumentTypeError(f"'{tags}' does not contain any tags")


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
    except ArgumentTypeError:
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
    except ArgumentTypeError:
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
        raise ArgumentTypeError(f"'{from_}' does not contain from")


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
        raise ArgumentTypeError(f"'{to}' does not contain to")


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
        ArgumentTypeError(f"'{start}' does not contain start")


def match_end(end):
    """Match end.

    :param str end: string containing end

    :raises ArgumentTypeError: when string does not contain end

    :returns: end
    :rtype: str
    """
    return match_start(end)


def search_datetime(line, keywords=tuple()):
    """Search datetime strings.

    :param str line: line
    :param tuple keywords: keywords

    :returns: datetime strings
    :rtype: list
    """
    pattern = re.compile(
        (r"([0-9]{4}(?:-[0-9]{2}){2}(?:\s[0-9]{2}:[0-9]{2})?" fr"{'|'.join(keywords)})")
    )
    scanner = pattern.scanner(line)
    while True:
        match = scanner.search()
        if match:
            yield match.span()
        else:
            break


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
