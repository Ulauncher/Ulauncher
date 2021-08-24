#!/usr/bin/env bash

#############################
# Helper script to tag a new release
#############################
tag-release() {
    # Args:
    # $1 version

    if [ -z "$1" ]; then
        echo "First argument should be the tag name"
        exit 1
    fi

    TAG=$1
    PREVIOUSTAG=$(git describe --tags --abbrev=0)
    LOG=$(git log $PREVIOUSTAG..HEAD --pretty=format:"* %s")
    # If the previous release was a pre-release, we should include the changes in that release too
    if [[ "$PREVIOUSTAG" == *-* ]]; then
        PREVIOUSLOG=$(git tag -l --format='%(contents)' $PREVIOUSTAG)
        LOG="Changes since $PREVIOUSTAG:\n$LOG\n\nChanges in $PREVIOUSTAG:\n$PREVIOUSLOG"
    fi

    # Creates the tag and opens an editor with the LOG since last tag as the annotation
    git tag -a $TAG -m "$LOG" -e
}
