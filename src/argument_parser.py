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
import collections

# third party imports
# library specific imports


FullName = collections.namedtuple(
    "FullName", ("name", "tags")
)
FullName.__new__.__defaults__ = ("", [])
KeyWord = collections.namedtuple(
    "KeyWord", ("full_name", "from_", "to", "summand")
)
KeyWord.__new__.__defaults__ = (True, False, False, False)
Args = collections.namedtuple(
    "Args", ("full_name", "from_", "to", "summand")
)
Args.__new__.__defaults__ = (FullName(), "today", "today", "full_name")


class ArgumentParser():
    """Argument parser.

    :cvar Pattern NAME_PATTERN: regular expression matching name
    :cvar Pattern TAG_PATTERN: regular expression matching tag
    :cvar Pattern FULL_NAME_PATTERN: regular expression matching full name
    :cvar Pattern ISODATE_PATTERN: regular expression matching ISO 8601 date
    :cvar list TIME_PERIOD: list of time periods
    :cvar Pattern TIME_PERIOD_PATTERN: regular expression matching time period
    :cvar Pattern FROM_PATTERN: regular expression matching from ...
    :cvar Pattern TO_PATTERN: regular expression matching ... to
    :cvar Pattern SUMMAND_PATTERN: regular expression matching summand
    """
    NAME_PATTERN = re.compile(r"(?:\w|\s)+")
    TAG_PATTERN = re.compile(r"\[((?:\w|\s)+)\]")
    FULL_NAME_PATTERN = re.compile(
        fr"(?:{TAG_PATTERN.pattern})*(?:{NAME_PATTERN.pattern})"
        fr"(?:{TAG_PATTERN.pattern})*"
    )
    ISODATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
    TIME_PERIOD = ("all", "year", "month", "week", "yesterday", "today")
    TIME_PERIOD_PATTERN = re.compile(fr"{'|'.join(TIME_PERIOD)}")
    FROM_PATTERN = re.compile(
        fr"{ISODATE_PATTERN.pattern}|{TIME_PERIOD_PATTERN.pattern}"
    )
    TO_PATTERN = re.compile(
        fr"{ISODATE_PATTERN.pattern}|{'|'.join(TIME_PERIOD[1:])}"
    )
    SUMMAND_PATTERN = re.compile(r"full name|name|tag")

    def parse_args(self, args, key_word):
        """Parse command-line arguments.

        :param str args: command-line arguments
        :param KeyWord key_word: list of key words

        :returns: command-line arguments
        :rtype: Args
        """
        if key_word.full_name:
            full_name_match = self.FULL_NAME_PATTERN.match(args)
            if full_name_match:
                name = self.TAG_PATTERN.sub("", args)
                tags = self.TAG_PATTERN.findall(args)
                parsed_args = Args(full_name=FullName(name=name, tags=tags))
            else:
                raise ValueError("required argument 'full_name' is missing")
        elif any((key_word.from_, key_word.to, key_word.summand)):
            parsed_args = Args()
            if key_word.from_:
                from_match = self.FROM_PATTERN.match(args)
                if from_match:
                    parsed_args = parsed_args._replace(
                        from_=from_match.group(0)
                    )
                    args = self.FROM_PATTERN.sub("", args, count=1).strip()
                    if key_word.to:
                        to_match = self.TO_PATTERN.match(args)
                        if to_match:
                            parsed_args = parsed_args._replace(
                                to=to_match.group(0)
                            )
                            args = self.TO_PATTERN.sub(
                                "", args, count=1
                            ).strip()
            if key_word.summand:
                summand_match = self.SUMMAND_PATTERN.match(args)
                if summand_match:
                    parsed_args = parsed_args._replace(
                        summand=summand_match.group(0)
                    )
        return parsed_args
