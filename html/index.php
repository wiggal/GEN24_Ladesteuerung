<!DOCTYPE html>
<html lang="de">
<head>
<title>PV_Planung</title>
<style>
html, body {
  font-family: Arial;
  height: 100%;
  overflow: hidden;
}

/* Style the tab */
.tab {
  overflow: hidden;
  border: 1px solid #ccc;
  background-color: #f1f1f1;
}

/* Style the buttons inside the tab */
.tab button {
  background-color: inherit;
  float: left;
  border: none;
  outline: none;
  cursor: pointer;
  padding: 14px 16px;
  transition: 0.3s;
  font-size: 17px;
}

/* Change background color of buttons on hover */
.tab button:hover {
  background-color: #ddd;
}

/* Create an active/current tablink class */
.tab button.active {
  background-color: #ccc;
}

/* Style the tab content */
.tabcontent {
  display: none;
  padding: 6px 12px;
  /* border: 1px solid #ccc;*/
  height: 90%;
}
</style>
</head>
<body>

<?php
$class_tab='<div class="tab">'."\n";
$class_link='';
$files = scandir( './' );
foreach ($files as $value) {
    if (strstr($value, '_tab_')){
        $linktext_a1=explode("_tab_", $value);
        $linktext_a2=explode(".", $linktext_a1[1]);
        if($linktext_a1[0] == '1') {
            $id_default = 'id="defaultOpen"';
        } else {
            $id_default = '';
        }
        $a2_anzahl = count($linktext_a2)-1;
        if ($linktext_a2[$a2_anzahl] == 'php' OR $linktext_a2[$a2_anzahl] == 'html') {
            $class_tab .= '<button class="tablinks" onclick="openCity(event,\''.$linktext_a2[0].'\')" '.$id_default.'>'.$linktext_a2[0].'</button>'."\n";
            $class_link .= '<div id="'.$linktext_a2[0].'" class="tabcontent"> <iframe src="'.$value.'" style="border:none;" height="100%" width="100%" title="description"></iframe> </div>'."\n";
        }
    }
}
$class_tab .= '</div>';
echo $class_tab;
echo $class_link;
?>

<script>
function openCity(evt, cityName) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  document.getElementById(cityName).style.display = "block";
  evt.currentTarget.className += " active";
}

// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click();
</script>
   
</body>
</html> 

