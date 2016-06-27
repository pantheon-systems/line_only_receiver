#!/bin/bash
###
# This bash function is designed to capture and evaluate the exit
# value of pylint such that it can be run in full evaluation mode
# testing for lower order refactorings and convention message types
# but yield a zero exit value so that circleci will pass the lint
# tests as long as there are no fatals, errors or warnings detected.
#
# From the docs in `pylint --long-help`
# 
# Pylint exits with following status codes:
#   0 if everything went fine
#   1 if a fatal message was issued
#   2 if an error message was issued
#   4 if a warning message was issued
#   8 if a refactor message was issued
#   16 if a convention message was issued
#   32 on usage error
# status 1 to 16 will be bit-ORed so you can know which different
# categories have been issued by analysing pylint output status code
###

FATAL=1
ERROR=2
WARN=4
REFACTOR=8
CONVENTION=16
USAGE=32

# run pylint on the modules given in arguments and capture the exit val
pylint $@
status=$?

## See them all evaluated live here
# echo "Pylint Status : $status (Greater than Zero indicates a linting issue)"
# echo "FATAL      > 0: $(($status & $FATAL))"
# echo "ERROR      > 0: $(($status & $ERROR))"
# echo "WARN       > 0: $(($status & $WARN))"
# echo "REFACTOR   > 0: $(($status & $REFACTOR))"
# echo "CONVENTION > 0: $(($status & $CONVENTION))"
# echo

# These conditionals detect if any of the logic failure bit flags are set in the pylint exit status
if (( $FATAL == ($status & $FATAL) || $ERROR == ($status & $ERROR) || $WARN == ($status & $WARN) )); then
	echo "[FAIL] Pylint detected some problematic issues with this code."
	exit ${status}  # Unsafe to proceed. Exit with the original status.
fi

# These conditionals detect if any of the style bit flags are set in the pylint exit status
if (( $REFACTOR == ($status & $REFACTOR) || $CONVENTION == ($status & $CONVENTION) )); then
	echo "[WARN] Pylint detected some minor issues with this code."
	exit 0  # Allow these kinds of issues. Exit OK.
fi

if (( $USAGE == ($status & $USAGE) )); then
	echo "[ERROR] There was a problem executing pylint. Check your pylintrc and command arguments."
	exit ${status}  # Just bad. Exit with the original status.
fi

# otherwise return success
echo "[SUCCESS] This is beautiful Python. Nice job!"
exit ${status}  # Golden. Exit with the original status FTW.
