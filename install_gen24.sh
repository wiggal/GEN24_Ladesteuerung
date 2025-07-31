#!/usr/bin/env bash
set -e

####################################################################
# Installation von GEN24_Ladesteuerung 
# !! Benutzung auf eigene Gefahr !!
# Folgende Schritte werden ausgeführt:
# - erfordeliche Pakete installieren
# - IP und Kennwort GEN24 abfragen und default_priv.ini anlegen
# - USER gen24 mit $HOME=/home/gen24 anlegen
# - /home/GEN24 anlegen und Skripte von github.com pullen
# - cronjobs erstellen
####################################################################

# Variablen definieren
USERNAME="gen24"
PASSWORD="gen24"
HOMEDIR="/home/gen24"
SHELL="/bin/bash"
REPO_URL="https://github.com/wiggal/GEN24_Ladesteuerung.git"
REPO_DIR="/home/GEN24"

# BETA-Hinweis
echo "Das Installationsskript ist noch BETA, Benutzung ohne Gewähr. Fortsetzen? (j/n)"
read -r antwort1
if [[ "$antwort1" == "j" || "$antwort1" == "J" ]]; then
    echo "Installation wird fortgesetzt..."
else
    echo "Installation abgebrochen."
    exit 1
fi


# Funktion zum Erkennen der Distribution
# Aktuell nur für DEBIAN und ALPINE Syteme 
detect_distro(){
  if [ -f /etc/debian_version ]; then
    PM="apt-get install -y"
    UPDATE="apt-get update -y"
    # DEBIAN-Paketliste
    packages=(iputils-ping cron file git python3 python3-pip python3-requests php php-sqlite3)
    SYSTEM=DEBIAN
    SUDO_IST='sudo'
  elif [ -f /etc/alpine-release ]; then
    PM="apk --update add"
    UPDATE=""
    packages=(shadow iputils-ping file git python3 py-pip py3-requests php php-sqlite3)
    SYSTEM=ALPINE
    # In Alpine ist sudo nicht standardmäßig vorhanden
    SUDO_IST=''
 # elif [ -f /etc/fedora-release ]; then
 #   PM="dnf install -y"
 #   UPDATE="dnf makecache"
 # elif [ -f /etc/centos-release ]; then
 #   PM="yum install -y"
 #   UPDATE="yum makecache"
 # elif [ -f /etc/arch-release ]; then
 #   PM="pacman -S --noconfirm"
 #   UPDATE="pacman -Sy"
  else
    echo "Distribution nicht erkannt – manuelle Installation erforderlich."
    exit 1
  fi
}

# erforderliche Programmpakete installieren
main(){
  detect_distro
  # Abfrage ob Pakete installiert werden sollen
  echo -e "\nSystem $SYSTEM erkannt!"
  echo -e "Folgende Pakete werden installiert ${packages[*]}.\nInstallation fortsetzen? (j/n)"
  read -r antwort1
  if [[ "$antwort1" == "j" || "$antwort1" == "J" ]]; then
      echo "Updating package database..."
  else
      echo "Installation abgebrochen."
      exit 1
  fi

  if [ -n "$UPDATE" ]; then $SUDO_IST $UPDATE; fi

  echo "Installing packages: ${packages[*]}"
  $SUDO_IST $PM "${packages[@]}"
  echo -e "Installationen abgeschlossen.\n"
}

main "$@"


# CONFIG/default_priv.ini mit Benutzereingaben erzeugen
if [ ! -f "CONFIG/default_priv.ini" ]; then
    # IP-Adresse Wechselrichter abfragen und prüfen
    echo "Daten zum Anlegen von CONFIG/default_priv.ini." 
    while true; do
        read -rp "Bitte geben Sie die IP-Adresse des GEN24 ein: " ip_adresse
    
        echo "Prüfe Erreichbarkeit von $ip_adresse ..."
        if ping -c 1 -W 1 "$ip_adresse" &>/dev/null; then
            echo "Wechselrichter erreichbar."
            break
        else
            echo "❌ IP-Adresse nicht erreichbar. Erneut versuchen? (j/n)"
            read -r erneut
            [[ "$erneut" =~ ^[Nn]$ ]] && echo "Abbruch." && exit 1
        fi
    done

    # Kennwort abfragen
    read -rp "Bitte geben Sie das Kennwort ein: " kennwort
fi

