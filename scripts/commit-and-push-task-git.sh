#!/bin/bash

TASK=$1

# Check if arguments are missing
if [ -z "$TASK" ]; then
    echo "Usage: ./commit-and-push-task-git-scratch.sh <TASK>"
    exit 1
fi

git add -A
git commit -m "TASK complete and tested"
git push -u origin HEAD

