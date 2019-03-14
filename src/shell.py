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
    prompt = "(task) "
    intro = "Task shell.\t Type help or ? to list commands.\n"

    def __init__(self):
        """Initialize task shell."""
        super().__init__()
        self.timer = src.timing.Timer("eichhoernchen.db")
        return

    def do_start(self, args):
        """Start task."""
        try:
            self.timer.start(args)
        except RuntimeError as exception:
            print(exception)
            stop = ""
            while stop not in ["y", "n"]:
                stop = input("stop running task [yn]? ").lower()
            if stop == "y":
                self.timer.stop()
                self.timer.start(args)

    def do_stop(self, args):
        """Stop task."""
        self.timer.stop()

    def do_show(self, args):
        """Show current task."""
        print(self.timer.show())

    def do_list(self, args):
        """List tasks."""
        print(self.timer.list())

    def do_bye(self, args):
        """Close task shell."""
        return True
