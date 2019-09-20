#    This file is part of Eichhörnchen 1.1.
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
:synopsis: Argument parser.
"""


# standard library imports
import re
import datetime

# third party imports
# library specific imports
from src import FullName


NAME_PATTERN = re.compile(r"(?:\w|\s[!#+-?])+")
TAG_PATTERN = re.compile(fr"\[({NAME_PATTERN.pattern})\]")
FULL_NAME_PATTERN = re.compile(
    fr"({NAME_PATTERN.pattern})(?:{TAG_PATTERN.pattern})*"
)
ISODATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
ISOTIME_PATTERN = re.compile(r"\d{2}:\d{2}")
ISO_PATTERN = re.compile(
    fr"({ISODATE_PATTERN.pattern})?\s*({ISOTIME_PATTERN.pattern})"
)
TIME_PERIOD = ("all", "year", "month", "week", "yesterday", "today")
TIME_PERIOD_PATTERN = re.compile(fr"{'|'.join(TIME_PERIOD)}")
FROM_PATTERN = re.compile(
    fr"@({ISODATE_PATTERN.pattern}|{TIME_PERIOD_PATTERN.pattern})"
)
TO_PATTERN = re.compile(
    fr"@({ISODATE_PATTERN.pattern}|{'|'.join(TIME_PERIOD[1:])})"
)
SUMMAND_PATTERN = re.compile(r"full name|name|tag")


def cast_to_datetime(args):
    """Cast command-line arguments to datetime objects.

    :param str args: command-line arguments

    :returns: list of datetime objects
    :rtype: datetime
    """
    iso_matches = ISO_PATTERN.findall(args)
    if not iso_matches:
        raise ValueError(f"{args} is not YYYY-MM-DD hh:mm format")
    datetimes = []
    for iso_match in iso_matches:
        now = iso_match[0] or datetime.datetime.now().strftime("%Y-%m-%d")
        datetimes.append(
            datetime.datetime.strptime(
                f"{now} {iso_match[1]}", "%Y-%m-%d %H:%M"
            )
        )
    return datetimes


def find_full_name(args):
    """Find full name.

    :param str args: command-line arguments

    :returns: full name and remaining command-line arguments
    :rtype: tuple
    """
    full_name_match = FULL_NAME_PATTERN.match(args)
    if full_name_match:
        name = full_name_match.group(1).strip()
        tags = set(TAG_PATTERN.findall(args))
        args = FULL_NAME_PATTERN.sub("", args, count=1).strip()
        return FullName(name=name, tags=tags), args
    return FullName("", ()), args


def find_from(args):
    """Find from ... .

    :param str args: command-line arguments

    :returns: from ... and remaining command-line arguments
    :rtype: tuple
    """
    from_match = FROM_PATTERN.match(args)
    if from_match:
        args = FROM_PATTERN.sub("", args, count=1).strip()
        return from_match.group(1).strip(), args
    return "", args


def find_to(args):
    """Find ... to.

    :param str args: command-line arguments

    :returns: ... to and remaining command-line arguments
    :rtype: tuple
    """
    to_match = TO_PATTERN.match(args)
    if to_match:
        args = TO_PATTERN.sub("", args).strip()
        return to_match.group(1), args
    return "", args


def find_summand(args):
    """Find summand.

    :param str args: command-line arguments

    :returns: summand and remaining command-line arguments
    :rtype: tuple
    """
    summand_match = SUMMAND_PATTERN.match(args)
    if summand_match:
        args = SUMMAND_PATTERN.sub("", args).strip()
        return summand_match.group(0), args
    return "", args
