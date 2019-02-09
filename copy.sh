#!/bin/bash

exec_dir=$(dirname $0)

status="$exec_dir/status.sh"
if [ "$?" -ne "0" ] || [ ! -x "$status" ]; then
    msg="Kann den Status nicht speichern";
    notify-send -u critical "Backup" "$msg"
    if [ -w $exec_dir ]; then
        fatal_log=$exec_dir/run_error
    else
        fatal_log=$HOME/fatal_backup_error
    fi
    echo $(date) $msg | tee -a $fatal_log >&2
    exit 127
fi

config_dir="$($exec_dir/config_dir)"
if [ "$?" -ne "0" ] || [ -z "$config_dir" ]; then
    $status FATAL "Kann Konfigurationsverzeichnis nicht bestimmen"
    exit 127;
fi
config="$exec_dir/config.py --path $config_dir"

$status START ""

# This part should do the actual copying.
source=$($config --section source --key path)
if [ "$?" -ne "0" ] || [ -z "$source" ]; then
    $status FATAL "Kann Quellpfad nicht bestimmen\n(sollte in source::path stehen)"
    exit 127;
fi
target=$($config --section target --key path)
if [ "$?" -ne "0" ] || [ -z "$target" ]; then
    $status FATAL "Kann Zielpfad nicht bestimmen\n(sollte in target::path stehen)"
    exit 127;
fi
exclude_file=$config_dir$($config --section source --key exclude_file)
if [ "$?" -ne "0" ] || [ -z "$exclude_file" ]; then
    $status FATAL "Kann nicht bestimmen, welche Dateien vom Backup ausgeschlossen werden sollen\n(sollte in source::exclude_file stehen)"
    exit 127;
fi
if [ ! -r "$exclude_file" ]; then
    $status FATAL "Kann Datei mit Ausschlussliste nicht lesen\n$exclude_file"
    exit 127;
fi

provide_exe=$config_dir$($config --section target --key provide)

if [ ! -d $target ]; then
    if [ -x $provide_exe ] && [ -f $provide_exe ]; then
        $provide_exe
    fi
    if [ ! -d $target ]; then
        $status FAIL "Ziel $target nicht gefunden, konnte auch nicht bereit gestellt werden"
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
        $status SUCCESS "Backup erfolgreich ausgeführt"
        exit 0;;
    23|24)
        $status SUCCESS_MESSAGE "Nicht alle Quelldateien konnten gelesen werden";
        exit 16;;
    [1246])
        $status FAIL "rsync usage error";
        exit 1;;
    3|5|10|11|12|13|14|21|22)
        $status FAIL "rsync copy error ($rsync_error)";
        exit 2;;
    25|40|35)
        $status FAIL "rsync other error $rsync_error";
        exit 3;;
    *)
        $status FAIL "Unknown rsync error $rsync_error";
esac
