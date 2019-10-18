#!/bin/bash

exec_dir=$(dirname $0)
msg_dir=$(mktemp -d)

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
$($config --section channel --key opening)

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

    echo $($config --section channel --key closing) >> $mailfile
    key=$($config --section channel --key sign)
    if [[ $key == 0x* ]]; then
        fold -w 72 -s $mailfile | \
            gpg --armor --clearsign --local-user $key> $mailfile.asc
        mv $mailfile.asc $mailfile
    fi
    email=$($config --section channel --key email)
    if [[ -z "$email" ]]; then
        email="backup-user@localhost"
    fi
    echo mail -s 'Backup-Script' $email < $mailfile
    cat $mailfile
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

now_date=$(date +%s)
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
last_success=$(grep ' SUC. ' $logfile | tail -n 1 | awk '{print $1}')
ls_date=$(date +%s -d "$last_success")
last_diff=$(( ($now_date - $ls_date) / (24 * 60 * 60 * $wm) ))
if [ $last_diff -gt 0 ]; then
    errorlog WARN "
        Das letzte erfolgreiche Backup ist länger als $wm Tage her. Nach
        dieser Zeitspanne erhälst du diese Warnung, weil wir sichergehen
        wollen, dass ein ausbleibendes Backup nicht bedeutet, dass etwas
        kaputt ist.
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
    line_date=$(date +%s -d "${line/ */}")
    line_past=$(( ($now_date - $line_date) / (24 * 60 * 60 * $se) ))
    if [ $line_past -le 1 ]; then
        line_level=$(awk '{print $2}' <<<$line)
        line_msg=$(cut -d' ' -f3- <<<$line)
        case $line_level in
            START)
                ;;
            SUCC)
                ;;
            SUC*)
                ;;
            *)
                errorlog ERR "$line_msg"
                ;;
        esac
    fi
done
