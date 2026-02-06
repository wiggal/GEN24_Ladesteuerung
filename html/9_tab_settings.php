  <script src="jquery.min.js"></script>
  <style>
  .center {
  margin-left: auto;
  margin-right: auto;
  }
  .speichern {
	background-color:#FB5555;
	border-radius:28px;
	background-color:#FB5555;
	display:inline-block;
	cursor:pointer;
	color:#000000;
	font-size:200%;
	padding:16px 31px;
	text-decoration:none;
	text-shadow:0px 1px 0px #FB5555;
    white-space: nowrap;
    position: fixed;
    transform: translate(-50%, 0);
  }
  .speichern:hover {
	background-color:#EE3030;
  }
  .speichern:active {
	position: fixed;
  }

/* LADEGRENZE */
/* ===== FLEX-CONTAINER ===== */
.flex-container {
  display: flex;
  flex-direction: column;
  margin: auto;               /* horizontal zentriert */
  background: #fff;
  align-items: flex-start;    /* Kinder links ausrichten */
  padding: 25px 28px;
  box-shadow: 5px 5px 30px rgba(0,0,0,0.2);

  width: fit-content;         /* Container passt sich Inhalt an */
  max-width: 100%;            /* niemals breiter als Bildschirm */
  box-sizing: border-box;     /* Padding wird eingerechnet */
}

/* Radiobuttons */
input[type="radio"] {
   width: 30px;
   height: 30px;
   accent-color: #FB5555;
}

/* CHECKBOX */
input[type="checkbox"] {
   width: 30px;
   height: 30px;
   accent-color: #FB5555;
}

/* ===== RADIO / CHECKBOX LABELS ===== */
.auswahllabel {
  font-size: 1.5rem;
  line-height: 1.4;
  padding: 5px 8px;
  display: grid;
  grid-template-columns: 1.5em minmax(0, 1fr); /* Checkbox/Radio + Text */
  grid-gap: 0.5em;
  align-items: center;
  white-space: nowrap;      /* keine Umbrüche */
  overflow: hidden;         /* überstehender Text wird abgeschnitten */
  text-overflow: ellipsis;  /* "..." am Ende bei zu langem Text */
  max-width: 100%;          /* Text nie breiter als Container */
}

.ACHTUNG{
  font-size:150%;
  color: #000000;
  margin-top: 100px !important; /* Abstand nach oben zum Button */
  margin-bottom: 10px !important; /* Abstand nach unten zum Slider */
}
.containerbeschriftung{
  font-weight: bold;
  font-size:120%;
  color: #000000;
}

/* Spezielle Anpassung für Mobilgeräte */
@media (max-width: 600px) {
  .ACHTUNG {
    font-size: 100% !important;
    margin-top: 70px !important; /* Abstand nach oben zum Button */
    margin-bottom: 5px !important; /* Abstand nach unten zum Slider */
  }

  .auswahllabel {
    font-size: 100% !important;
  }
  input[type="checkbox"] {
    width: 20px;
    height: 20px;
  }
  input[type="radio"] {
    width: 20px;
    height: 20px;
  }

  th, td {
    font-size: 90%; /* Schrift auf Handys deutlich verkleinern */
  }

  .sliderbeschriftung{
    font-size:90%;
    margin-top: 25px !important; /* Abstand nach oben zum Button */
    margin-bottom: 10px !important; /* Abstand nach unten zum Slider */
  }

  .flex-container {
    width: 95% !important; /* Container fast volle Breite */
    padding: 5px 2px !important;
  }

  .speichern {
    font-size: 100% !important; /* Speicher-Button verkleinern */
    padding: 8px 10px !important;
  }

  .dropdown {
    font-size: 1.2rem !important; /* Dropdown kleiner */
  }

  /* Tabelle zwingen, in die Breite zu passen */
  table.center {
    width: 90% !important;
    display: table; /* Stellt sicher, dass sie sich wie eine Tabelle verhält */
  }
  table.center td,
  table.center th {
    white-space: normal;        /* Umbruch erlauben */
    word-wrap: break-word;      /* alte Browser */
    overflow-wrap: break-word;  /* moderne Browser */
  }
}
</style>

<!-- Hilfeaufruf ANFANG -->
<?php
  $hilfe_link = "index.php?tab=Hilfe&file={$activeTab}";
?>
  <div class="hilfe"> <a href="<?php echo $hilfe_link; ?>"><b>Hilfe</b></a></div>
<!-- Hilfeaufruf ENDE -->

<div align="center"><button type="button" id="import_data" class="speichern">Einstellungen speichern</button></div>

   <div class="ACHTUNG" align="center"><p>
   <b>ACHTUNG:</b> Wenn die WebUI-Settings nicht ausgeschaltet sind, 
   <br>überschreiben sie die Aufrufparameter des Skriptes (z.B. vom Cronjob)!
   </p></div>

<?php
# DB-Eintraege lesen
include 'SQL_steuerfunctions.php';
$EV_Reservierung = getSteuercodes('ProgrammStrg');

#Radiobutton wie in DB setzen
$Setting_radio = array();
for ($i = 0; $i <= 4; $i++) {
    if ($EV_Reservierung['23:09']['Res_Feld1'] == $i){
        $Setting_radio[$i] = 'checked';
    } else {
        $Setting_radio[$i] = '';
    }
}

#Checkbox wie in DB setzen
$CheckOptionsDB = explode(":", $EV_Reservierung['23:09']['Options']);
$CheckOptionsALL = array("logging", "laden", "entladen", "optimierung",'notstrom','dynamicprice');
$Setting_check = array();
foreach ($CheckOptionsALL as &$option) {
    if (in_array($option, $CheckOptionsDB)) {
        $Setting_check[$option] = 'checked';
    } else {
        $Setting_check[$option] = '';
    }
}
?>

