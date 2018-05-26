<?php

define('API_URL', 'http://api.openeventdatabase.org');
define('DB_FILE', 'oedb_fr_missioncentenaire.sqlite');
define('DEBUG', false);


/**
 * @return array[]
 */
function crawlEvent()
{
    $url = 'http://centenaire.org/fr/agenda?agendaType=public&dateStart=1388530800&dateEnd=1546210800&from=1/1/2014&to=31/12/2018&filterRegion=world';
    $contents = file_get_contents($url);

    $startHtml = '<span class="print-link"></span><div class="agenda-datas">';
    $endHtml = '<div class="ct-agenda-public">';
    $contents = substr($contents, strpos($contents, $startHtml) + strlen($startHtml));
    $contents = substr($contents, 0, strpos($contents, $endHtml));
    $contents = trim($contents);
    preg_match_all('#data-nid="([0-9]+)"#', $contents,$matchesId);
    preg_match_all('#data-latitude="([0-9\.\- ]+)"#', $contents,$matchesLat);
    preg_match_all('#data-longitude="([0-9\.\- ]+)"#', $contents,$matchesLon);
    return array(
        $matchesId[1],
        $matchesLat[1],
        $matchesLon[1],
    );
}

/**
 * @param int $id
 * @param string $lat
 * @param string $lon
 * @return array
 */
function crawlEventId($id, $lat, $lon)
{
    $url = 'http://centenaire.org/fr/event-agenda-infos/'.$id;
    $contents = file_get_contents($url);

    $dtOne = fnExtractDate($contents);
    $dtStart = fnExtractDateStart($contents);
    $dtEnd = fnExtractDateEnd($contents);
    $titre = fnExtractTitle($contents);
    $content = fnExtractText($contents);
    $where = fnExtractWhere($contents);
    $website = fnExtractWebsite($contents);

    if (!is_object($dtOne) && !is_object($dtStart) && !is_object($dtEnd)) {
        var_dump(__LINE__);
        var_dump($contents);
        die();
    }

    $arrayReturn = array(
        'type' => 'Feature',
        'geometry' => array(
            'coordinates' => array(
                $lon,
                $lat,
            ),
            'type' => 'Point'
        ),
        'properties' => array(
            'what' => 'culture.history',
            'type' => 'scheduled',
            'source' => 'http://centenaire.org/fr/agenda?agendaType=public&dateStart=1388530800&dateEnd=1546210800&from=1/1/2014&to=31/12/2018&filterRegion=world#4992',
            'label' => $titre,
            'event:id' => $id,
            'event:description' => $content,
            'event:url' => $website,
            'where:address' => $where,
        )
    );

    if (is_object($dtOne)) {
        $arrayReturn['properties']['when'] = $dtOne->format(DATE_ISO8601);
    } else {
        $arrayReturn['properties']['start'] = $dtStart->format(DATE_ISO8601);
        $arrayReturn['properties']['end'] = $dtEnd->format(DATE_ISO8601);
    }

    return $arrayReturn;
}

/**
 * @param $string
 * @return int
 */
function fnConvertMonth($string) {
    switch ($string) {
        case 'Jan':
            $month = 1;
            break;
        case 'F&eacute;v':
            $month = 2;
            break;
        case 'Mar':
            $month = 3;
            break;
        case 'Avr':
            $month = 4;
            break;
        case 'Mai':
            $month = 5;
            break;
        case 'Jun':
            $month = 6;
            break;
        case 'Jul':
            $month = 7;
            break;
        case 'Ao&ucirc;':
            $month = 8;
            break;
        case 'Sep':
            $month = 9;
            break;
        case 'Oct':
            $month = 10;
            break;
        case 'Nov':
            $month = 11;
            break;
        case 'D&eacute;c':
            $month = 12;
            break;
        default:
            var_dump(__LINE__);
            var_dump($string);
            die();
    }

    return $month;
}

/**
 * @param string $data
 * @return DateTime|null
 */
function fnExtractDate($data) {
    $startHtml = '<div class="event-date">';
    $endHtml = '</div>';
    $pos = strpos($data, $startHtml);
    if ($pos === false) {
        return null;
    }
    $data = substr($data, $pos + strlen($startHtml));
    $data = substr($data, 0,strpos($data, $endHtml));
    $data = trim($data);

    preg_match('#<span class="event-day">([0-9]+)</span>#', $data, $day);
    preg_match('#<span class="event-month">([A-Za-z&;]+)</span>#', $data, $month);
    preg_match('#<span class="event-year">([0-9]+)</span>#', $data, $year);

    $oDT = new \DateTime();
    $oDT->setDate($year[1], fnConvertMonth($month[1]), $year[1]);
    $oDT->setTime(0, 0, 0);
    return $oDT;
}

/**
 * @param string $data
 * @return DateTime|null
 */
function fnExtractDateStart($data) {
    $startHtml = '<div class="event-date begin">';
    $endHtml = '</div>';
    $pos = strpos($data, $startHtml);
    if ($pos === false) {
        return null;
    }
    $data = substr($data, $pos + strlen($startHtml));
    $data = substr($data, 0,strpos($data, $endHtml));
    $data = trim($data);

    preg_match('#<span class="event-day">([0-9]+)</span>#', $data, $day);
    preg_match('#<span class="event-month">([A-Za-z&;]+)</span>#', $data, $month);
    preg_match('#<span class="event-year">([0-9]+)</span>#', $data, $year);

    $oDT = new \DateTime();
    $oDT->setDate($year[1], fnConvertMonth($month[1]), $year[1]);
    $oDT->setTime(0, 0, 0);
    return $oDT;
}

/**
 * @param string $data
 * @return DateTime|null
 */
