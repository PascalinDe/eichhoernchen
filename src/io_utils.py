#    This file is part of Eichhörnchen 1.0.
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
:synopsis: Input parser and output formatter.
"""


# standard library imports
import re
import collections

# third party imports
# library specific imports


KEY_WORD_LIST = (
    "all", "year", "month", "week", "yesterday", "today",   # time period
    "task", "tag"                                           # listing
)


KEY_WORD_PATTERN = re.compile(fr"{'|'.join(KEY_WORD_LIST)}")
TAG_PATTERN = re.compile(r"\[(\w+)\]")


FullName = collections.namedtuple(
    "FullName", ("name", "tags"), defaults=("", [])
)
Args = collections.namedtuple(
    "Args", ("full_name",) + KEY_WORD_LIST,
    defaults=(FullName(),) + tuple("" for _ in range(len(KEY_WORD_LIST)))
)


def _parse_full_name(args):
    """Parse full name.

    :param str args: command-line arguments

    :returns: full name
    :rtype: FullName
    """
    name = TAG_PATTERN.sub("", args)
    tags = TAG_PATTERN.findall(args)
    return FullName(name=name, tags=tags)


def parse_args(args, key_word=False):
    """Parse command-line arguments.

    :param str args: command-line arguments
    :param bool key_word: toggle searching for key words on/off

    :returns: command-line arguments
    :rtype: Args
    """
    if not key_word:
        args = Args(full_name=_parse_full_name(args))
    else:
        args = Args(
            **{match: match for match in KEY_WORD_PATTERN.findall(args)}
        )
    return args