<div style='text-align: center;'>
  <p class="containerbeschriftung">Programmsteuerung:</p>
<div class="flex-container">
 <label class="auswahllabel" ><input type="radio" name="hausakkuladung" id="steuer0" value="0" onclick="disablecheckboxes('steuer0')" <?php echo $Setting_radio['0'] ?>>WebUI-Settings ausschalten</label>
 <label class="auswahllabel" ><input type="radio" name="hausakkuladung" id="steuer1" value="1" onclick="disablecheckboxes('steuer1')" <?php echo $Setting_radio['1'] ?>>Ladesteuerung AUS (WR-Settings löschen)</label>
 <label class="auswahllabel" ><input type="radio" name="hausakkuladung" id="steuer2" value="2" onclick="disablecheckboxes('steuer2')" <?php echo $Setting_radio['2'] ?>>Ladesteuerung AUS (WR-Settings belassen)</label>
 <label class="auswahllabel" ><input type="radio" name="hausakkuladung" id="steuer3" value="3" onclick="disablecheckboxes('steuer3')" <?php echo $Setting_radio['3'] ?>>Nur Analyse in Crontab.log</label>
 <label class="auswahllabel" ><input type="radio" name="hausakkuladung" id="steuer4" value="4" onclick="disablecheckboxes('steuer4')" <?php echo $Setting_radio['4'] ?>>Ladesteuerung nach folgenden Optionen:</label>

 <label style="padding: 5px 50px" class="auswahllabel" ><input type="checkbox" name="hausakkuladung.option" id="steuer5" value="logging" <?php echo $Setting_check['logging'] ?> >Logging</label>
 <label style="padding: 5px 50px" class="auswahllabel" ><input type="checkbox" name="hausakkuladung.option" id="steuer6" value="laden" <?php echo $Setting_check['laden'] ?> >Ladesteuerung</label>
 <label style="padding: 5px 50px" class="auswahllabel" ><input type="checkbox" name="hausakkuladung.option" id="steuer7" value="entladen" <?php echo $Setting_check['entladen'] ?> >Ent- und Zwangsladesteuerung</label>
 <label style="padding: 5px 50px" class="auswahllabel" ><input type="checkbox" name="hausakkuladung.option" id="steuer8" value="optimierung" <?php echo $Setting_check['optimierung'] ?> >Eigenverbrauchs-Optimierung</label>
 <label style="padding: 5px 50px" class="auswahllabel" ><input type="checkbox" name="hausakkuladung.option" id="steuer9" value="notstrom" <?php echo $Setting_check['notstrom'] ?> >Notstromreserve</label>
 <label style="padding: 5px 50px" class="auswahllabel" ><input type="checkbox" name="hausakkuladung.option" id="steuer10" value="dynamicprice" <?php echo $Setting_check['dynamicprice'] ?> >Dynamischer Strompreis</label>
</div>
</div>

  <script>
function disablecheckboxes() {
  var auswahl = document.querySelectorAll("input[name='hausakkuladung']");
  if (auswahl[4].checked == true){
    document.getElementById("steuer5").disabled = false;
    document.getElementById("steuer6").disabled = false;
    document.getElementById("steuer7").disabled = false;
    document.getElementById("steuer8").disabled = false;
    document.getElementById("steuer9").disabled = false;
    document.getElementById("steuer10").disabled = false;
  } else {
    document.getElementById("steuer5").checked = false;
    document.getElementById("steuer5").disabled = true;
    document.getElementById("steuer6").checked = false;
    document.getElementById("steuer6").disabled = true;
    document.getElementById("steuer7").checked = false;
    document.getElementById("steuer7").disabled = true;
    document.getElementById("steuer8").checked = false;
    document.getElementById("steuer8").disabled = true;
    document.getElementById("steuer9").checked = false;
    document.getElementById("steuer9").disabled = true;
    document.getElementById("steuer10").checked = false;
    document.getElementById("steuer10").disabled = true;
  }
}
</script>
<script>

$(document).ready(function(){

 $(document).on('click', '#import_data', function(){
  var ID = [];
  var Schluessel = [];
  var Tag_Zeit = [];
  var Res_Feld1 = [];
  var Res_Feld2 = [];
  var Options = [];
  var checkitem = "";
  const js = document.querySelectorAll('input[name="hausakkuladung"]');
  for(var i=0; i < js.length; i++){
        if(js[i].checked == true){
            js_value = js[i].value;
        }
    }
  if (js_value == "4") {
  // HIER OPTONEN ZUSAMMENBAUEN
  const checkboxes = document.getElementsByName ("hausakkuladung.option");
  var trenner = "";

   checkboxes.forEach ((item) => {
    if (item.checked === true) {
        checkitem += trenner + item.value;
        trenner = ":";
    }
   })
  }

  if (js != "") {
  ID.push("23:09");
  Schluessel.push("ProgrammStrg");
  Tag_Zeit.push("23:09");
  Res_Feld1.push(js_value);
  Res_Feld2.push(0);
  Options.push(checkitem);
  //alert (Tag_Zeit + "\n" + Res_Feld1 );
  }

  $.ajax({
   url:"SQL_speichern.php",
   method:"post",
   data:{ID:ID, Schluessel:Schluessel, Tag_Zeit:Tag_Zeit, Res_Feld1:Res_Feld1, Res_Feld2:Res_Feld2, Options:Options},
   //data:{Tag_Zeit:Tag_Zeit, Steuerung:Res_Feld1},
   success:function(data)
   {
    //alert(data);
    window.location.href = "index.php?tab=<?php echo $activeTab; ?>";

   }
  })
 });
});
</script>
