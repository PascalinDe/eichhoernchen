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
:synopsis: Output formatter.
"""


# standard library imports
# third party imports
# library specific imports
from src import FullName, Task
from src.template import Template

TEMPLATE = Template()


def pprint_name(name):
    """Pretty-print name.

    :param str name: name

    :returns: pretty-printed name
    :rtype: tuple
    """
    return ((TEMPLATE.name[0].format(name=name), TEMPLATE.name[1]),)


def pprint_tags(tags):
    """Pretty-print tags.

    :param list tags: tags

    :returns: pretty-printed tags
    :rtype: tuple
    """
    return (
        (
            "".join(TEMPLATE.tag[0].format(tag=tag) for tag in sorted(tags) if tag),
            TEMPLATE.tag[1],
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
    :param bool date: toggle displaying date on/off

    :returns: time span
    :rtype: tuple
    """
    if date:
        if time_span[0].date() != time_span[1].date():
            start = time_span[0].strftime("%Y-%m-%d %H:%M")
        else:
            start = time_span[0].strftime("%H:%M")
        end = time_span[1].strftime("%H:%M %Y-%m-%d")
    else:
        start = time_span[0].strftime("%H:%M")
        end = time_span[1].strftime("%H:%M")
    return (
        (TEMPLATE.time_span[0].format(start=start, end=end), TEMPLATE.time_span[1]),
    )


def pprint_total(total):
    """Pretty-print total runtime.

    :param int total: runtime (in seconds)

    :returns: pretty-printed runtime
    :rtype: tuple
    """
    hours, minutes = divmod(divmod(total, 60)[0], 60)
    return (
        (TEMPLATE.total[0].format(hours=hours, minutes=minutes), TEMPLATE.total[1]),
    )


def pprint_task(task, date=False):
    """Pretty-print task.

    :param Task task: task
    :param bool date: toggle displaying date on/off

    :returns: pretty-printed task
    :rtype: tuple
    """
    return (
        *pprint_time_span(task.time_span, date=date),
        *pprint_total(task.total),
        *pprint_full_name(FullName(task.name, task.tags)),
    )


def pprint_sum(full_name, total):
    """Pretty-print sum of total runtime.

    :param FullName full_name: full name
    :param int total: runtime (in seconds)

    :returns: pretty-printed runtime
    :rtype: tuple
    """
    return (*pprint_full_name(full_name), *pprint_total(total))


def pprint_running(task):
    """Pretty-print currently running task.

    :param Task task: task

    :returns: pretty-printed currently running task
    :rtype: tuple
    """
    start = task.time_span[0].strftime("%H:%M")
    return ((TEMPLATE.running[0].format(start=start), TEMPLATE.running[1]),)


def pprint_prompt(task=Task("", frozenset(), ())):
    """Pretty-print prompt.

    :param Task task: task

    :returns: pretty-printed prompt
    :rtype: tuple
    """
    if task.name:
        return (
            *pprint_full_name(FullName(task.name, task.tags)),
            *pprint_running(task),
            TEMPLATE.prompt,
        )
    return (TEMPLATE.prompt,)


def pprint_info(info):
    """Pretty-print info.

    :param str info: info

    :returns: pretty-printed info
    :rtype: tuple
    """
    return ((TEMPLATE.info[0].format(info=info), TEMPLATE.info[1]),)


def pprint_error(error):
    """Pretty-print error.

    :param str error: error

    :returns: pretty-printed error
    :rtype: tuple
    """
    return ((TEMPLATE.error[0].format(error=error), TEMPLATE.error[1]),)
