#!/bin/bash

# This script distributes the backup status to the appropriate places.
status=$1
message=$2
exec_dir=$(dirname $0)
config_dir="$($exec_dir/config_dir)"
if [ "$?" -ne "0" ] || [ -z "$config_dir" ]; then
    echo STATUS.SH Kann Konfigurationsverzeichnis nicht bestimmen >&2
    exit 127;
fi
config="$exec_dir/config.py --path $config_dir"
notify_local_low="$($config --section notify --key local_2)"
if [ "$?" -ne "0" ] || [ -z "$notify_local_low" ]; then
    notify_local_low="notify-send -u low "
fi
notify_local_med="$($config --section notify --key local_1)"
if [ "$?" -ne "0" ] || [ -z "$notify_local_med" ]; then
    notify_local_med="notify-send -u normal "
fi
notify_local_hih="$($config --section notify --key local_0)"
if [ "$?" -ne "0" ] || [ -z "$notify_local_hih" ]; then
    notify_local_hih="notify-send -u critical "
fi
logcmd="$($config --section notify --key log)"
if [ "$?" -ne "0" ] || [ -z "$logcmd" ]; then
    logcmd="cat "
    notify-send -u critical Backup "Kann nicht bestimmen, wohin der Status gemeldet werden soll"
fi
logcmd="$($config --section notify --key log)"
if [ "$?" -ne "0" ] || [ -z "$logcmd" ]; then
    notify_remote_hih="$logcmd"
fi
date="$(date +%Y-%m-%dT%H:%M:%S)"

case $status in
    START)
        $notify_local_low "Starte Backup" \
            "$date\n$message";
        echo "$date START $message" | $logcmd
        ;;
    SUCCESS)
        $notify_local_low "Backup: Erfolg" "$message";
        echo "$date SUCC $message" | $logcmd
        echo $message;;
    FATAL)
        # FATAL sind alle Fehler, die auf Programmierfehler oder
        # ungültige Konfiguration zurückzuführen sind.
        $notify_local_hih \
            "Backup-Fehler (FATAL)" \
            "Konnte nicht anfangen, das Backup zu machen:\n$message";
        echo "$date WTF! $message" | $logcmd
        ;;
    FAIL)
        # FAIL sind Fehler beim Backup selbst.
        $notify_local_hih "Backup: Fehler $date" "$message";
        echo "$date FAIL $message" | $logcmd
        echo $message >&2;;
    SUCCESS_MESSAGE)
        $notify_local_low "Backup: Erfolg" "$message\n$(< $config_dir/rsync.err)";
        echo "$date SUC* $message" | $logcmd
        echo $message;;
    *)
        $notify_local_hih "Backup: Unbekannter Status $status" \
        "Es ist nicht klar, was genau schiefgelaufen ist. \n\
        $message";
        echo "$date UNKN $status $message" | $logcmd
esac

exit 0;
