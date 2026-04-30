#!/bin/bash

PHASE=$1
FEATURE=$2
TASK=$3

# Check if arguments are missing
if [ -z "$PHASE" ] || [ -z "$FEATURE" ] || [ -z "$TASK" ]; then
    echo "Usage: ./next-task-git-scratch.sh <PHASE> <FEATURE> <TASK>"
    exit 1
fi

BASE_BRANCH="$PHASE/$FEATURE/main"
NEXT_BRANCH="$PHASE/$FEATURE/$TASK"

git checkout "$BASE_BRANCH"
git pull
git checkout -b "$NEXT_BRANCH"

echo "Pulled changes into $BASE_BRANCH and checked out $NEXT_BRANCH"
