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
:synopsis: Command-line interpreters.
"""


# standard library imports
import json
import curses
import datetime

from pathlib import Path

# third party imports
# library specific imports
import src.timer

from src import FullName, Task
from src.interpreter import (
    convert_to_date_string,
    generate_stats,
    InterpreterMixin,
    match_end,
    match_from,
    match_full_name,
    match_name,
    match_start,
    match_summand,
    match_tags,
    match_to,
    NoSuchTask,
    UserAbort,
)
from src.output_formatting import (
    pprint_error,
    pprint_full_name,
    pprint_info,
    pprint_sum,
    pprint_task,
)
from src.curses.subwindows_menus import draw_input_box, draw_menu, draw_stats_window


class Interpreter(InterpreterMixin):
    """Main command-line interpreter."""

    ARGS = {
        "full_name": {
            "type": match_full_name,
            "help": "name followed by 0 or more tags, e.g. 'foo[bar]'",
            "metavar": "full name",
        },
        "from_": {
            "type": match_from,
            "help": "date (e.g. '@2021-12-19') or keyword (e.g. '@month')",
            "metavar": "from",
        },
        "to": {
            "type": match_to,
            "help": "date (e.g. '@2021-12-19') or keyword (e.g. '@month')",
        },
        "start": {
            "type": match_start,
            "help": "time (e.g. '@18:35') or date and time (e.g. '@2021-12-19 18:35')",
        },
        "end": {
            "type": match_end,
            "help": "time (e.g. '@18:35') or date and time (e.g. '@2021-12-19 18:35')",
        },
    }
    SEP = ("@",)

    def __init__(self, config):
        """Initialize main command-line interpreter.

        :param dict config: configuration
        """
        self.config = config
        self.timer = src.timer.Timer(
            str(Path(config["database"]["path"]) / Path(config["database"]["dbname"]))
        )
        self.aliases = (
            {k: json.loads(v) for k, v in config["aliases"].items()}
            if "aliases" in config
            else {}
        )
        self.subcommands = {
            "start": {
                "description": "start task",
                "aliases": self.aliases.get("start", tuple()),
                "func": self.start,
                "args": {"full_name": self.ARGS["full_name"]},
            },
            "stop": {
                "description": "stop task",
                "aliases": self.aliases.get("stop", tuple()),
                "func": self.stop,
                "args": {},
            },
            "add": {
                "description": "add task",
                "aliases": self.aliases.get("add", tuple()),
                "func": self.add,
                "args": {k: self.ARGS[k] for k in ("full_name", "start", "end")},
            },
            "remove": {
                "description": "remove task",
                "aliases": self.aliases.get("remove", tuple()),
                "func": self.remove,
                "args": {
                    "full_name": self.ARGS["full_name"],
                    **{
                        k: {
                            **self.ARGS[k],
                            **{"nargs": "?", "default": "@today"},
                        }
                        for k in ("from_", "to")
                    },
                },
            },
            "edit": {
                "description": "edit task",
                "aliases": self.aliases.get("edit", tuple()),
                "func": self.edit,
                "args": {
                    "full_name": self.ARGS["full_name"],
                    **{
                        k: {
                            **self.ARGS[k],
                            **{"nargs": "?", "default": "@today"},
                        }
                        for k in ("from_", "to")
                    },
                },
            },
            "list": {
                "description": "list tasks",
                "aliases": self.aliases.get("list", tuple()),
                "func": self.list,
                "args": {
                    "full_name": {
                        **self.ARGS["full_name"],
                        **{"nargs": "?", "default": FullName("", frozenset())},
                    },
                    **{
                        k: {
                            **self.ARGS[k],
                            **{"nargs": "?", "default": "@today"},
                        }
                        for k in ("from_", "to")
                    },
                },
            },
            "clean_up": {
                "description": "list buggy tasks",
                "aliases": self.aliases.get("clean_up", tuple()),
                "func": self.list_buggy_tasks,
                "args": {},
            },
            "sum": {
                "description": "sum runtimes up",
                "aliases": self.aliases.get("sum", tuple()),
                "func": self.sum,
                "args": {
                    "summand": {
                        "type": match_summand,
                        "help": "full name, name or tag(s) (e.g. '[foo][bar]')",
                    },
                    **{
                        k: {
                            **self.ARGS[k],
                            **{"nargs": "?", "default": "@today"},
                        }
                        for k in ("from_", "to")
                    },
                },
            },
            "export": {
                "description": "export tasks",
                "aliases": self.aliases.get("export", tuple()),
                "func": self.export,
                "args": {
                    "ext": {"choices": ("csv", "json"), "metavar": "format"},
                    "full_name": {
                        **self.ARGS["full_name"],
                        **{"nargs": "?", "default": FullName("", frozenset())},
                    },
                    **{
                        k: {
                            **self.ARGS[k],
                            **{"nargs": "?", "default": "@today"},
                        }
                        for k in ("from_", "to")
                    },
                },
            },
            "show_stats": {
                "description": "show statistics",
                "aliases": self.aliases.get("show_stats", tuple()),
                "func": self.show_statistics,
                "args": {
                    **{
                        k: {
                            **self.ARGS[k],
                            **{"nargs": "?", "default": "@today"},
                        }
                        for k in ("from_", "to")
                    },
                },
            },
        }
        super().__init__()
        self._init_parser()

    def _pick_task(
        self,
        full_name=FullName("", frozenset()),
        start="today",
        end="today",
        include_running=True,
    ):
        """Pick task.

        :param FullName full_name: full name
        :param str start: start of time period
        :param str end: end of time period
        :param bool include_running: toggle including current tasks on/off

        :returns: task and pretty-printed task
        :rtype: tuple
        """
        tasks = self.timer.list(
            convert_to_date_string(start),
            convert_to_date_string(end),
            full_name=full_name,
            include_running=include_running,
        )
        if not tasks:
            raise NoSuchTask(
                f"'{''.join(p for p, _ in pprint_full_name(full_name))}' does not exist"
            )
        items = tuple("".join(p for p, _ in pprint_task(task)) for task in tasks)
        i = draw_menu(items, banner=f"Pick menu item 1...{len(items)}.")
        if i < 0:
            raise UserAbort("user abort")
        return tasks[i], items[i]

    def start(self, full_name=FullName("", frozenset())):
        """Start task.

        :param FullName full_name: full name

        :returns: output
        :rtype: tuple
        """
        if self.timer.task.name:
            return (pprint_error("another task is already running"),)
        self.timer.start(Task(full_name.name, full_name.tags, (None, None)))
        return tuple()

    def stop(self):
        """Stop task.

        :returns: output
        :rtype: tuple
        """
        if self.timer.task.name:
            self.timer.stop()
            return tuple()
        return (pprint_error("no task is currently running"),)

    def add(self, full_name=FullName("", frozenset()), start="", end=""):
        """Add task.

        :param FullName full_name: full name
        :param str start: start of time period
        :param str end: end of time period

        :returns: output
        :rtype: tuple
        """
        try:
            start = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M")
            task = Task(
                *full_name,
                (
                    start,
                    datetime.datetime.strptime(
                        end,
                        "%Y-%m-%d %H:%M",
                    ),
                ),
            )
            self.timer.add(task)
            return (
                pprint_task(
                    task, date=(start.date() != datetime.datetime.today().date())
                ),
            )
        except ValueError as exception:
            return (pprint_error(str(exception)),)

    def remove(self, full_name=FullName("", frozenset()), from_="today", to="today"):
        """Remove task.

        :param FullName full_name: full name
        :param str from_: start of time period
        :param str to: end of time period

        :returns: output
        :rtype: tuple
        """
        try:
            task, pprinted_task = self._pick_task(
                full_name=full_name,
                start=from_,
                end=to,
                include_running=False,
            )
        except Exception as exception:
            return (pprint_error(str(exception)),)
        try:
            self.timer.remove(task)
        except ValueError as exception:
            return (pprint_error(str(exception)),)
        return (pprint_info(f"removed '{pprinted_task}'"),)

    def edit(self, full_name=FullName("", frozenset()), from_="today", to="today"):
        """Edit task.

        :param FullName full_name: full name
        :param str from_: start of time period
        :param str to: end of time period

        :returns: output
        :rtype: tuple
        """
        try:
            task, pprinted_task = self._pick_task(
                full_name=full_name, start=from_, end=to
            )
        except Exception as exception:
            return (pprint_error(str(exception)),)
        if not task:
            return (pprint_error(f"'{pprinted_task}' does not exist"),)
        attributes = ("name", "tags", "start", "end")
        i = draw_menu(
            attributes,
            banner=f"Pick attribute 1...{len(attributes)} to edit.",
        )
        if i < 0:
            return (pprint_error("user abort"),)
        try:
            new = (match_name, match_tags, match_from, match_to)[i](
                draw_input_box(
                    banner=f"New {attributes[i]}",
                    prompt=((">", curses.color_pair(0)),),
                )
            )
        except EOFError:
            return (pprint_error("user abort"),)
        if attributes[i] in ("start", "end"):
            new = datetime.datetime.strptime(new, "%Y-%m-%d %H:%M")
        try:
            task = self.timer.edit(task, attributes[i], new)
            return (
                pprint_task(
                    task,
                    date=(task.time_span[0].date() != datetime.datetime.today().date()),
                ),
            )
        except ValueError as exception:
            return (pprint_error(exception),)

    def list(self, full_name=FullName("", frozenset()), from_="today", to="today"):
        """List tasks.

        :param FullName full_name: full name
        :param str from_: start of time period
        :param str end: end of time period

        :returns: output
        :rtype: tuple
        """
        return tuple(
            pprint_task(
                task,
                date=from_ not in ("today", convert_to_date_string("today")),
            )
            for task in self.timer.list(
                convert_to_date_string(from_),
                convert_to_date_string(to),
                full_name=full_name,
                match_full_name=any(full_name),
            )
        )

    def list_buggy_tasks(self):
        """List buggy tasks.

        :returns: output
        :rtype: tuple
        """
        return tuple(
            pprint_task(task, date=True) for task in self.timer.list_buggy_tasks()
        )

    def sum(self, summand=FullName("", frozenset()), from_="today", to="today"):
        """Sum up runtimes.

        :param FullName summand: full name
        :param str from_: start of time period
        :param str to: end of time period

        :returns: output
        :rtype: tuple
        """
        return tuple(
            pprint_sum(FullName(*full_name), runtime)
            for full_name, runtime in self.timer.sum(
                convert_to_date_string(from_),
                convert_to_date_string(to),
                full_name=summand,
                match_full_name=all(summand),
            )
        )

    def export(
        self, ext="", full_name=FullName("", frozenset()), from_="today", to="today"
    ):
        """Export tasks.

        :param str ext: file extension
        :param FullName full_name: full name
        :param str from_: start of time period
        :param str to: end of time period

        :returns: output
        :rtype: tuple
        """
        filename = self.timer.export(
            ext,
            convert_to_date_string(from_),
            convert_to_date_string(to),
            full_name=full_name,
        )
        return (pprint_info(f"exported tasks to {filename}"),)

    def show_statistics(self, from_="today", to="today"):
        """Show statistics.

        :param str from_: start of time period
        :param str to: end of time period

        :returns: output
        :rtype: tuple
        """
        draw_stats_window(
            generate_stats(
                self.timer,
                convert_to_date_string(from_),
                convert_to_date_string(to),
            ),
            StatsInterpreter(self.config, from_, to),
        )
        return tuple()


class StatsInterpreter(InterpreterMixin):
    """Statistics command-line interpreter."""

    def __init__(self, config, from_, to):
        """Initialize command-line interpreter.

        :param dict config: configuration
        :param str from_: start of time period
        :param str to: end of time period
        """
        self.new_loop = True
        self.timer = src.timer.Timer(
            str(Path(config["database"]["path"]) / Path(config["database"]["dbname"]))
        )
        self.from_ = datetime.datetime.strptime(
            convert_to_date_string(from_), "%Y-%m-%d"
        )
        self.to = datetime.datetime.strptime(convert_to_date_string(to), "%Y-%m-%d")
        self.aliases = (
            {k: json.loads(v) for k, v in config["aliases"].items()}
            if "aliases" in config
            else {}
        )
        self.subcommands = {
            "next": {
                "description": "show next day",
                "aliases": (">", *self.aliases.get("next", tuple())),
                "func": self.next,
                "args": {},
            },
            "previous": {
                "description": "show previous day",
                "aliases": ("<", *self.aliases.get("previous", tuple())),
                "func": self.previous,
                "args": {},
            },
        }
        super().__init__()
        self._init_parser()

    def _show_stats(self):
        """Show statistics."""
        draw_stats_window(
            generate_stats(
                self.timer,
                self.from_.strftime("%Y-%m-%d"),
                self.to.strftime("%Y-%m-%d"),
            ),
            self,
            new_loop=self.new_loop,
        )

    def next(self):
        """Show next day.

        :returns: output
        :rtype: tuple
        """
        self.new_loop = False
        self.from_ = self.from_ + datetime.timedelta(days=1)
        self.to = self.to + datetime.timedelta(days=1)
        self._show_stats()
        return tuple()

    def previous(self):
        """Show previous day.

        :returns: output
        :rtype: tuple
        """
        self.new_loop = False
        self.from_ = self.from_ - datetime.timedelta(days=1)
        self.to = self.to - datetime.timedelta(days=1)
        self._show_stats()
        return tuple()
