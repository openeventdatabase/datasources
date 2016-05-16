# Ecrit par Christian Quest le 8/5/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

import requests
import sys
import json
import re
import psycopg2

e_when=sys.argv[2]

db = psycopg2.connect("dbname=osm")
cur = db.cursor()

with open(sys.argv[1]) as json_file:
    data = json.load(json_file)
    for e in data['Placemarks']:
      e_what = 'traffic'
      if e['Preview'][:8]=='ACCIDENT':
        e_what = 'traffic.accident'
      if e['Preview'][:8]=='OBSTACLE':
        e_what = 'traffic.obstacle'
      if e['Preview'][:10]=='BROUILLARD':
        e_what = 'weather.warning.fog'

      label = e['Metadatas']['AUTOROUTE']
      if e['Metadatas']['DIRECTION'] != '':
        label = label +' vers '+e['Metadatas']['DIRECTION']
      label = label + ': ' + e['Preview']

      geometry = dict(type = 'Point', coordinates = [e['Points'][0]['Lon'],e['Points'][0]['Lat']])
      geojson=dict(type='Feature', properties=dict(type='unscheduled', what=e_what, when=e_when, source='http://www.vinci-autoroutes.com/', label=label), geometry=geometry)
      r = requests.post('http://api.openeventdatabase.org/event', data = json.dumps(geojson))
      #print(json.dumps(geojson))
