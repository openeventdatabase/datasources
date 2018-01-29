# Ecrit par Christian Quest le 1/6/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

import requests
import sys
import re
import json
import time

with open('vigicrue-stations.geojson') as json_file:
    data = json.load(json_file)
    for s in data['features']:
        url = 'https://www.vigicrues.gouv.fr/services/observations.json/index.php?FormatDate=iso&CdStationHydro='+s['properties']['id']
        # données des hauteurs d'eau
        hauteurs=requests.get(url+'&typegraphe=h').content.decode('utf-8')
        mesures = json.loads(hauteurs)
        if 'Serie' in mesures:
            nom_station = mesures['Serie']['LbStationHydro']
            mm = mesures['Serie']['ObssHydro']
            #print(s['properties']['id'], nom_station)
            for i in range(1,len(mm)):
                m = mm[len(mm)-i]
                when = m['DtObsHydro']
                geojson = json.dumps(dict(type='Feature',properties=dict(source='http://www.vigicrues.gouv.fr/', type='observed', what='water.level', when=when, hauteur=m['ResObsHydro'], id_station=s['properties']['id'], label=nom_station+" : "+str(m['ResObsHydro'])+"m"), geometry=s['geometry']))
                # envoi à l'API OpenEventDatabase
                #print(geojson)
                r = requests.post('http://localhost:8000/event', data = geojson)
                if r.status_code != 201:
                    break
