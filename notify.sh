#!/bin/bash

function notify {
    local _msgdate="$(date +%Y-%m-%dT%H:%M:%S)"
    msg=""
    level=$1
    shift
    case "$level" in
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
            msg="$_msgdate"
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
    msg="$* $msg"
    notify-send -u $urgency -t $timeout "$head" "$(sed 's/\\n/\n/g' <<<$msg | fold -w 72 -s)"
    verbose_echo "NOTIFY-SEND $head"
    verbose_echo $msg
    loghost=$($config --section notify --key host --default localhost)
    loguser=$($config --section notify --key user --default $LOGNAME)
    logpipe=$($config --section notify --key pipe --emptydefault)
    logremote=$($config --section notify --key remotekey --default $stripped_rc)
    logmsg="content-type: text/x-plain-log\n$logremote\n$subject\n$msg"
    if [ "$logpipe" == "yes" ]; then
        echo -e "$logmsg" | ssh $loguser@$loghost receiver
        if [ $? -ne 0 ]; then
            head="Backup-Fehler $friendly_rc"
            msg="Kann Meldungen nicht auf dem Server schreiben ($?)"
            notify-send -u critical -t 3600000 "$head" "$msg"
            verbose_echo "NOTIFY-SEND $head"
            verbose_echo $msg
        fi
    else
        echo "$logmsg"
    fi
}
