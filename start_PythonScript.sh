#!/bin/bash
GEN24_Pfad_tmp=`dirname $0`
# Falls das skript nicht mit absolutem Pfad auferufen wird
GEN24_Pfad=`realpath $GEN24_Pfad_tmp`
GEN24_html_Pfad=${GEN24_Pfad}"/html"

Einfacher_PHP_Webserver=2
# Variable Einfacher_PHP_Webserver aus config.ini bestimmen
eval `grep "^Einfacher_PHP_Webserver" ${GEN24_Pfad}/config.ini|sed 's# ##g'`

# PHP_webserver auf PORT 2424 starten
if [ $Einfacher_PHP_Webserver == 1 ]
then
    cd $GEN24_html_Pfad
    if [ `ps -ef|grep "0.0.0.0:2424"|grep -v grep|wc -l` == 0 ]
    then
        nohup /usr/bin/php -S 0.0.0.0:2424 &
        echo -e `date` " PHP-Webserver gestartet! \n" >> ${GEN24_Pfad}/Crontab.log
    fi
fi

# PHP_webserver auf PORT 2424 beenden
if [ $Einfacher_PHP_Webserver == 0 ]
then
    cd $GEN24_html_Pfad
    if [ `ps -ef|grep "0.0.0.0:2424"|grep -v grep|wc -l` == 1 ]
    then
        #nohup /usr/bin/php -S 0.0.0.0:2424 &
        pid=`ps -ef|grep "0.0.0.0:2424"|grep -v grep|awk '{print $2}'`
        kill -9 $pid
        echo -e `date` " PHP-Webserver beendet! \n" >> ${GEN24_Pfad}/Crontab.log
    fi
fi
    
cd $GEN24_Pfad
if (( $# == 0))
then
    echo " Bitte Pythonscript als Parameter angeben!"
    exit
elif [[ ! -f "$1" ]]
then
    echo " Pythonscript \"$1\" existiert nicht!"
    exit
elif [[ "`file $1`" != *"Python script"* ]]
then
    echo "\"$1\" ist kein Pythonscript!"
    exit
fi

/usr/bin/python3 $1 $2 >>Crontab.log 2>&1
