#!/usr/bin/env python3
"""
db_scheduler.py
Wird jede Minute per Crontab aufgerufen:
    * * * * * /usr/bin/python3 /DIR/db_scheduler.py >> /DIR/Crontab.log 2>&1

Liest alle aktiven Jobs aus der SQLite-DB, prüft ob sie jetzt fällig sind,
und führt sie ggf. aus.
"""

import sqlite3
import subprocess
import os
import sys
import logging
from datetime import datetime

# ── Konfiguration ─────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(BASE_DIR, "CONFIG/Prog_Steuerung.sqlite")
LOG_FILE  = os.path.join(BASE_DIR, "Crontab.log")
#LOG_LEVEL = logging.INFO
LOG_LEVEL = logging.ERROR

# Maximale Laufzeit eines Jobs in Sekunden (danach wird er abgebrochen)
JOB_TIMEOUT = 300  # 5 Minuten

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ── Cron-Matching ─────────────────────────────────────────────────────────────

def _match_field(field: str, value: int, min_val: int, max_val: int) -> bool:
    """
    Prüft ob `value` zum Cron-Feld `field` passt.
    Unterstützt: * | Einzelwert | Liste (a,b,c) | Bereich (a-b) | Schritt (a-b/n, */n)
    """
    field = field.strip()

    # Komma-getrennte Liste → rekursiv prüfen
    if "," in field:
        return any(_match_field(f.strip(), value, min_val, max_val) for f in field.split(","))

    # Stern mit optionalem Schritt: * oder */n
    if field == "*":
        return True

    if "/" in field:
        range_part, step_str = field.split("/", 1)
        step = int(step_str)
        if range_part == "*":
            start = min_val
            end   = max_val
        elif "-" in range_part:
            start, end = (int(x) for x in range_part.split("-", 1))
        else:
            start = int(range_part)
            end   = max_val
        return value >= start and value <= end and (value - start) % step == 0

    # Einfacher Bereich: a-b
    if "-" in field:
        start, end = (int(x) for x in field.split("-", 1))
        return start <= value <= end

    # Einzelwert
    return int(field) == value


def is_due(job: dict, now: datetime) -> bool:
    """Gibt True zurück wenn der Job zum Zeitpunkt `now` laufen soll."""
    return (
        _match_field(job["Minute"],        now.minute,     0,  59) and
        _match_field(job["Stunde"],          now.hour,       0,  23) and
        _match_field(job["Tag_Monat"],  now.day,        1,  31) and
        _match_field(job["Monat"],         now.month,      1,  12) and
        _match_field(job["Tag_Woche"],   now.weekday() + 1, 1, 7)
        # weekday(): Mo=0..So=6 → +1 → Mo=1..So=7 (wie Cron üblich)
    )


# ── Datenbankzugriff ──────────────────────────────────────────────────────────

def load_jobs(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT * FROM cron_jobs WHERE Aktiv = 1")
    return [dict(row) for row in cur.fetchall()]


def update_job_status(conn: sqlite3.Connection, job_id: int, exit_code: int):
    conn.execute(
        "UPDATE cron_jobs SET Letzter_Lauf = ?, Letzter_Status = ? WHERE ID = ?",
        (datetime.now().isoformat(timespec="seconds"), exit_code, job_id),
    )
    conn.commit()


# ── Job-Ausführung ────────────────────────────────────────────────────────────

def run_job(job: dict, conn: sqlite3.Connection):
    name    = job["Name"]
    command = job["Befehl"]
    log.info(f"START  Job #{job['ID']} '{name}' → {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            timeout=JOB_TIMEOUT,
            capture_output=True,
            text=True,
        )
        exit_code = result.returncode
        if result.stdout.strip():
            log.info(f"STDOUT #{job['ID']}: {result.stdout.strip()}")
        if result.stderr.strip():
            log.warning(f"STDERR #{job['ID']}: {result.stderr.strip()}")
        level = logging.INFO if exit_code == 0 else logging.ERROR
        log.log(level, f"END    Job #{job['ID']} '{name}' → exit={exit_code}")

    except subprocess.TimeoutExpired:
        exit_code = -1
        log.error(f"TIMEOUT Job #{job['ID']} '{name}' nach {JOB_TIMEOUT}s abgebrochen")

    except Exception as exc:
        exit_code = -2
        log.exception(f"ERROR  Job #{job['ID']} '{name}': {exc}")

    update_job_status(conn, job["ID"], exit_code)


# ── Hauptprogramm ─────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(DB_PATH):
        log.error(f"Datenbank nicht gefunden: {DB_PATH}")
        log.error("Bitte zuerst 'python3 create_scheduler_db.py' ausführen.")
        sys.exit(1)

    now = datetime.now().replace(second=0, microsecond=0)
    log.debug(f"Scheduler läuft für {now:%Y-%m-%d %H:%M}")

    conn  = sqlite3.connect(DB_PATH)
    jobs  = load_jobs(conn)
    due   = [j for j in jobs if is_due(j, now)]

    if not due:
        log.debug(f"Keine Jobs fällig um {now:%H:%M}")
        conn.close()
        return

    log.info(f"{len(due)} Job(s) fällig um {now:%H:%M}")

    for job in due:
        run_job(job, conn)

    conn.close()


if __name__ == "__main__":
    main()
