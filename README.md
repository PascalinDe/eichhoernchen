# Eichhörnchen
[![](https://github.com/PascalinDe/eichhoernchen/workflows/Python%20package/badge.svg)](https://github.com/PascalinDe/eichhoernchen/actions/runs/)
[![](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Lightweight curses-based time tracking tool.

![Eichhörnchen](/screenshots/eichhoernchen-intro.png?raw=true)

## Table of contents

1. [Table of contents](#table-of-contents)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)

## Features

* start and stop tasks
* add new tasks
* edit or remove existing tasks
* list tasks
* sum up run times
* show summary
* export tasks to CSV or JSON

Also,

* curses-based user interface
* standard library only

## Installation

To install Eichhörnchen using ``pip`` run the following command:

```bash
pip install eichhoernchen
```

## Configuration

The default location of the configuration file is
``~/.config/eichhoernchen.ini``. An alternate configuration
file can be specified using the ``-c, --config`` argument.

### Minimal configuration

The configuration file is an INI file and has to contain
at least the following section:

```ini
[database]
dbname = eichhoernchen.db
path = /home/user/.local/share
```

The ``dbname`` specifies the name of the SQLite3 database, and
``path`` its path.

### Aliases

To define aliases for the commands, add the ``aliases`` section
to define one or more aliases per command:

```ini
[aliases]
list = ["ls"]
remove = ["rm", "rem"]
```

## Usage

```bash
usage: eichhoernchen [-h] [-c CONFIG] [--version]

Lightweight curses-based time tracking tool.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        use this configuration file
  --version             show program's version number and exit
```

When inside the program use the ``help`` or ``?`` commands to list
available commands or ``help command`` to show the command's
help message.

Use Control+D to close windows and abort operations. Control+C will
exit the program.
