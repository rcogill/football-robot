#!/bin/bash
#
# Starting script for measuring pylint scores
# Look here: https://medium.com/@ryangordon210/build-a-python-ci-cd-system-code-quality-with-pylint-f6dea78461c6
#

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

status=0

find ./ -iname "*.py" |
while read line; do
    score=$(pylint $line | grep -oE "rated at [0-9]+\.[0-9]+/" | grep -oE "[0-9]+\.[0-9]+")
    if (( $(echo "$score >= 8.0" | bc -l) ))
        then
            echo -e "${GREEN}[PASS]${NC} $line score: $score"
        else
            echo -e "${RED}[FAIL]${NC} $line score: $score"
            status=1
    fi
done

exit $status
