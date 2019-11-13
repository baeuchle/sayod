#!/bin/bash

if [ "$(which notify-send)" == "" ]; then
    echo "Kann notify-send nicht finden, bitte installieren" >&2
    exit 127
fi

# make sure notify-send works from cronjob
if [ -z "$XDG_RUNTIME_DIR" ]; then
    export XDG_RUNTIME_DIR=/run/user/$(id -u)
fi
# same for zenity
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0.0
fi

function verbose_echo {
    if [ -z "$verbose" ]; then
        return
    fi
    echo -e "$(sed 's/\\n/\n/g' <<<$* | fold -w 72 -s)"
}
