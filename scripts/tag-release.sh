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

    set -f

    TAG=$1
    PREVIOUSTAG=$(git describe --tags --abbrev=0)
    LOG=$(git log $PREVIOUSTAG..HEAD --pretty=format:"* %s")
    # If the previous release was a pre-release, we should include the changes in that release too
    if [[ "$PREVIOUSTAG" == *-* ]]; then
        PREVIOUSLOG=$(git tag -l --format='%(contents)' $PREVIOUSTAG)
        LOG=$(printf "Changes since $PREVIOUSTAG:\n$LOG\n\nChanges in $PREVIOUSTAG:\n$PREVIOUSLOG")
    fi

    echo "$LOG" > /tmp/ulauncher-release-notes
    # Let us edit the log
    $EDITOR /tmp/ulauncher-release-notes
    LOG=$(cat /tmp/ulauncher-release-notes)

    # Creates the tag
    git tag -a $TAG -m "\n$LOG"

    echo "Push the new tag with 'git push' and 'git push origin $TAG' (assuming origin is the correct remote)"
}
