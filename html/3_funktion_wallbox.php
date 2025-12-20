<?php
/**
 * Generiert den HTML-Code für den Ladebalken basierend auf den übergebenen Werten.
 */
function generateLoadBar(float $solar, float $battery, float $grid, float $in_auto, float $in_haus): string
{
    // 1. Berechnung der Energiewerte
    $aus_battery = max(0.0, $battery);
    $aus_grid = max(0.0, $grid);
    $total = $solar + $aus_battery + $aus_grid;

    $in_battery = max(0.0, -$battery);
    $in_grid = max(0.0, -$grid);



    if ($total === 0.0) {
        #return '<p class="small">Keine Energiequelle aktiv (Total = 0)</p>';
        return '';
    }

    // 2. Erstellung eines Arrays für die Daten der Quellen
    $data_quelle = [
        'solar' => [
            'value' => $solar,
            'class' => 'solar',
            'label' => '☀️'
        ],
        'battery' => [
            'value' => $aus_battery,
            'class' => 'aus_battery',
            'label' => '🪫'
        ],
        'grid' => [
            'value' => $aus_grid,
            'class' => 'aus_grid',
            'label' => '⬇️'
        ]
    ];

    // 3. Erstellung eines Arrays für die Daten Ziele
    $data_ziel = [
        'haus' => [
            'value' => $in_haus,
            'class' => 'in_haus',
            'label' => '🏠'
        ],
        'auto' => [
            'value' => $in_auto,
            'class' => 'in_auto',
            'label' => '🚘'
        ],
        'battery' => [
            'value' => $in_battery,
            'class' => 'in_battery',
            'label' => '🔋'
        ],
        'grid' => [
            'value' => $in_grid,
            'class' => 'in_grid',
            'label' => '⬆️'
        ]
    ];

    $quelle_emoji_cells = ''; 
    $quelle_value_cells = ''; 
    $ziel_emoji_cells = ''; 
    $ziel_value_cells = ''; 

    // 3. Dynamische Generierung der Zellen Quelle
    foreach ($data_quelle as $item) {
        if ($item['value'] >= 0.1) {
            $pct = ($item['value'] / $total) * 100;
            $width_style = "width: {$pct}%";
            
            // Emoji Zelle (Obere Reihe)
            $quelle_emoji_cells .= "<td style=\"{$width_style}\">{$item['label']}</td>";

            // Zelle für den Wert (Untere Reihe)
            $quelle_value_cells .= "<td class=\"{$item['class']}\" style=\"{$width_style}\">{$item['value']}</td>";
        }
    }

    // 4. Dynamische Generierung der Zellen Ziel
    foreach ($data_ziel as $item) {
        if ($item['value'] >= 0.1) {
            $pct = ($item['value'] / $total) * 100;
            $width_style = "width: {$pct}%";
            
            // Emoji Zelle (Obere Reihe)
            $ziel_emoji_cells .= "<td style=\"{$width_style}\">{$item['label']}</td>";

            // Zelle für den Wert (Untere Reihe)
            $ziel_value_cells .= "<td class=\"{$item['class']}\" style=\"{$width_style}\">{$item['value']}</td>";
        }
    }


    // 4. Erzeugung des HTML-Strings mit den integrierten CSS-Styles
    $html = <<<HTML
    <div class="wrapper">

        <table class="bar-table">
            <tr class="load-bar-icons">
                {$quelle_emoji_cells}
            </tr>
            <tr class="load-bar-values">
                {$quelle_value_cells}
            </tr>
        </table>

        <table class="bar-table">
            <tr class="load-bar-values">
                {$ziel_value_cells}
            </tr>
            <tr class="load-bar-icons">
                {$ziel_emoji_cells}
            </tr>
        </table>
    </div>
    HTML;

    return $html;
}
?>
