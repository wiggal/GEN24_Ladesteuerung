# Dynamischen Strompreis zum Laden des Akkus, bzw. Entladestopps verwenden.

Stand 18.03.2025
- Durch einen negativen Eintrag in die Spalte `Feste Entladegrenze(KW)` in der Tabelle `ENTLadeStrg` wird eine Zwangsladung für diese Stunde mit der eingetragenen Leistung in Kilowatt veranlasst. Der Eintrag kann auch manuell erfolgen. Der Parameter [Entladung] -> Batterieentlandung_steuern = 1 muss in der CONFIG/charge_priv.ini gesetzt sein.  
Die Zwangslandung wird dann durch http_SymoGen24Controller2.py auf den GEN24 geschrieben, wobei der Parameter schreiben erforderlich ist, bzw. in den Settings die Option `Ent- und Zwangsladesteuerung` gesetzt sein muss.

- Das Tool DynamicPriceCheck.py trägt die erforderlichen Zwangsladungen bzw. Ladepausen automatisch ein.  
Der Aufruf `start_PythonScript.sh DynamicPriceCheck.py schreiben` erfolgt entweder manuell, oder immer kurz vor einer vollen Stunde per Cronjob. Ohne den Parameter schreiben erfolgt nur eine Analyse, und es wird nichts in die Tabelle ENTLadeStrg geschrieben.  
Beispiel für Crontabeintrag mit einem alternativen Logfile:  
`58 * * * * /home/GEN24/start_PythonScript.sh -o LOG_DynamicPriceCheck.log DynamicPriceCheck.py schreiben`

  - Als Erstes prüft DynamicPriceCheck.py, ob in CONFIG/Prog_Steuerung.sqlite ein Lastprofil vorhanden, oder älter als die eingestellten Tage (`CONFIG/dynprice_priv.ini ==>> LastprofilNeuTage`) ist. Wenn eine Erzeugung erforderlich ist, erzeugt es aus den Daten der letzten 35 Tage aus der Loggingdatenbank PV_Daten.sqlite ein Lastprofil, und speichert es in CONFIG/Prog_Steuerung.sqlite. Das Lastprofil enthält den Durchschnittsverbrauch für jede Stunde jedes Wochentages. Ist in der Loggingdatenbank keine vollständige Woche (7 Tage) vorhanden, werden die fehlenden Werte mit 600 Watt aufgefüllt.
  - Parameter für die Nutzung des Tools `DynamicPriceCheck.py` werden in der CONFIG/dynprice_priv.ini gesetzt.  
  - Die Strompreise und die geplanten Zwangslandungen werden in die Datenbanktabellen `strompreise` bzw. `priceforecast` geschrieben. Daraus wird dann das Diagramm Strompreis gebildet.