<?php
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

$logFile = __DIR__ . '/clicks.txt';
$date = date('d/m/Y');

if (!file_exists($logFile)) {
    file_put_contents($logFile, '');
}

$content = file($logFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
$found = false;

foreach ($content as $key => $line) {
    if (strpos($line, $date) === 0) {
        $parts = explode(' : ', $line);
        $count = (int)$parts[1] + 1;
        $content[$key] = "$date : $count";
        $found = true;
        break;
    }
}

if (!$found) {
    $content[] = "$date : 1";
}

file_put_contents($logFile, implode("\n", $content) . "\n");
?>