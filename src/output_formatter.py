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
:synopsis: Output formatter.
"""


# standard library imports
# third party imports
# library specific imports
from src.colour import FGColours


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
        if not any(tags):
            return ""
        elif colour:
            return "".join(
                f"{self.DEFAULT}{FGColours.DARK_GRAY}[{tag}]{self.DEFAULT}"
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
        else:
            start = start.strftime("%H:%M")
            end = end.strftime("%H:%M")
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
