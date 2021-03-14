# [2.2] ()
## Bug Fixes
* properly update prompt when editing running task (closes [#27](https://github.com/PascalinDe/eichhoernchen/issues/27))
* do not accept aliases for unknown commands (closes [#21](https://github.com/PascalinDe/eichhoernchen/issues/21))
* take "'" into account (closes [#20](https://github.com/PascalinDe/eichhoernchen/issues/20))
* fixed backspace (closes [#44](https://github.com/PascalinDe/eichhoernchen/issues/44) and [#45](https://github.com/PascalinDe/eichhoernchen/issues/45))
## Features
* use Ctrl+D to abort input, editing, ... (closes [#26](https://github.com/PascalinDe/eichhoernchen/issues/26))
* automatically jump to bottom on starting to type a command (closes [#6](https://github.com/PascalinDe/eichhoernchen/issues/6))
* choose tasks to export by full name (closes [#22](https://github.com/PascalinDe/eichhoernchen/issues/22))
* add `clean_up` command to show broken tasks (closes [#32](https://github.com/PascalinDe/eichhoernchen/issues/32))
* add tab completion (closes [#33](https://github.com/PascalinDe/eichhoernchen/issues/33))
* use arrow keys to navigate command history and Ctrl+Down/Ctrl+Up to scroll window (closes [#34](https://github.com/PascalinDe/eichhoernchen/issues/34))
## Miscellaneous
* include date when listing tasks from day other than today
* show error message instead of empty aliases table (closes [#19](https://github.com/PascalinDe/eichhoernchen/issues/19))
* migrated to GitHub actions
* upgraded to Python3.9
# [2.1] (2020-10-24)
## Bug Fixes
* take resizing into account (closes [#5](https://github.com/PascalinDe/eichhoernchen/issues/5))
* fixed inserting non-ASCII characters (closes [#14](https://github.com/PascalinDe/eichhoernchen/issues/14))
* fixed displaying multi-part lines longer than window (closes [#15](https://github.com/PascalinDe/eichhoernchen/issues/15))
* Control+C aborts editing task in editing window as well (closes [#13](https://github.com/PascalinDe/eichhoernchen/issues/13))
* trying to edit non-existing task displays error message (closes [#12](https://github.com/PascalinDe/eichhoernchen/issues/12))
* fixed editing tags of running task (closes [#11](https://github.com/PascalinDe/eichhoernchen/issues/11))
## Features
* sum up by specific full name, name or tag(s) instead of summing up and listing all of them
* added command aliases
* export tasks to CSV or JSON files
* show summary of tasks
## Migrations
* configuration file
	* "DEFAULT" section has been dropped
	* keys in "DEFAULT" section ("database", "path") have been moved to "database" section
	* "database" key has been renamed to "dbname"
## Miscellaneous
* dropped support for < Python3.7
* used [black](https://github.com/psf/black) for code formatting

# [2.0] (2020-05-28)
## Bug Fixes
* replaced Pylint with Flake8
## Features
* curses-based user interface
* pip-installable
* replaced ``bye`` command to exit program with Control+C
* dropped configurable colour scheme
* dropped template

# [1.2] (2019-10-07)
## Bug Fixes
* common punctuation characters are allowed in task names and tags (closes [#2](https://github.com/PascalinDe/eichhoernchen/issues/2))
## Features
* listing tasks having given full name
* editing task functionality
* adding/removing task functionality
* configuration file support
* basic colour scheme and template

# [1.1] (2019-07-15)
## Bug Fixes
* active task is listed only once if it has more than one tag (closes [#1](https://github.com/PascalinDe/eichhoernchen/issues/1))
## Features
* defining time period using start date and end date
* summing up of run time
* coloured display

# [1.0] (2019-05-28)
## Features
* basic time tracking
* tags
