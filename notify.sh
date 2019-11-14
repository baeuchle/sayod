#!/bin/bash

function notify {
    local _msgdate="$(date +%Y-%m-%dT%H:%M:%S)"
    local _msg=""
    local _level=$1
    shift
    case "$_level" in
        ABORT)
            subject="ABORT"
            urgency="normal"
            head="Backup $friendly_rc abgebrochen"
            timeout="10000"
        ;;
        DEADTIME)
            subject="DEADTIME"
            urgency="low"
            head="Backup $friendly_rc: Braucht noch nicht wieder"
            timeout="2000"
        ;;
        FAIL) # Fehler beim Ausführen
            subject="FAIL"
            urgency="critical"
            head="Backup $friendly_rc: Fehler $_msgdate"
            timeout="60000"
        ;;
        FATAL) # Fehler im Script / Konfiguration
            subject="WTF!"
            urgency="critical"
            head="Backup-Fehler (Fatal) $friendly_rc"
            timeout="3600000"
        ;;
        START)
            subject="START"
            urgency="low"
            head="Starte Backup $friendly_rc"
            _msg="$_msgdate"
            timeout="4000"
        ;;
        SUCCESS)
            subject="SUCCESS"
            urgency="low"
            head="Backup $friendly_rc: Erfolg"
            timeout="4000"
        ;;
        *)
            subject="$1"
            timeout="5000"
            urgency="normal"
            head="Backup $friendly_rc"
            shift
        ;;
    esac
    _msg="$* $_msg"
    notify-send -u $urgency -t $timeout "$head" "$(sed 's/\\n/\n/g' <<<$_msg | fold -w 72 -s)"
    verbose_echo "NOTIFY-SEND $head"
    verbose_echo $_msg
    local _loghost=$($config --section notify --key host --default localhost)
    local _loguser=$($config --section notify --key user --default $LOGNAME)
    local _logpipe=$($config --section notify --key pipe --emptydefault)
    local _logremote=$($config --section notify --key remotekey --default $stripped_rc)
    local _logmsg="content-type: text/x-plain-log\n$_logremote\n$subject\n$_msg"
    if [ "$_logpipe" == "yes" ]; then
        echo -e "$_logmsg" | ssh $_loguser@$_loghost receiver
        if [ $? -ne 0 ]; then
            head="Backup-Fehler $friendly_rc"
            _msg="Kann Meldungen nicht auf dem Server schreiben ($?)"
            notify-send -u critical -t 3600000 "$head" "$_msg"
            verbose_echo "NOTIFY-SEND $head"
            verbose_echo $_msg
        fi
    else
        echo "$_logmsg"
    fi
}
