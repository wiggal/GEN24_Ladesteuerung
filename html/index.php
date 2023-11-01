<!DOCTYPE html>
<html lang="de">
<head>
<title>PV_Planung</title>
<style>
/**
 * Tabs
 */
.tabs {
    position:fixed; top:0px; width:100%;
	display: flex;
	flex-wrap: wrap; // make sure it wraps
    overflow: hidden;
}
.tabs label {
	order: 1; // Put the labels first
	display: block;
	padding: 15px 7px;
	*margin-right: 0.2rem;
	margin-right: 0.2%;
	cursor: pointer;
    background: #90CAF9;
    font-weight: bold;
    font-size: 17px;
    white-space: nowrap;
    text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background ease 0.2s;
}
.tabs .tab {
  order: 99; // Put the tabs last
  flex-grow: 1;
	width: 100%;
    height: 88dvh;
	display: none;
  padding: 1rem;
  background: #fff;
}
.tabs input[type="radio"] {
	display: none;
}
.tabs input[type="radio"]:checked + label {
	background: #fff;
}
.tabs input[type="radio"]:checked + label + .tab {
	display: block;
}

@media (max-width: 85em) {
  .tabs label {
    margin-right: 0;
    font-size: 20px;
  }
}

/**
 * Generic Styling
*/
body {
  background: #eee;
  min-height: 100vh;
	box-sizing: border-box;
	padding-top: 1vh;
  font-family: "HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif;
  font-weight: 300;
  line-height: 1.5;
  * max-width: 60rem;
  margin: 0 auto;
  font-size: 112%;
  overflow: hidden;
}


</style>
</head>
<body>
<div class="tabs">

<?php
#$class_tab='<div class="tab">'."\n";
$class_link='';
$files = scandir( './' );
# Breite der Tabs in % rechnen
$anzahl_tabs =0;
foreach ($files as $value) {
    if (strstr($value, '_tab_')){
        $anzahl_tabs += 1;
    }
}
$Tab_Proz = floor((100-($anzahl_tabs*2))/$anzahl_tabs);
foreach ($files as $value) {
    if (strstr($value, '_tab_')){
        $linktext_a1=explode("_tab_", $value);
        $linktext_a2=explode(".", $linktext_a1[1]);
        if($linktext_a1[0] == '1') {
            $id_default = ' checked="checked"';
        } else {
            $id_default = '';
        }
        $a2_anzahl = count($linktext_a2)-1;
        if ($linktext_a2[$a2_anzahl] == 'php' OR $linktext_a2[$a2_anzahl] == 'html') {
            $class_tab .= '<input type="radio" name="tabs" id="'.$linktext_a2[0].'"'.$id_default.'>'."\n";
            $class_tab .= '<label style="width: '.$Tab_Proz.'vw;" for="'.$linktext_a2[0].'">'.$linktext_a2[0].'</label>'."\n";
            $class_tab .= '<div class="tab"><iframe src="'.$value.'" style="border:none;" height="100%" width="100%"></iframe></div>'."\n";
        }
    }
}
$class_tab .= '</div>';
echo $class_tab;
?>
</body>
</html>

