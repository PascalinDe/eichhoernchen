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
:synopsis: Output formatter.
"""


# standard library imports
# third party imports
# library specific imports


class FGColours():
    """
    Black       0;30     Dark Gray     1;30
    Blue        0;34     Light Blue    1;34
    Green       0;32     Light Green   1;32
    Cyan        0;36     Light Cyan    1;36
    Red         0;31     Light Red     1;31
    Purple      0;35     Light Purple  1;35
    Brown       0;33     Yellow        1;33
    Light Gray  0;37     White         1;37

    Refer to
    `Colours<http://www.tldp.org/HOWTO/Bash-Prompt-HOWTO/x329.html>`_ for
    additional information.
    """
    BLACK = "\033[0;31m"
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    CYAN = "\033[0;36m"
    RED = "\033[0;31m"
    PURPLE = "\033[0;35m"
    BROWN = "\033[0;33m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_GREEN = "\033[1;32m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_PURPLE = "\033[1;35m"
    YELLOW = "\033[1;33m"
    WHITE = "\033[1;37m"


class BGColours():
    """Background colours."""
    BLACK = "\033[41m"
    BLUE = "\033[44m"
    GREEN = "\033[42m"
    CYAN = "\033[46m"
    RED = "\033[41m"
    PURPLE = "\033[45m"
    BROWN = "\033[43m"
    LIGHT_GRAY = "\033[47m"


class OutputFormatter():
    """Output formatter."""
    DEFAULT = "\033[0m"

    def pprint_name(self, name, colour=False):
        """Pretty-print name.

        :param str name: name
        :param bool colour: toggle coloured display on/off

        :returns: pretty-printed name
        :rtype: str
        """
        if colour:
            return f"{FGColours.GREEN}{name}{self.DEFAULT}"
        else:
            return name

    def pprint_tags(self, tags, colour=False):
        """Pretty-print tags.

        :param list tags: tags
        :param bool colour: toggle coloured display on/off

        :returns: pretty-printed tags
        :rtype: str
        """
        if colour:
            return "".join(
                f"{self.DEFAULT}[{FGColours.DARK_GRAY}{tag}{self.DEFAULT}]"
                for tag in tags
            )
        else:
            return "".join(f"[{tag}]" for tag in tags)

    def pprint_full_name(self, name, tags, colour=False):
        """Pretty-print full name.

        :param str name: name
        :param list tags: tags
        :param bool colour: toggle coloured display on/off
        """
        name = self.pprint_name(name, colour=colour)
        tags = self.pprint_tags(tags, colour=colour)
        return f"{name}{tags}"

    def pprint_time_span(self, time_span, date=False, colour=False):
        """Pretty-print time span.

        :param tuple time_span: time span
        :param bool date: toggle displaying date on/off
        :param bool colour: toggle coloured display on/off

        :returns: time span
        :rtype: str
        """
        start, end = time_span
        if date:
            if (end - start).days >= 1:
                start = start.strftime("%Y-%m-%d %H:%M")
            else:
                start = start.strftime("%H:%M")
            end = end.strftime("%H:%M %Y-%m-%d")
        if colour:
            return (
                f"{FGColours.PURPLE}{start}{self.DEFAULT}-"
                f"{FGColours.PURPLE}{end}{self.DEFAULT}"
            )
        else:
            return f"{start}-{end}"

    def pprint_total(self, total, colour=False):
        """Pretty-print representation of total runtime.

        :param int total: runtime (in seconds)

        :returns: pretty-printed representation of total runtime
        :rtype: str
        """
        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        if colour:
            return f"{FGColours.YELLOW}{hours}h{minutes}m{self.DEFAULT}"
        else:
            return f"{hours}h{minutes}m"

    def pprint_task(self, task, date=False, colour=False):
        """Pretty-print representation of task.

        :param Task task: task
        :param bool date: toggle displaying date on/off
        :param bool colour: toggle coloured display on/off

        :returns: pretty-printed representation of task
        :rtype: str
        """
        full_name = self.pprint_full_name(
            task.name, task.tags, colour=colour
        )
        time_span = self.pprint_time_span(
            task.time_span, date=date, colour=colour
        )
        total = self.pprint_total(task.total, colour=colour)
        return f"{time_span} ({total}) {full_name}"

    def pprint_sum(self, full_name, total, colour=False):
        """Pretty-print sum of total runtime.

        :param tuple full_name: full name
        :param int total: runtime (in seconds)
        :param bool colour: toggle coloured display on/off

        :returns: pretty-printed representation of total runtime
        :rtype: str
        """
        full_name = self.pprint_full_name(*full_name, colour=colour)
        total = self.pprint_total(total, colour=colour)
        return f"{full_name} {total}"

    def pprint_prompt(self, task):
        """Pretty-print prompt.

        :param Task task: task

        :returns: prompt
        :rtype: str
        """
        if task.name:
            full_name = self.pprint_full_name(
                task.name, task.tags, colour=True
            )
            start, _ = task.time_span
            start = start.strftime("%H:%M")
            return (
                f"{full_name}({FGColours.PURPLE}{start}{self.DEFAULT}-) ~> "
            )
        else:
            return "~> "
