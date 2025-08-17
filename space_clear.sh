#!/bin/bash

# This script finds all .py files in the current directory and its subdirectories.
# It then uses `sed` to remove any trailing whitespace from each line.
# The `-i` flag for `sed` performs an in-place edit, so the original file is modified.
# The `find` command is used for recursive file discovery.

# The `-name "*.py"` flag finds all files ending with .py.
# The `-type f` flag ensures we only operate on files, not directories.
# The `-exec` flag executes the following command on each found file.
# The `{}` is a placeholder for the current file path.
# The `\;` marks the end of the `-exec` command.

# Explanation of the `sed` command:
# `s/`  - Start of the substitution command.
# `[[:space:]]*$` - This is the regular expression to search for.
#    `[[:space:]]` - Matches any whitespace character (space, tab, etc.).
#    `*` - Matches the preceding character (`[[:space:]]`) zero or more times.
#    `$` - Matches the end of the line.
#    So, `[[:space:]]*$` finds any number of whitespace characters at the end of a line.
# `//` - The replacement string is empty, so the found whitespace is deleted.
# `-i` - The in-place edit flag, which modifies the file directly.
#      Note: On some systems, especially macOS, you might need to use `sed -i ''` (with an empty string).
#      However, `sed -i` is the standard for GNU/Linux (Debian, etc.), so this script is correct for your system.

find . -name "*.py" -type f -exec sed -i 's/[[:space:]]*$//' {} \;

echo "Successfully removed trailing whitespace from all .py files."

