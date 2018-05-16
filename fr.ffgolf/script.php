<?php

define('API_URL', 'http://api.openeventdatabase.org');
define('DEBUG', false);


/**
 * @return array[]
 */
function crawlList()
{
    $url = 'https://guidegolfs.ffgolf.org/fcapi/golfs/calendrier?contexte=calendrier';
    $contents = file_get_contents($url);
    $contents = json_decode($contents, true);
    return $contents;
}

/**
 * @param array $properties
 * @return string[]|null
 */
function crawlGolf($properties)
{
    $date = explode(' ', $properties['date']);
    if (!is_array($date) || count($date) != 3) {
        return null;
    }
    switch (strtolower($date[1])) {
        case 'janvier':
            $date[1] = 1;
            break;
        case 'fevrier':
            $date[1] = 2;
            break;
        case 'mars':
            $date[1] = 3;
            break;
        case 'avril':
            $date[1] = 4;
            break;
        case 'mai':
            $date[1] = 5;
            break;
        case 'juin':
            $date[1] = 6;
            break;
        case 'juillet':
            $date[1] = 7;
            break;
        case 'aout':
            $date[1] = 8;
            break;
        case 'septembre':
            $date[1] = 9;
            break;
        case 'octobre':
            $date[1] = 10;
            break;
        case 'novembre':
            $date[1] = 11;
            break;
        case 'decembre':
            $date[1] = 12;
            break;
    }
    if (!is_int($date[1])) {
        return null;
    }
    if ($date[2] > (date('Y') + 1)) {
        return null;
    }

    $oDT = new \DateTime();
    $oDT->setDate($date[2], $date[1], $date[0]);

    $fromDate = $oDT->setTime(0, 0, 0)->format(DATE_ISO8601); // ISO6801
    $toDate = $oDT->setTime(23, 59, 59)->format(DATE_ISO8601); // ISO6801

    $arrayReturn = array(
        'type' => 'Feature',
        'geometry' => array(
            'coordinates' => array(
                $properties['coordonneesGps']['longitude'],
                $properties['coordonneesGps']['latitude'],
            ),
            'type' => 'Point'
        ),
        'properties' => array(
            'what' => 'sport.golf.competition',
            'type' => 'scheduled',
            'start' => $fromDate,
            'stop' => $toDate,
            'source' => 'https://www.ffgolf.org/Jouer/Messieurs-Dames/Competitions-de-clubs/Calendrier',
            'label' => $properties['competition'],
            'competition:formula' => $properties['formule'],
            'competition:type' => $properties['type'],
            'competition:numHoles' => $properties['nombreTrou'],
            'where:name' => $properties['libelle'],
        )
    );

    return $arrayReturn;
}

$arrayList = crawlList();
$numAdded = $numEverExists = 0;
foreach ($arrayList as $propsGolf) {
    $data = crawlGolf($propsGolf);
    if (!is_array($data)) {
        continue;
    }
    $data_string = json_encode($data);

    $hCurl = curl_init();
    curl_setopt_array($hCurl, array(
        CURLOPT_URL => API_URL . '/event',
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => count($data),
        CURLOPT_POSTFIELDS => $data_string,
        CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
    ));
    $result = curl_exec($hCurl);
    curl_close($hCurl);
    $result = json_decode($result, true);
    if (isset($result['id'])) {
        $numAdded++;
        echo 'The competition has been added : '.API_URL.'/event/'.$result['id']. ' ('.$propsGolf['competition'] . ' - '.$propsGolf['libelle'].' à '.$propsGolf['ville'].')'.PHP_EOL;
    }
    if (isset($result['duplicate'])) {
        $numEverExists++;
        echo 'The competition ever exists : '.API_URL.'/event/'.$result['duplicate']. ' ('.$propsGolf['competition'] . ' - '.$propsGolf['libelle'].' à '.$propsGolf['ville'].')'.PHP_EOL;
    }
    if (DEBUG) {
        var_dump($data);
        var_dump($result);
    }
}
echo PHP_EOL. 'Ajouts : '.$numAdded.' - Duplications : '.$numEverExists.PHP_EOL;
