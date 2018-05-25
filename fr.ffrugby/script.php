<?php

define('API_URL', 'http://api.openeventdatabase.org');
define('DB_FILE', 'oedb_fr_ffrugby.sqlite');
define('DEBUG', true);


/**
 * @return array[]
 */
function crawlAllComite()
{
    $url = 'https://competitions.ffr.fr/api/v1/navigation';
    $contents = file_get_contents($url);
    $contents = json_decode($contents, true);
    $arrReturn = array();
    foreach ($contents as $comite => $arrComite) {
        if ($comite == 'FFR') {
            $arrReturn[$comite] = crawlComite($arrComite);
        } else {
            foreach ($arrComite as $subArrComite) {
                $arrReturn[$comite . ' > ' . $subArrComite['nom']] = crawlComite($subArrComite);
            }
        }
    }
    return $arrReturn;
}

/**
 * @param array $arrComite
 * @return array
 */
function crawlComite(array $arrComite)
{
    $arrReturn = array();
    foreach ($arrComite['categories'] as $arrCategory) {
        $arrReturn[$arrCategory['nom']] = array();
        foreach ($arrCategory['competitions'] as $arrCompetition) {
            $arrReturn[$arrCategory['nom']][$arrCompetition['identifiant']] = $arrCompetition['nom'];
        }
    }
    return $arrReturn;
}

/**
 * @param string $competition
 * @param SQLite3 $oDB
 * @return Generator
 */
function crawlCompetition($competition, $oDB)
{
    $url = 'https://competitions.ffr.fr/api/v1/competition/' . $competition;
    $contents = file_get_contents($url);
    $contents = json_decode($contents, true);
    var_dump($url);

    foreach ($contents['competitions_phases'] as $phase) {
        $urlDay = $url . '/journees?phase=' . $phase['id'];
        $contentsPhase = file_get_contents($urlDay);
        $contentsPhase = json_decode($contentsPhase, true);
        var_dump($urlDay);
        foreach ($contentsPhase as $journee) {
            foreach ($journee['poules'] as $poule) {
                foreach ($poule['rencontres'] as $rencontre) {
                    $result = $oDB->query('SELECT * FROM oedb_ffrugby_rencontre WHERE ffrugby_rencontre_id = "'.$rencontre['id'].'";');
                    $result = $result->fetchArray(SQLITE3_ASSOC);
                    if ($result !== false) {
                        continue;
                    }

                    $urlRencontre = 'https://competitions.ffr.fr/api/v1/rencontre/' . $rencontre['id'];
                    $contentsRencontre = file_get_contents($urlRencontre);
                    $contentsRencontre = json_decode($contentsRencontre, true);
                    if ($contentsRencontre['statut'] == 'en instance') {
                        continue;
                    }
                    if ($contentsRencontre['statut'] != 'score valide'
                        && $contentsRencontre['statut'] != 'planifiee'
                        && $contentsRencontre['statut'] != 'presaisie'
                        && $contentsRencontre['statut'] != 'perequation') {
                        var_dump($urlRencontre);
                        var_dump($contentsRencontre);
                        die();
                    }
                    $arrayReturn = array(
                        'type' => 'Feature',
                        'geometry' => array(
                            'coordinates' => array(
                                $contentsRencontre['terrain']['lng'],
                                $contentsRencontre['terrain']['lat'],
                            ),
                            'type' => 'Point'
                        ),
                        'properties' => array(
                            'what' => 'sport.rugby.competition',
                            'type' => 'scheduled',
                            'when' => $contentsRencontre['date'],
                            'source' => 'https://competitions.ffr.fr/competitions/' . $competition . '/match-' . $rencontre['id'] . '.html',
                            'label' => 'Match : ' . $contentsRencontre['local_structure']['nom'] . ' - ' . $contentsRencontre['visitor_structure']['nom'],
                            'competition:nom' => $contentsRencontre['competition']['nom'],
                            'competition:journee' => $contentsRencontre['competitions_journee']['nom'],
                            'competition:score' => $contentsRencontre['score_structure_locale'] . ' - ' . $contentsRencontre['score_structure_visiteur'],
                            'competition:rencontre:id' => $rencontre['id'],
                            'where:name' => $contentsRencontre['terrain']['nom'] . ' à ' . $contentsRencontre['terrain']['ville'],
                        )
                    );
                    var_dump('https://competitions.ffr.fr/competitions/' . $competition . '/match-' . $rencontre['id'] . '.html');
                    $headers = get_headers('https://competitions.ffr.fr/competitions/' . $competition . '/match-' . $rencontre['id'] . '.html', 1);
                    if ($headers[0] != 'HTTP/1.1 200 OK') {
                        var_dump($urlRencontre);
                        var_dump($contentsRencontre);
                        die();
                    }
                    yield $arrayReturn;
                }
            }
        }
    }
}

/**
 * @return SQLite3
 */
function initDatabase()
{
    $oSQLite = new SQLite3(DB_FILE);
    $oSQLite->query('CREATE TABLE IF NOT EXISTS oedb_ffrugby_rencontre(oedb_id TEXT, ffrugby_rencontre_id TEXT)');
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
        var_dump($data);
        var_dump($result);
        die();
    }
    return $resultJson;
}

$oDB = initDatabase();
$numAdded = $numEverExists = 0;
$arrayAllComite = crawlAllComite();
foreach ($arrayAllComite as $comite => $arrComite) {
    var_dump($comite);
    foreach ($arrComite as $category => $itemChampionship) {
        var_dump($category);
        foreach ($itemChampionship as $key => $value) {
            var_dump($key);
            var_dump($value);
            foreach (crawlCompetition($key, $oDB) as $data) {
                $data['properties']['competition:authority'] = $comite;
                $data['properties']['competition:championship'] = $category;
                $id = $data['properties']['competition:rencontre:id'];
                $result = fnPostOED($data);
                $idOED = null;
                if (DEBUG) {
                    var_dump($data);
                    var_dump($result);
                }
                if (isset($result['id'])) {
                    if ($result['id'] == 'None') {
                        die();
                    }
                    $numAdded++;
                    $idOED = $result['id'];
                    echo 'The competition has been added : '.API_URL.'/event/'.$result['id']. ' ('.$data['properties']['source'].')'.PHP_EOL;
                }
                if (isset($result['duplicate'])) {
                    if ($result['duplicate'] == 'None') {
                        die();
                    }
                    $numEverExists++;
                    $idOED = $result['duplicate'];
                    echo 'The competition ever exists : '.API_URL.'/event/'.$result['duplicate']. ' ('.$data['properties']['source'].')'.PHP_EOL;
                }
                $oDB->query('INSERT INTO oedb_ffrugby_rencontre VALUES ("'.$idOED.'","'.$id.'");');
            }
        }
    }
}

echo PHP_EOL . 'Ajouts : ' . $numAdded . ' - Duplications : ' . $numEverExists . PHP_EOL;
