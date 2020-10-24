# eichhoernchen
[![Build Status](https://www.travis-ci.org/PascalinDe/eichhoernchen.svg?branch=master)](https://www.travis-ci.org/PascalinDe/eichhoernchen)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Lightweight curses-based time tracking tool.

## Table of Contents

1. [Table of Contents](#table-of-contents)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Configuring Eichhörnchen](#configuring-eichhörnchen)
6. [Exporting tasks](#exporting-tasks)

## Features

* curses-based user interface
* time tracking functionality
	* starting/stopping tasks
	* adding/removing tasks
	* editing tasks
	* listing tasks
	* summing up of run time
	* summary of tasks
	* exporting tasks to CSV or JSON
* standard library only

## Installation

To install Eichhörnchen using ``pip`` run the following command:

```bash
pip install eichhoernchen
```

## Usage

```
usage: eichhoernchen [-h] [-c CONFIG] [--version]

Lightweight curses-based time tracking tool.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        use this configuration file
  --version             show program's version number and exit
```

When inside the program use the ``help`` or ``?`` commands
to list available commands or ``help command`` to show
the help message of the command ``command``.

Use Control+C to close windows displaying choices (and thus
aborting the related operation) or to exit the program.

### Configuring Eichhörnchen

The default location of the configuration file is
``~/.config/eichhoernchen.ini``. An alternate configuration
file can be specified using the ``-c``/``--config`` argument.

#### Minimum configuration

The configuration file is an INI file and needs to contain
at least the following sections:

```ini
[database]
dbname = eichhoernchen.db
path = /home/user/.local/share
```

The ``dbname`` specifies the name of the SQLite3 database, and
``path`` specifies the path to the database file.

#### Aliases

To define aliases for the standard commands, add the ``aliases``
section containing key-value pairs defining one or more aliases
per command:

```ini
[aliases]
list = ["ls"]
remove = ["rm", "rem"]
```

### Exporting tasks

The tasks in the database can be exported to either CSV or JSON
file format.

#### Exporting to CSV file format

When exporting to CSV file format, for each tag a task is
associated with an entry is created. For example, the
following list of tasks

```
~>list
21:32-21:32 2020-06-04(0h0m)foo[bar]
21:32-21:32 2020-06-04(0h0m)bar[foo]
21:32-21:32 2020-06-04(0h0m)foobar[bar][foo]
21:32-21:32 2020-06-04(0h0m)foo
21:32-21:32 2020-06-04(0h0m)bar
21:32-21:59 2020-06-04(0h27m)foobar
```

result in the following CSV file content

```
foo,bar,2020-06-04T21:32:19,2020-06-04T21:32:20
bar,foo,2020-06-04T21:32:31,2020-06-04T21:32:32
foobar,bar,2020-06-04T21:32:37,2020-06-04T21:32:39
foobar,foo,2020-06-04T21:32:37,2020-06-04T21:32:39
foo,,2020-06-04T21:32:43,2020-06-04T21:32:44
bar,,2020-06-04T21:32:45,2020-06-04T21:32:46
foobar,,2020-06-04T21:32:49,2020-06-04T21:59:38
```

To recreate the original list of tasks, the start time
of the tasks can be used as it is unique.

#### Exporting to JSON file format

When exporting to JSON file format, the original tasks' structure
is more or less preserved. For example, the following list of tasks

```
~>list
21:32-21:32 2020-06-04(0h0m)foo[bar]
21:32-21:32 2020-06-04(0h0m)bar[foo]
21:32-21:32 2020-06-04(0h0m)foobar[bar][foo]
21:32-21:32 2020-06-04(0h0m)foo
21:32-21:32 2020-06-04(0h0m)bar
21:32-21:59 2020-06-04(0h27m)foobar
```

results in the following JSON file content

```
[["foo", ["bar"], "2020-06-04T21:32:19", "2020-06-04T21:32:20"], ["bar", ["foo"], "2020-06-04T21:32:31", "2020-06-04T21:32:32"], ["foobar", ["bar", "foo"], "2020-06-04T21:32:37", "2020-06-04T21:32:39"], ["foo", [], "2020-06-04T21:32:43", "2020-06-04T21:32:44"], ["bar", [], "2020-06-04T21:32:45", "2020-06-04T21:32:46"], ["foobar", [], "2020-06-04T21:32:49", "2020-06-04T22:06:58"]]
```
