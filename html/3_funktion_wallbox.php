<?php

/**
 * Generiert den HTML-Code für den Ladebalken basierend auf den übergebenen Werten.
 * Generiert zwei Zeilen mit spezifischen Klassen:
 * 1. Obere Zeile (class="load-bar-icons") mit Emojis, die als Trennlinien dienen.
 * 2. Untere Zeile (class="load-bar-values") mit den farbigen Segmenten und Werten.
 * Lässt Zellen weg, wenn der zugehörige Wert 0 ist.
 *
 * @param float $solar Wert der Solarenergie (z.B. 8.4)
 * @param float $battery Wert der Batterieenergie (z.B. 0.4)
 * @param float $grid Wert der Netzenergie (z.B. 2.8)
 * @return string Der komplette HTML-Code des Ladebalkens (inklusive CSS)
 */
function generateLoadBar(float $solar, float $battery, float $grid): string
{
    // 1. Berechnung der Gesamtenergie und der Prozentsätze
    $total = $solar + $battery + $grid;

    if ($total === 0.0) {
        return '<p class="small">Keine Energiequelle aktiv (Total = 0)</p>';
    }

    // 2. Erstellung eines Arrays für die Daten
    $data = [
        'solar' => [
            'value' => $solar,
            'class' => 'solar',
            'label' => '☀️'
        ],
        'battery' => [
            'value' => $battery,
            'class' => 'battery',
            'label' => '🔋'
        ],
        'grid' => [
            'value' => $grid,
            'class' => 'grid',
            'label' => '🔌'
        ]
    ];

    $emoji_cells = ''; 
    $value_cells = ''; 

    // 3. Dynamische Generierung der Zellen
    foreach ($data as $item) {
        if ($item['value'] > 0) {
            $pct = ($item['value'] / $total) * 100;
            $width_style = "width: {$pct}%";
            
            // Emoji Zelle (Obere Reihe)
            $emoji_cells .= "<td style=\"{$width_style}\">{$item['label']}</td>";

            // Zelle für den Wert (Untere Reihe)
            $value_cells .= "<td class=\"{$item['class']}\" style=\"{$width_style}\">{$item['value']}</td>";
        }
    }

    // 4. Erzeugung des HTML-Strings mit den integrierten CSS-Styles
    $html = <<<HTML
    <style>

    .wrapper {
        width: 90%;
        margin: 30px 0;
        font-family: sans-serif;
    }
    
    /* ---------- BALKENTABELLE ---------- */
    .bar-table {
        width: 100%;
        border-collapse: collapse; 
    }
    
    /* Stil für die obere Emoji-Zeile */
    .load-bar-icons td {
        padding: 5px 0;
        text-align: center;
        vertical-align: middle;
        font-size: 1.2em;
        /* Senkrechte Trennlinie Emoji */
        border-left: 2px solid #999;
        border-right: 2px solid #999;
    }
    
    /* Stil für die untere Wert-Zeile */
    .load-bar-values td {
        padding: 10px;
        text-align: center;
        font-weight: 600;
    }

    /* Farbschemas */
    .solar { background: #00e639; color: black; }
    .battery { background: #48e68b; color: black; }
    .grid { background: #1e2130; color: white; }

    </style>

    <div class="wrapper">

        <table class="bar-table">
            <tr class="load-bar-icons">
                {$emoji_cells}
            </tr>
            <tr class="load-bar-values">
                {$value_cells}
            </tr>
        </table>

    </div>
    HTML;

    return $html;
}
?>
