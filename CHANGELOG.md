# [2.1] ()
## Migrations
* configuration file
	* "DEFAULT" section has been dropped
	* keys in "DEFAULT" section ("database", "path") have been moved to "database" section
	* "database" key has been renamed to "dbname"

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
