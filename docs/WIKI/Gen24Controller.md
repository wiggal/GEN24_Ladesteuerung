# http_SymoGen24Controller2.py
<p><a name="user-content-️-gen24_ladesteuerung-"></a><strong>Programmfunktionen:</strong></p>
<ul>
	<li><p style="margin-bottom: 0cm">Prognosebasierte Ladesteuerung für
	Fronius Symo GEN24 Plus um eine Einspeisebegrenzung (bei mir 70%) zu
	umgehen, und eine Produktion über der AC-Ausgangsleistungsgrenze
	des WR als DC in die Batterie zu laden.<br/>
Über die Tabelle
	<a href="https://github.com/wiggal/GEN24_Ladesteuerung/#batterieladesteuerung--tab---ladesteuerung-">Ladesteuerung</a>
	können große, geplante Verbräuche bei der Ladeplanung
	berücksichtigt werden. 
	</p></li>
	<li><p style="margin-bottom: 0cm"><a href="https://github.com/wiggal/GEN24_Ladesteuerung/#batterieentladesteuerung--tab---entladesteuerung-">Entladesteuerung,</a>
	um die Entladung der Batterie bei großen Verbräuchen zu steuern. 
	</p></li>
	<li><p style="margin-bottom: 0cm"><a href="https://github.com/wiggal/GEN24_Ladesteuerung/#bar_chart-logging">Logging</a>
	und grafische Darstellung von Produktion und Verbrauch. 
	</p></li>
	<li><p style="margin-bottom: 0cm">Akkuschonung: Um einen LFP-Akku zu
	schonen, wird die Ladeleistung ab 80% auf 0,2C und ab 90% auf 0,1C
	(optional ab 95% weniger) beschränkt (anpassbar). 
	</p>
	<p style="margin-bottom: 0cm"></p></li>
</ul>
<p><strong>Funktionsweise:</strong></p>
<ul>
	<li><p>Das Tool http_SymoGen24Controller2.py ist in Python
	programmiert, und wird mit folgendem Aufruf in der Regel auf einem
	Linux System gestartet:<br/>
/DIR/start_PythonScript.sh
	http_SymoGen24Controller2.py</p></li>
	<li><p>Im Verzeichnis <b>CONFIG</b> wird mit charge.ini eine
	Konfiguration für http_SymoGen24Controller2.py ausgeliefert. Wird
	die charge.ini nach charge_priv.ini kopiert, können dort die
	eigenen Parameter eingestellt werden, ohne dass sie bei Updates
	überschrieben werden.</p></li>
	<li><p>In der <b>charge_priv.ini</b> können bestimmte Funktionen
	abgestellt werden, dann werden die Funktionen beim Programmlauf
	nicht durchlaufen, es erfolgt also auch keine Analyse für die
	Funktion (z.B. Entladung, Notstrom, EigenverbOptimum), die Funktion
	für die Ladesteuerung kann nicht abgeschaltet werden, da sie
	grundlegende Daten für alle weiteren Funktonen ermittelt. Die
	Analysen werden in die Protokolldatei Crontab.log geschrieben, wenn
	in der default_priv.ini print_level mindestens auf 1 gesetzt
	ist.<br/>
Weitere Parameter der charge_priv.ini sind in ihr oder der
	Hilfe, die in der WebUI aufrufbar ist erläutert.</p></li>
	<li><p>Welche berechneten Werte auf den Wechselrichter GEN24
	geschrieben werden, wird mit Aufrufparametern (Erklärung siehe
	nächsten Punkt) oder im Register Settings der WebUI gesteuert. Es
	ist aber zu beachten, dass für Funktionen, die in der
	charge_priv.ini von der Analyse ausgeschlossen wurden, auch keine
	berechneten Werte vorliegen und auch nicht auf den GEN24 geschrieben
	werden können, auch wenn der entsprechende Aufrufparameter gesetzt
	wird, während eine zur Analyse eingeschaltete Funktion ohne
	entsprechenden Aufrufparameter zwar analysiert aber nicht am GEN24
	geschrieben wird.</p></li>
	<li><p>Beim Aufruf von /DIR/start_PythonScript.sh
	http_SymoGen24Controller2.py können folgende Parameter mitgegeben
	werden, und steuern, welche Werte auf den GEN24 geschrieben werden,
	ausgenommen der Einstellungen in den WebUI Settings (siehe nächsten
	Punkt):</p>
	<ul>
		<li><p>logging = Damit werden die ermittelten Werte in der
		PV_Daten.sqlite gespeichert, die für weitere Berechnungen und die
		Darstellung in den Diagrammen benötigt werden.</p></li>
		<li><p>laden = Damit wird die Ladesteuerung auf den GEN24
		geschrieben. Die Werte werden am GEN24 unter En&shy;er&shy;gie&shy;ma&shy;nage&shy;ment
		-&gt; Bat&shy;te&shy;rie&shy;ma&shy;nage&shy;ment -&gt;
		Zeit&shy;ab&shy;hän&shy;gi&shy;ge Bat&shy;te&shy;rie&shy;steue&shy;rung
		gespeichert, und sind dort auch einsehbar.</p></li>
		<li><p>entladen = Damit werden die errechneten Entladewerte auf den
		GEN24 geschrieben. Dies sind z.B. Entladebegrenzungen oder
		Zwangsladungen, die in der WebUI im TAB ENTLadeStrg manuell oder
		über das Tool DynamicPriceCheck.py eingetragen wurden.</p></li>
		<li><p>optimierung = Damit werden die errechneten Werte im GEN24
		unter En&shy;er&shy;gie&shy;ma&shy;nage&shy;ment -&gt;
		Ei&shy;gen&shy;ver&shy;brauchs-Op&shy;ti&shy;mie&shy;rung
		eingetragen. Damit kann der Akku z.B. nachts je nach Prognose
		teilweise entladen werden, um am nächsten Tag genügend Kapazität
		für den Überschuss aus der Einspeisebegrenzung zu haben.</p></li>
		<li><p>notstrom = Hiermit wird ein prognoseabhängig berechneter
		Wert als Notstromreserve am GEN24 unter En&shy;er&shy;gie&shy;ma&shy;nage&shy;ment
		-&gt; Bat&shy;te&shy;rie&shy;ma&shy;nage&shy;ment -&gt;
		Reservekapazität geschrieben. Somit wäre bei einem Stromausfall
		genügend Akkukapazität vorhanden.</p></li>
		<li><p><b>schreiben</b> = Der Parameter setzt alle vorher
		angeführten Parameter auf einmal, und sie müssen nicht einzeln
		angeführt werden.</p></li>
	</ul>
	<p>Es können mehrere Parameter beim Programmaufruf folgendermaßen
	angegeben werden:<br/>
WICHTIG: Die Parameter werden mit Komma
	getrennt, und es dürfen <b>keine</b> Leerzeichen verwendet
	werden!!<br/>

 /DIR/start_PythonScript.sh
	http_SymoGen24Controller2.py 'logging,optimierung,notstrom'</p></li>
	<li><p>Welche Werte auf den GEN24 geschrieben werden, kann auch in
	der WebUI im TAB Settings gesteuert werden:<br/>
Ist der Punkt
	`WebUI-Settings ausschalten` angewählt, gelten ausschließlich die
	Parameter des Programmaufrufs.<br/>
Alle Anderen Punkte
	überschreiben die Parameter des Programmaufrufs. Nähere
	Informationen siehe in der zugehörigen Hilfe der WebUI.</p></li>
</ul>
<p><br/>
<br/>
<br/>
