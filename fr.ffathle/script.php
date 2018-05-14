<?php

define('API_URL', 'http://api.openeventdatabase.org');

$fromDate = $argv[1]; // Format MySQL 2018-05-13
$toDate = isset($argv[2]) ? $argv[2] : $argv[1];

/**
 * @param string $fromDate
 * @param string $toDate
 * @return string[]
 */
function crawlList($fromDate, $toDate)
{
    $fromDate = explode('-', $fromDate);
    $fromDate = array_map(function($v){
        return ltrim($v, '0');
    }, $fromDate);
    $toDate = explode('-', $toDate);
    $toDate = array_map(function($v){
        return ltrim($v, '0');
    }, $toDate);

    $url = 'http://bases.athle.com/asp.net/liste.aspx?frmpostback=true&frmbase=calendrier&frmmode=1&frmtri=D&frmespace=0'
        .'&frmdate_j1='.$fromDate[2].'&Frmdate_m1='.$fromDate[1].'&frmdate_a1='.$fromDate[0]
        .'&frmdate_j2='.$toDate[2].'&frmdate_m2='.$toDate[1].'&frmdate_a2='.$toDate[0];

    $contents = file_get_contents($url);
    preg_match_all('#javascript:bddThrowCompet\(\'([0-9]+)\', 0\)#', $contents, $matches);
    return $matches[1];
}

/**
 * @param int $idCompetition
 * @return string[]|null
 */
function crawlCompetition($idCompetition)
{
    $url = 'http://bases.athle.com/asp.net/competitions.aspx?base=calendrier&id='.$idCompetition;
    $contents = file_get_contents($url);
    if (strpos($contents, 'L\'enregistrement demand&#233; n\'existe pas') !== false) {
        return null;
    }

    $arrayReturn = array(
        'type' => 'Feature',
        'geometry' => array(
            'coordinates' => array(),
            'type' => 'Point'
        ),
        'properties' => array(
            'what' => 'sport.athletics',
            'type' => 'forecast',
            'start' => null, // ISO6801
            'stop' => null, // ISO6801
            'source' => $url,
            'label' => null,
            'competition:id' => $idCompetition,
            'competition:level' => null,
            'competition:type' => null,
            'where:name' => null,
        )
    );

    $fromDate = $toDate = null;

    // Date de début
    preg_match('#<td>Date de Début : <b><span style="color:\#A00014">([0-9/]+)</span></b></td>#', $contents, $matches);
    if(!empty($matches[1])) {
        $fromDate = explode('/', $matches[1]);
    }
    $oDT = new \DateTime();
    $oDT->setDate($fromDate[2], $fromDate[1], $fromDate[0]);
    $oDT->setTime(0,0,0,0);
    $arrayReturn['properties']['start'] = $oDT->format(DATE_ISO8601);

    // Date de fin
    preg_match('#<td>Date de Fin : <b>([0-9/]+)</b></td>#', $contents, $matches);
    if(!empty($matches[1])) {
        $toDate = explode('/', $matches[1]);
    }
    if (empty($toDate)) {
        $toDate = $fromDate;
    }
    $oDT = new \DateTime();
    $oDT->setDate($toDate[2], $toDate[1], $toDate[0]);
    $oDT->setTime(23,59,59,0);
    $arrayReturn['properties']['stop'] = $oDT->format(DATE_ISO8601);

    // Compétition : Niveau
    preg_match('#<td style="text-align:right">Niveau : <b>([A-Za-zéè\s\-\/]+)</b></td>#', $contents, $matches);
    if (!empty($matches[1])) {
        $arrayReturn['properties']['competition:level'] = $matches[1];
    }

    // Compétition : Type
    preg_match('#<td style="text-align:right">Type : <b>([A-Za-zéè\s\-\/]+)</b></td>#', $contents, $matches);
    if (!empty($matches[1])) {
        $arrayReturn['properties']['competition:type'] = $matches[1];
    }

    // Compétition : Nom
    preg_match('#<div class="titles" style="background:url\(\'\/images\/v3\/pic.performance.png\'\) no-repeat; margin-bottom:10px; padding-left:70px">[\s]+([A-Za-zéè0-9\-\s\'\(\)]+)#m', $contents, $matches);
    if (!empty($matches[1])) {
        $arrayReturn['properties']['label'] = trim($matches[1]);
    }

    // Compétition : Lieu
    preg_match('#<span style="color:\#000; font-size:15px">([A-Za-z0-9\'\-\(\)\s\\\/]+)</span>#', $contents, $matches);
    if (!empty($matches[1])) {
        $matches[1] = trim($matches[1]);
        $competitionLocation = $matches[1];
        $competitionLocation = explode('(', $competitionLocation);
        $competitionLocation = array_map(function($v){
            return rtrim(trim($v), ')');
        }, $competitionLocation);
        if (strpos($competitionLocation[1], '/') === false) {
            // Hors France
            $apiGoogle = 'https://nominatim.openstreetmap.org/search?format=json&q='.urlencode($matches[1]);
            $data = file_get_contents($apiGoogle);
            $data = json_decode($data, true);
            if (empty($data)) {
//                var_dump(__LINE__);
//                var_dump($data);
//                die();
                return null;
            }
            $data = reset($data);
            $arrayReturn['geometry']['coordinates'] = array(
                $data['lon'],
                $data['lat'],
            );
            $arrayReturn['properties']['where:name'] = $matches[1];
        } else {
            // France
            $dptCode = explode('/', $competitionLocation[1]);
            $dptCode = substr(trim($dptCode[1]), -2);
            // API
            $apiBAN = 'https://api-adresse.data.gouv.fr/search/?type=municipality&q='.urlencode($competitionLocation[0]);
            $data = file_get_contents($apiBAN);
            $data = json_decode($data, true);
            $featureFound = null;
            foreach ($data['features'] as $feature) {
                if (substr($feature['properties']['id'], 0, 2) == $dptCode) {
                    $featureFound = $feature;
                }
            }
            if (is_null($featureFound)) {
//                var_dump(__LINE__);
//                var_dump($data);
//                die();
                return null;
            }
            $arrayReturn['geometry'] = $featureFound['geometry'];
            $arrayReturn['properties']['where:insee'] = $featureFound['properties']['id'];
            $arrayReturn['properties']['where:name'] = $competitionLocation[0] . ' ('.$dptCode.')';
        }
    }

    return $arrayReturn;
}

$arrayIdCompetition = crawlList($fromDate, $toDate);
foreach ($arrayIdCompetition as $id) {
    $data = crawlCompetition($id);
    if (is_array($data)) {
        $data_string = json_encode($data);

        $ch = curl_init();
        curl_setopt($ch,CURLOPT_URL, API_URL.'/event');
        curl_setopt($ch,CURLOPT_POST, count($data));
        curl_setopt($ch,CURLOPT_POSTFIELDS, $data_string);
        $result = curl_exec($ch);
        curl_close($ch);
//        var_dump($data);
//        var_dump($result);
    }
}
