# Ecrit par Christian Quest le 23/11/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

import requests
import sys
import json
import re
import sqlite3

# adresse de l'API
api ='http://api.openeventdatabase.org'

# base sqlite pour suivre l'évolution des événements d'un run au suivant
sql = sqlite3.connect(sys.argv[2])
db = sql.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS events (id text, what text,
  start text, geom text, label text, stop text)''')

# récupération de la date dans le nom du fichier
e_when=sys.argv[1][-26:]
e_when=e_when[:21]

with open(sys.argv[1]) as json_file:
    events = json.load(json_file)
    for ev in events['features']:
        # fermetures de routes (block, closures)
        if 'FULLCLOSE' in ev['properties']:
            ev['properties']['what'] = 'traffic.closed'
            if ev['properties']['FULLCLOSE'] != 'Yes':
                ev['properties']['what'] = 'traffic.partially_closed'
            if ev['properties']['STARTDATE'] < ev['properties']['ENDDATE']:
                ev['properties']['start'] = ev['properties']['STARTDATE']
                ev['properties']['stop'] = ev['properties']['ENDDATE']
            else:
                ev['properties']['when'] = ev['properties']['STARTDATE']
            ev['properties']['type'] = 'scheduled'
            ev['properties']['label'] = ev['properties']['BLOCKNM']
            if ev['properties']['label'] is None:
                ev['properties']['label'] = ev['properties']['LOCDESC']
            if ev['properties']['label'] is None:
                ev['properties']['label'] = ev['properties']['COMMENT']
        else:
            # incidents...
            ev['properties']['start'] = ev['properties']['Start']
            ev['properties']['stop'] = ev['properties']['End_']
            if ev['properties']['type'] == 'Travaux':
                ev['properties']['what'] = 'traffic.roadwork'
                ev['properties']['label'] = ev['properties']['type'] + ": " + ev['properties']['Description'] + ", " + ev['properties']['Street_name']
                ev['properties']['type'] = 'scheduled'


        ev['properties']['source'] = 'http://www.cavgp.opendata.arcgis.com/'

        geojson = json.dumps(ev)
        r = requests.post(api+'/event', data = geojson)
