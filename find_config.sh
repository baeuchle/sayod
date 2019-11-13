#!/bin/bash

stripped_rc=${rc/.rc}
stripped_rc=${stripped_rc/.ini}
config="$exec_dir/config.py --file $stripped_rc"
if $config --doesfileexist --section a --key b; then
    verbose_echo "Config file $stripped_rc found"
else
    notify FATAL "Konfigurationsscript kann nicht gestartet werden oder Konfigurationsdatei $stripped_rc nicht gefunden"
    exit 127;
fi

friendly_rc=$($config --section info --key friendly_name --default $stripped_rc)
verbose_echo "Friendly name $friendly_rc"
