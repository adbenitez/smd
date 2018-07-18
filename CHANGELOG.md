# Changelog

## 1.5.0

Released 18/07/2018
* **New:** Added new option `-d`/`--directory` to set the place where to save the manga folder (default: working directory).
* **Fix:** If the manga title or chapter title are an invalid folder name, ask the user for a new name instead of crashing.
* **New:** Removed `--start` and `--stop` options in favor of a more powerful `--chapters` option. Now use `--chapters 10:20` instead of `--start 10 --stop 20`.
* **New:** Log file now moved to `[USER HOME]/smd/smd.log` and log size limited.
* **New:** Now exception traces are sent only to log file and small messages to console.
* **New:** Added `--verbose` option to make the program print debug messages and error stack traces.
* **Fix:** On ConnectionResetError retry only a fixed number of times.
* **New:** Added `tests` module for unit testing.

## Sorry, changes to previous versions were not tracked...