function fnExtractDateEnd($data) {
    $startHtml = '<div class="event-date end">';
    $endHtml = '</div>';
    $pos = strpos($data, $startHtml);
    if ($pos === false) {
        return null;
    }
    $data = substr($data, $pos + strlen($startHtml));
    $data = substr($data, 0,strpos($data, $endHtml));
    $data = trim($data);

    preg_match('#<span class="event-day">([0-9]+)</span>#', $data, $day);
    preg_match('#<span class="event-month">([A-Za-z&;]+)</span>#', $data, $month);
    preg_match('#<span class="event-year">([0-9]+)</span>#', $data, $year);

    $oDT = new \DateTime();
    $oDT->setDate($year[1], fnConvertMonth($month[1]), $year[1]);
    $oDT->setTime(23, 59, 59);
    return $oDT;
}

/**
 * @param string
 * @return bool|null|string
 */
function fnExtractTitle($data) {
    $startHtml = '<h4 class="event-title">';
    $endHtml = '</h4>';
    $pos = strpos($data, $startHtml);
    if ($pos === false) {
        return null;
    }
    $data = substr($data, $pos + strlen($startHtml));
    $data = substr($data, 0,strpos($data, $endHtml));
    $data = trim($data);
    return $data;
}

/**
 * @param string
 * @return bool|null|string
 */
function fnExtractText($data) {
    $startHtml = '<p class="event-text">';
    $endHtml = '</p>';
    $pos = strpos($data, $startHtml);
    if ($pos === false) {
        return null;
    }
    $data = substr($data, $pos + strlen($startHtml));
    $data = substr($data, 0,strpos($data, $endHtml));
    $data = trim($data);
    return $data;
}

/**
 * @param string
 * @return bool|null|string
 */
function fnExtractWhere($data) {
    $startHtml = '<div class="event-label">Adresse(s)</div>';
    $endHtml = '</div>';
    $pos = strpos($data, $startHtml);
    if ($pos === false) {
        return null;
    }
    $data = substr($data, $pos + strlen($startHtml));
    $data = substr($data, 0,strpos($data, $endHtml));
    $data = strip_tags($data);
    $data = trim($data);
    return $data;
}

/**
 * @param string
 * @return bool|null|string
 */
function fnExtractWebsite($data) {
    $startHtml = '<div class="event-info event-info-website">';
    $endHtml = '</a>';
    $pos = strpos($data, $startHtml);
    if ($pos === false) {
        return null;
    }
    $data = substr($data, $pos + strlen($startHtml));
    $data = substr($data, 0,strpos($data, $endHtml));
    $data = trim($data);

    $startHtml = '<a target="_blank" href="';
    $pos = strpos($data, $startHtml);
    if ($pos === false) {
        return null;
    }
    $dataInit = $data;
    $data = substr($data, $pos + strlen($startHtml));
    $endHtml = '" class="go-to-event">';
    $posEnd = strpos($data, $endHtml);
    if ($posEnd == false) {
        $endHtml = '">';
        $posEnd = strpos($data, $endHtml);
    }
    $data = substr($data, 0, $posEnd);
    $data = trim($data);
    if (empty($data)) {
        var_dump(__LINE__);
        var_dump($dataInit);
        die();
    }
    return $data;
}

/**
 * @return SQLite3
 */
function initDatabase()
{
    $oSQLite = new SQLite3(DB_FILE);
    $oSQLite->query('CREATE TABLE IF NOT EXISTS oedb_missioncentenaire_event(oedb_id TEXT, missioncentenaire_event_id TEXT)');
    return $oSQLite;
}

/**
 * @param array $data
 * @return array|null
 */
function fnPostOED($data) {
    if (!is_array($data)) {
        return null;
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
    $resultJson = json_decode($result, true);
    if (json_last_error() != JSON_ERROR_NONE) {
        var_dump(__LINE__);
        var_dump($data);
        var_dump($result);
        die();
    }
    return $resultJson;
}

$oDB = initDatabase();
$numAdded = $numEverExists = 0;
list($arrayEventId, $arrayEventLat, $arrayEventLon) = crawlEvent();
foreach ($arrayEventId as $key => $eventId) {
    $data = crawlEventId($eventId, trim($arrayEventLat[$key]), trim($arrayEventLon[$key]));

    $result = $oDB->query('SELECT * FROM oedb_missioncentenaire_event WHERE missioncentenaire_event_id = "'.$eventId.'";');
    $result = $result->fetchArray(SQLITE3_ASSOC);
    if ($result !== false) {
        continue;
    }
    $result = fnPostOED($data);
    $idOED = null;
    if (DEBUG) {
        var_dump(__LINE__);
        var_dump($data);
        var_dump($result);
    }
    if (isset($result['id'])) {
        if ($result['id'] == 'None') {
            die();
        }
        $numAdded++;
        $idOED = $result['id'];
        echo 'The competition has been added : '.API_URL.'/event/'.$result['id']. ' (http://centenaire.org/fr/event-agenda-infos/'.$eventId.')'.PHP_EOL;
    }
    if (isset($result['duplicate'])) {
        if ($result['duplicate'] == 'None') {
            die();
        }
        $numEverExists++;
        $idOED = $result['duplicate'];
        echo 'The competition ever exists : '.API_URL.'/event/'.$result['duplicate']. ' (http://centenaire.org/fr/event-agenda-infos/'.$eventId.')'.PHP_EOL;
    }
    $oDB->query('INSERT INTO oedb_missioncentenaire_event VALUES ("'.$idOED.'","'.$eventId.'");');
}

echo PHP_EOL . 'Ajouts : ' . $numAdded . ' - Duplications : ' . $numEverExists . PHP_EOL;
