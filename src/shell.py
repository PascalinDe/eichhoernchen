#    This file is part of Eichhörnchen 1.0.
#    Copyright (C) 2018  Carine Dengler
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
:synopsis: Eichhörnchen shell.
"""


# standard library imports
import cmd
import readline

# third party imports
# library specific imports
import src.timing


class TaskShell(cmd.Cmd):
    """Task shell.

    :ivar Timer timer: timer
    """

    def __init__(self):
        """Initialize task shell."""
        super().__init__()
        self.intro = "Task shell.\t Type help or ? to list commands.\n"
        self.timer = src.timing.Timer("eichhoernchen.db")
        self._reset_prompt()
        return

    def _reset_prompt(self):
        """Reset prompt."""
        if self.timer.current_task.name:
            self.prompt = f"{self.timer.current_task.name} ~> "
        else:
            self.prompt = "~> "

    def do_start(self, args):
        """Start task."""
        try:
            self.timer.start(args)
        except RuntimeError as exception:
            stop = ""
            while stop not in ["y", "n"]:
                stop = input("replace running task [yn]? ").lower()
            if stop == "y":
                self.timer.stop()
                self.timer.start(args)
        self._reset_prompt()

    def do_stop(self, args):
        """Stop task."""
        if self.timer.current_task.name:
            self.timer.stop()
            self._reset_prompt()
        else:
            print("no current task")

    def do_show(self, args):
        """Show current task."""
        print(self.timer.show())

    def do_list(self, args):
        """List tasks."""
        print(self.timer.list())

    def do_bye(self, args):
        """Close task shell."""
        if self.timer.current_task.name:
            self.timer.stop()
        return True
