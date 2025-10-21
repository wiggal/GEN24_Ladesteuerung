#!/bin/bash
GEN24_Pfad_tmp=`dirname $0`
# Falls das skript nicht mit absolutem Pfad auferufen wird
GEN24_Pfad=`realpath $GEN24_Pfad_tmp`
GEN24_html_Pfad=${GEN24_Pfad}"/html"

Einfacher_PHP_Webserver="0"
# Variable Einfacher_PHP_Webserver bestimmen
eval `grep -s "^Einfacher_PHP_Webserver" ${GEN24_Pfad}/CONFIG/default.ini|sed 's# ##g'`
eval `grep -s "^Einfacher_PHP_Webserver" ${GEN24_Pfad}/CONFIG/default_priv.ini|sed 's# ##g'`

# PHP_webserver auf PORT 2424 starten
if [[ $Einfacher_PHP_Webserver == 1 ]]
then
    cd $GEN24_html_Pfad
    if [[ `ps -ef|grep "0.0.0.0:2424"|grep -v grep|wc -l` == 0 ]]
    then
        nohup /usr/bin/php -S 0.0.0.0:2424 2>> /dev/null &
        echo -e `date` " PHP-Webserver gestartet! \n" >> ${GEN24_Pfad}/Crontab.log
    fi
fi

# PHP_webserver auf PORT 2424 beenden
if [[ $Einfacher_PHP_Webserver == 0 ]]
then
    cd $GEN24_html_Pfad
    if [[ `ps -ef|grep "0.0.0.0:2424"|grep -v grep|wc -l` == 1 ]]
    then
        #nohup /usr/bin/php -S 0.0.0.0:2424 &
        pid=`ps -ef|grep "0.0.0.0:2424"|grep -v grep|awk '{print $2}'`
        kill -9 $pid
        echo -e `date` " PHP-Webserver beendet! \n" >> ${GEN24_Pfad}/Crontab.log
    fi
fi

cd $GEN24_Pfad
LOGFILE="Crontab.log"
# Hilfsfunktion für die Argumentbehandlung
while getopts "ho:" opt; do
  case "$opt" in
    o)
      LOGFILE="$OPTARG"
      ;;
    h)
      echo "Usage: $0 [-o logging_file] [Pythonskript Argumente]"
      exit 0
      ;;
    *)
      echo "Invalid option: -$opt"
      echo "Usage: $0 [-o logging_file] [Pythonskript Argumente]"
      exit 1
      ;;
  esac
done
shift $((OPTIND - 1))
if (( $# == 0))
then
    echo " Bitte Pythonscript als Parameter angeben!" >> ${GEN24_Pfad}/Crontab.log
    exit
elif [[ ! -f "$1" ]]
then
    echo " Pythonscript \"$1\" existiert nicht!" >> ${GEN24_Pfad}/Crontab.log
    exit
elif [[ "`file $1`" != *"Python script"* ]]
then
    echo "\"$1\" ist kein Pythonscript!" >> ${GEN24_Pfad}/Crontab.log
    exit
fi

/usr/bin/python3 $1 $2 >> $LOGFILE 2>&1
