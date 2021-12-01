#    This file is part of Eichhörnchen 2.2.
#    Copyright (C) 2018-2021  Carine Dengler
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
:synopsis: Output formatting.
"""


# standard library imports
import curses

# third party imports
# library specific imports
from src import FullName, Task


class Template:
    """Output formatting template."""

    @property
    def name(self):
        return ("{name}", curses.color_pair(1))

    @property
    def tag(self):
        return ("[{tag}]", curses.color_pair(2))

    @property
    def time_span(self):
        return ("{start}-{end}", curses.color_pair(3))

    @property
    def total(self):
        return ("({hours}h{minutes}m)", curses.color_pair(4))

    @property
    def running(self):
        return ("({start}-)", curses.color_pair(3))

    @property
    def prompt(self):
        return ("~>", curses.color_pair(0))

    @property
    def info(self):
        return ("{info}", curses.color_pair(4))

    @property
    def error(self):
        return ("{error}", curses.color_pair(5))


def pprint_name(name):
    """Pretty-print name.

    :param str name: name

    :returns: pretty-printed name
    :rtype: tuple
    """
    template = Template().name
    return ((template[0].format(name=name), template[1]),)


def pprint_tags(tags):
    """Pretty-print tags.

    :param list tags: tags

    :returns: pretty-printed tags
    :rtype: tuple
    """
    template = Template().tag
    return (
        (
            "".join(template[0].format(tag=tag) for tag in sorted(tags) if tag),
            template[1],
        ),
    )


def pprint_full_name(full_name):
    """Pretty-print full name.

    :param FullName full_name: full name

    :returns: pretty-printed full name
    :rtype: tuple
    """
    return pprint_name(full_name.name) + pprint_tags(full_name.tags)


def pprint_time_span(time_span, date=False):
    """Pretty-print time span.

    :param tuple time_span: time span
    :param bool date: toggle printing date on/off

    :returns: time span
    :rtype: tuple
    """
    template = Template().time_span
    if date:
        if time_span[0].date() != time_span[1].date():
            start = time_span[0].strftime("%Y-%m-%d %H:%M")
        else:
            start = time_span[0].strftime("%H:%M")
        end = time_span[1].strftime("%H:%M %Y-%m-%d")
    else:
        start = time_span[0].strftime("%H:%M")
        end = time_span[1].strftime("%H:%M")
    return ((template[0].format(start=start, end=end), template[1]),)


def pprint_total(run_time):
    """Pretty-print run time.

    :param str total: run time

    :returns: pretty-printed run time
    :rtype: str
    """
    template = Template().total
    hours, minutes = divmod(divmod(run_time, 60)[0], 60)
    return ((template[0].format(hours=hours, minutes=minutes), template[1]),)


def pprint_task(task, date=False):
    """Pretty-print task.

    :param Task task: task
    :param bool date: toggle printing date on/off

    :returns: pretty-printed task
    :rtype: tuple
    """
    return (
        *pprint_time_span(task.time_span, date=date),
        *pprint_total(task.total),
        *pprint_full_name(FullName(task.name, task.tags)),
    )


def pprint_sum(full_name, run_time):
    """Pretty-print sum of run times.

    :param FullName full_name: full name
    :param int run_time: run time (in seconds)

    :returns: pretty-printed sum of run times
    :rtype: tuple
    """
    return (*pprint_full_name(full_name), *pprint_total(run_time))


def pprint_running(task):
    """Pretty-print currently running task.

    :param Task task: task

    :returns: pretty-printed currently running task
    :rtype: tuple
    """
    template = Template().running
    start = task.time_span[0].strftime("%H:%M")
    return ((template[0].format(start=start), template[1]),)


def pprint_prompt(task=Task("", frozenset(), ())):
    """Pretty-print prompt.

    :param Task task: task

    :returns: pretty-printed prompt
    :rtype: tuple
    """
    template = Template().prompt
    if task.name:
        return (
            *pprint_full_name(FullName(task.name, task.tags)),
            *pprint_running(task),
            template,
        )
    return (template,)


def pprint_info(msg):
    """Pretty-print message with level INFO.

    :param str msg: message

    :returns: pretty-printed message
    :rtype: tuple
    """
    template = Template().info
    return ((template[0].format(info=msg), template[1]),)


def pprint_error(msg):
    """Pretty-print message with level ERROR.

    :param str msg: message

    :returns: pretty-printed message
    :rtype: tuple
    """
    template = Template().error
    return ((template[0].format(error=msg), template[1]),)
