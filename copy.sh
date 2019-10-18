#!/bin/bash

exec_dir=$(dirname $0)
if [ "$(which notify-send)" == "" ]; then
    echo "Kann notify-send nicht finden, bitte installieren";
    exit 127
fi

function notify {
    msg=""
    level=$1
    shift
    case "$level" in
        FAIL) # Fehler beim Ausführen
            subject="FAIL"
            urgency="critical"
            head="Backup: Fehler $(date)"
        ;;
        FATAL) # Fehler im Script / Konfiguration
            subject="WTF!"
            urgency="critical"
            head="Backup-Fehler (Fatal)"
        ;;
        START)
            subject="START"
            urgency="low"
            head="Starte Backup"
            msg="$(date)"
        ;;
        SUCCESS)
            subject="SUCC"
            urgency="low"
            head="Backup: Erfolg"
        *)
            subject="$1"
            shift
        ;;
    esac
    msg=$* $msg
    notify-send -u $urgency "$head" "$msg"
    logcmd=$($config --section notify --key log)
    logpipe=$($config --section notify --key pipe)
    logmsg="$(date) $level_for_log $message"
    if [ "$logpipe" == "yes" ]; then
        echo "$logmsg" | $logcmd
    else
        $logcmd "$logmsg"
    fi
}

config_dir="$($exec_dir/config_dir)"
if [ "$?" -ne "0" ] || [ -z "$config_dir" ]; then
    notify FATAL "Kann Konfigurationsverzeichnis nicht bestimmen"
    exit 127;
fi
config="$exec_dir/config.py --path $config_dir"
if ! $config --help > /dev/null 2>&1; then
    notify FATAL "Konfigurationsscript kann nicht gestartet werden"
    exit 127;
fi

notify START "Starte Backup" "$(date)"

# This part should do the actual copying.
source=$($config --section source --key path)
if [ "$?" -ne "0" ] || [ -z "$source" ]; then
    notify FATAL "Kann Quellpfad nicht bestimmen (sollte in source::path stehen)"
    exit 127;
fi
target=$($config --section target --key path)
if [ "$?" -ne "0" ] || [ -z "$target" ]; then
    notify FATAL "Kann Zielpfad nicht bestimmen (sollte in target::path stehen)"
    exit 127;
fi
exclude_file=$config_dir$($config --section source --key exclude_file)
if [ "$?" -ne "0" ] || [ -z "$exclude_file" ]; then
    notify FATAL "Kann nicht bestimmen, welche Dateien vom Backup ausgeschlossen werden sollen (sollte in source::exclude_file stehen)"
    exit 127;
fi
if [ ! -r "$exclude_file" ]; then
    notify FATAL "Kann Datei mit Ausschlussliste nicht lesen\n$exclude_file"
    exit 127;
fi

provide_exe=$config_dir$($config --section target --key provide)

if [ ! -d $target ]; then
    if [ -x $provide_exe ] && [ -f $provide_exe ]; then
        $provide_exe
    fi
    if [ ! -d $target ]; then
        notify FAIL "Ziel $target nicht gefunden, konnte auch nicht bereit gestellt werden"
        exit 2
    fi
fi

rsync --partial -a \
        -n \
        --exclude-from=$exclude_file \
        $source \
        $target \
        > $config_dir/rsync.log \
        2> $config_dir/rsync.err
rsync_error=$?

case $rsync_error in
    0)
        notify SUCCESS
        exit 0;;
    23|24)
        notify SUCCESS "Nicht alle Quelldateien konnten gelesen werden";
        exit 0;;
    [1246])
        notify FATAL "rsync usage error";
        exit 1;;
    3|5|10|11|12|13|14|21|22)
        notify FAIL "rsync copy error ($rsync_error)";
        exit 2;;
    25|40|35)
        notify FAIL "rsync other error $rsync_error";
        exit 3;;
    *)
        notify FAIL "Unknown rsync error $rsync_error";
        exit $rsync_error;;
esac
