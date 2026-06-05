# ============================================================
# GEN24 Ladesteuerung – Home Assistant Addon
# Build-Kontext ist das ha_addon/ Verzeichnis selbst.
# Der Repo-Code wird per git clone geholt.
# ============================================================
ARG BUILD_FROM
FROM ${BUILD_FROM}

ARG BUILD_VERSION

LABEL \
  io.hass.name="GEN24 Ladesteuerung" \
  io.hass.description="Fronius GEN24/Verto prognosebasierte Ladesteuerung" \
  io.hass.type="addon" \
  io.hass.version="${BUILD_VERSION}" \
  maintainer="wiggal <ludwig.sporrer@gmx.de>"

# --- Abhängigkeiten ---
RUN apk add --no-cache \
        git \
        php-openssl \
        php \
        php-json \
        php-sqlite3 \
        php-cli \
        php-posix \
        php-curl \
        tzdata \
        python3 \
        py-pip \
        bash \
        file \
        py3-yaml \
        py3-aiohttp \
        py3-websockets \
        py3-requests \
 && touch /var/log/cron.log

# --- s6-Overlay run-Skript (liegt jetzt direkt im Build-Kontext) ---
COPY rootfs /

RUN chmod a+x /etc/s6-overlay/s6-rc.d/gen24-app/run
