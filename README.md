# eichhoernchen
[![Build Status](https://www.travis-ci.org/PascalinDe/eichhoernchen.svg?branch=master)](https://www.travis-ci.org/PascalinDe/eichhoernchen)

Lightweight curses-based time tracking tool.

## Features

* curses-based user interface
* basic time tracking functionality
	* starting/stopping tasks
	* adding/removing tasks
	* editing tasks
	* listing tasks
	* summing up of run time
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
