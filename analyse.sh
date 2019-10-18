#!/bin/bash

exec_dir=$(dirname $0)
msg_dir=$(mktemp -d)

function get_seconds {
    curr_date="$*"
    if [ "$curr_date" == "" ]; then
        date +%s
        return
    fi
    date +%s -d "$curr_date"
}

function days_in_past {
    curr_date="$*"
    curr_seconds=$(get_seconds "$curr_date")
    now_seconds=$(get_seconds)
    echo $(( ($now_seconds - $curr_seconds) / (24 * 60 * 60) ))
}

function errorlog {
    category=$1
    shift
    count=$(ls $msg_dir/* 2>/dev/null | wc -l)
    next_count=$(( ($count + 1) ))
    echo "$*" > $msg_dir/$next_count.$category
}

function report_all_messages {
    noti=$(ls $msg_dir/*.NOTIFY 2>/dev/null | wc -l)
    warn=$(ls $msg_dir/*.WARN   2>/dev/null | wc -l)
    errs=$(ls $msg_dir/*.ERR    2>/dev/null | wc -l)
    alls=$(ls $msg_dir/*        2>/dev/null | wc -l)
    if [ $alls -eq 0 ]; then
        rmdir $msg_dir
        exit 0;
    fi
    mailfile=$(mktemp)
    cat >> $mailfile <<EOF
$($config --section mail --key opening)

Die Analyse der letzten Backups hat $alls Meldung(en) gefunden:
EOF
    if [ $noti -gt 0 ]; then
        echo " - $noti Information(en)" >> $mailfile
    fi
    if [ $warn -gt 0 ]; then
        echo " - $warn Warnung(en)" >> $mailfile
    fi
    if [ $errs -gt 0 ]; then
        echo " - $errs Fehler" >> $mailfile
    fi
    echo "" >> $mailfile
    if [ $errs -gt 0 ]; then
        echo "##### FEHLER #####" >> $mailfile
        echo "" >> $mailfile
        cat $msg_dir/*.ERR >> $mailfile
        echo "">> $mailfile
    fi
    if [ $warn -gt 0 ]; then
        echo "##### WARNUNGEN #####" >> $mailfile
        echo "" >> $mailfile
        cat $msg_dir/*.WARN >> $mailfile
        echo "">> $mailfile
    fi
    if [ $noti -gt 0 ]; then
        echo "##### INFORMATIONEN #####" >> $mailfile
        echo "" >> $mailfile
        cat $msg_dir/*.NOTIFY >> $mailfile
        echo "">> $mailfile
    fi

    echo $($config --section mail --key closing) >> $mailfile
    key=$($config --section mail --key sign)
    if [[ $key == 0x* ]]; then
        fold -w 72 -s $mailfile | \
            gpg --armor --clearsign --local-user $key> $mailfile.asc
        mv $mailfile.asc $mailfile
    fi
    email=$($config --section mail --key email)
    if [[ -z "$email" ]]; then
        email="backup-user@localhost"
    fi
    mailprg=$($config --section --mail --key cmd)
    if [[ -z "$mailprg" ]]; then
        mailprg="echo"
    fi
    $mailprg -s 'Backup-Script' $email < $mailfile
    if [[ "$mailprg" -eq "echo" ]]; then
        cat $mailfile
    fi
    rm $mailfile
    rm -rf $msg_dir
}
trap report_all_messages EXIT

config_dir="$($exec_dir/config_dir)"
if [ "$?" -ne "0" ] || [ -z "$config_dir" ]; then
    errorlog ERR "Kann Konfigurationsverzeichnis nicht bestimmen"
    exit 127;
fi
config="$exec_dir/config.py --path $config_dir --file analyse.rc"
if ! $config --help > /dev/null 2>&1; then
    errorlog ERR "Konfigurationsscript kann nicht gestartet werden"
    exit 127;
fi

logfile=$($config --section status --key file)
if [ "$?" -ne "0" ] || [ -z "$logfile" ]; then
    errorlog ERR "Kann Statusdateiname status::file nicht bestimmen"
    exit 127;
fi

if [ ! -r "$logfile" ]; then
    errorlog NOTIFY "Kann Statusdatei\
    $logfile\
    nicht finden. Vielleicht wurde noch nie ein Backup erstellt?"
    exit 63
fi
wm=$($config --section status --key warn_missing)
if [[ -z "$wm" ]] || [[ $wm -le 0 ]]; then
    errorlog WARN "
    Kann nicht herausfinden, was das Warnintervall ist, benutze 7 Tage
    "
    wm=7
fi
last_success="$(grep ' SUCCESS ' $logfile | tail -n 1 | awk '{print $1}')"
last_diff=$(days_in_past $last_success)
last_start=$(days_in_past "$(grep ' START ' $logfile | tail -n 1 | awk '{print $1}')")
if [[ $last_diff -gt $wm ]]; then
    errorlog WARN "
        Das letzte erfolgreiche Backup ist länger als $wm Tage her (es
        wurde bei $last_success beendet). Nach dieser Zeitspanne erhälst
        du diese Warnung, weil wir sichergehen wollen, dass ein
        ausbleibendes Backup nicht bedeutet, dass etwas kaputt ist.
        Das letzte angefangende Backup war vor $last_start Tagen.
"
fi

se=$($config --section status --key stale_errors)
if [[ -z "$se" ]] || [[ $se -le 0 ]]; then
    errorlog WARN "
    Kann nicht herausfinden, wie alt gemeldete Fehler sein sollen, nehme 7 Tage
    an.
    "
    se=7
fi

cat $logfile | while read -r line; do
    line_past=$(days_in_past $(date -I -d "${line/ */}"))
    if [[ $line_past -le $se ]]; then
        line_level=$(awk '{print $2}' <<<$line)
        line_msg=$(cut -d' ' -f3- <<<$line)
        case $line_level in
            START)
                ;;
            SUCCESS)
                ;;
            *)
                errorlog ERR "$line_msg ($line_level ${line/ */})"
                ;;
        esac
    fi
done
