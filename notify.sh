#!/bin/bash

function get_timeout {
    local _key="$1"
    local _default="$2"
    if [ -z "$_default" ]; then
        _default=10000
    fi
    local _global_timeout=$($config --section notify --key timeout --default $_default)
    $config --section timeout --key $_key --default $_global_timeout
}

function notify {
    local _msgdate="$(date +%Y-%m-%dT%H:%M:%S)"
    local _msg=""
    local _level=$1
    local _timeout=1000
    shift
    case "$_level" in
        ABORT)
            subject="ABORT"
            urgency="normal"
            head="Backup $friendly_rc abgebrochen"
            _timeout=$(get_timeout abort 10000)
        ;;
        DEADTIME)
            subject="DEADTIME"
            urgency="low"
            head="Backup $friendly_rc: Braucht noch nicht wieder"
            _timeout=$(get_timeout deadtime 2000)
        ;;
        FAIL) # Fehler beim Ausführen
            subject="FAIL"
            urgency="critical"
            head="Backup $friendly_rc: Fehler $_msgdate"
            _timeout=$(get_timeout fail 60000)
        ;;
        FATAL) # Fehler im Script / Konfiguration
            subject="WTF!"
            urgency="critical"
            head="Backup-Fehler (Fatal) $friendly_rc"
            _timeout=$(get_timeout fatal 3600000)
        ;;
        START)
            subject="START"
            urgency="low"
            head="Starte Backup $friendly_rc"
            _msg="$_msgdate"
            _timeout=$(get_timeout start 4000)
        ;;
        SUCCESS)
            subject="SUCCESS"
            urgency="low"
            head="Backup $friendly_rc: Erfolg"
            _timeout=$(get_timeout success 4000)
        ;;
        *)
            subject="$1"
            urgency="normal"
            head="Backup $friendly_rc"
            _timeout=$(get_timeout else 5000)
            shift
        ;;
    esac
    _msg="$* $_msg"
    notify-send -u $urgency -t $_timeout "$head" "$(sed 's/\\n/\n/g' <<<$_msg | fold -w 72 -s | head -c 131071)"
    verbose_echo "NOTIFY-SEND $head"
    verbose_echo $_msg
    local _loghost=$($config --section notify --key host --default localhost)
    local _loguser=$($config --section notify --key user --default $LOGNAME)
    local _logport=$($config --section notify --key port --default 22)
    local _logpipe=$($config --section notify --key pipe --default '')
    local _logremote=$($config --section notify --key remotekey --default $stripped_rc)
    local _logmsg="content-type: text/x-plain-log\n$_logremote\n$subject\n$_msg"
    if [ "$_logpipe" == "yes" ]; then
        local _errfile=$(mktemp)
        echo -e "$_logmsg" | \
            ssh $_loguser@$_loghost -p $_logport receiver \
            2>$_errfile || \
            (
                local _head="Backup-Fehler $friendly_rc"
                local _msg="Kann Meldungen nicht auf dem Server schreiben $_errfile:\\n$(one_line $_errfile)"
                local _timeout=$(get_timeout fatal 3600000)
                notify-send -u critical -t $_timeout "$_head" "$_msg"
                verbose_echo "NOTIFY-SEND $_head"
                verbose_echo $_msg
            )
        rm $_errfile
    else
        echo "$_logmsg"
    fi
}
