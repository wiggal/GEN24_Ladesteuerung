#!/usr/bin/env python3
# Datei: http_SymoGen24Controller2.py
# Zweck: Wrapper für inverter_akku_controller.py

import sys
import os
import runpy

print(
    "\n⚠️  [WARNUNG] Das Skript 'http_SymoGen24Controller2.py' ist veraltet.\n"
    "⚠️  [WARNUNG] Bitte verwende zukünftig 'EnergyController.py'.\n"
    "⚠️  [WARNUNG] Cronjob anpassen nicht vergessen!!\n",
    file=sys.stderr
)

# Absoluten Pfad zur neuen Datei bestimmen
current_dir = os.path.dirname(os.path.abspath(__file__))
new_script = os.path.join(current_dir, "EnergyController.py")

# Prüfen, ob die Datei existiert
if not os.path.exists(new_script):
    print(f"[FEHLER] '{new_script}' wurde nicht gefunden!", file=sys.stderr)
    sys.exit(1)

# Neues Skript im selben Prozess ausführen
runpy.run_path(new_script, run_name="__main__")