echo ""
echo "IP-Adresse des GEN24 ist $ip_adresse"
echo "GEN24 Kennwort für customer ist $kennwort"
echo "Es wird der User $USERNAME mit Homeverzeichnis $HOMEDIR angelegt!"
echo "Die Skripte zur GEN24_Ladesteuerung werden in $REPO_DIR abgelegt und konfiguriert."

echo "Wollen Sie mit diesen Einstellungen installieren? (j/n)"
read -r antwort
if [[ "$antwort" == "j" || "$antwort" == "J" ]]; then
    echo "Installation wird gestartet..."
    # Hier kommt dein Installationsbefehl hin
else
    echo "Installation abgebrochen."
    exit 1
fi

# Prüfen, ob Benutzer existiert
if id -u "$USERNAME" &>/dev/null; then
  echo "Benutzer $USERNAME existiert bereits."
else
  echo "Legt Benutzer $USERNAME an ..."
  # Benutzer samt Homeverzeichnis und Shell anlegen
  useradd -m -d "$HOMEDIR" -s "$SHELL" "$USERNAME"
  # Passwort setzen
  echo "${USERNAME}:${PASSWORD}" | chpasswd
  echo "Benutzer $USERNAME angelegt mit Home $HOMEDIR und Passwort gesetzt."
fi

# Prüfen, ob .git-Unterverzeichnis existiert
mkdir -p $REPO_DIR
cd $REPO_DIR
if [ -d ".git" ]; then
  echo "Git-Repository vorhanden – führe git pull aus."
  git pull
else
  echo "Kein Git-Repository gefunden – clonen."
  #git clone "$REPO_URL" .  #entWIGGlung
  git clone --branch v0.31.0 "$REPO_URL" .  #entWIGGlung
fi

# Datenbanken anlegen, wenn nicht vorhanden!
cd $REPO_DIR
export PYTHONPATH=/home/GEN24/FUNCTIONS
# weatherData.sqlite
if [ ! -s "weatherData.sqlite" ]; then
    python3 -c "from WeatherData import WeatherData; WeatherData().create_database('/home/GEN24/weatherData.sqlite')"
fi
#PV_Daten.sqlite
if [ ! -s "PV_Daten.sqlite" ]; then
    python3 -c "from SQLall import sqlall; sqlall().create_database_PVDaten('/home/GEN24/PV_Daten.sqlite')"
fi
#CONFIG/Prog_Steuerung.sqlite
if [ ! -s "CONFIG/Prog_Steuerung.sqlite" ]; then
    python3 -c "from SQLall import sqlall; sqlall().create_database_ProgSteuerung('/home/GEN24/CONFIG/Prog_Steuerung.sqlite')"
fi

# CONFIG/default_priv.ini mit Benutzereingaben erzeugen
if [ ! -f "CONFIG/default_priv.ini" ]; then
    sed -e "s/^hostNameOrIp *= *.*/hostNameOrIp = $ip_adresse/" \
        -e "s/^password *= *.*/password = '$kennwort'/" \
        CONFIG/default.ini > CONFIG/default_priv.ini
fi

# Eigentümer gen24 auf /home/GEN24 setzten
$SUDO_IST chown -R gen24:gen24 $REPO_DIR

# Cronjobs für gen24 anlegen
# Prüfen, ob der User eine Crontab hat
if crontab -u "$USERNAME" -l &>/dev/null; then
  echo "Benutzer $USERNAME hat bereits eine Crontab – keine Änderungen."
  exit 0
fi

# Neue Crontab definieren
CRON_ENTRIES=$(cat <<'EOF'
1-56/10 * * * * /home/GEN24/start_PythonScript.sh http_SymoGen24Controller2.py logging
2 3-21 * * * /home/GEN24/start_PythonScript.sh FORECAST/Akkudoktor__WeatherData.py
3 3,7,9,11,13,15,17,19 * * * /home/GEN24/start_PythonScript.sh FORECAST/Forecast_solar__WeatherData.py
# 4 3,7,9,11,13,15,17,19 * * * /home/GEN24/start_PythonScript.sh FORECAST/Solcast_WeatherData.py
32 * * * * /home/GEN24/start_PythonScript.sh FORECAST/OpenMeteo_WeatherData.py
# 7 3,7,9,11,13,15,17,19 * * * /home/GEN24/start_PythonScript.sh FORECAST/Solarprognose_WeatherData.py
0 0 * * 1 mv /home/GEN24/Crontab.log /home/GEN24/Crontab.log_weg
EOF
)

# Crontab erstellen
echo "$CRON_ENTRIES" | crontab -u "$USERNAME" -
echo "Crontab für Benutzer $USERNAME wurde angelegt."

