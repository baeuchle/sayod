#!/bin/bash

if [ -z "$nonotify" ]; then
    if ! which notify-send >/dev/null; then
        echo "Kann notify-send nicht finden, bitte installieren" >&2
        exit 127
    fi
    # make sure notify-send works from cronjob
    if [ -z "$XDG_RUNTIME_DIR" ]; then
        export XDG_RUNTIME_DIR=/run/user/$(id -u)
    fi
else
    # if notify-send shouldn't be used, just mute it.
    function notify-send {
        true
    }
fi

function verbose_echo {
    if [ -z "$verbose" ]; then
        return
    fi
    echo -e "$(sed 's/\\n/\n/g' <<<$* | fold -w 72 -s)"
}

function one_line {
    awk 1 ORS='\\n' "$1";
}

