#!/bin/bash

function verbose_echo {
    if [ -z "$verbose" ]; then
        return
    fi
    echo -e "$(sed 's/\\n/\n/g' <<<$* | fold -w 72 -s)"
}

function one_line {
    awk 1 ORS='\\n' "$1";
}

