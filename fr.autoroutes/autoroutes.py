# Ecrit par Christian Quest le 8/5/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

import requests
import sys
import json
import re
import psycopg2
import sqlite3

# This function is free of any dependencies.
# source: https://github.com/mgd722/decode-google-maps-polyline
def decode_polyline(polyline_str):
    '''Pass a Google Maps encoded polyline string; returns list of lat/lon pairs'''
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']: 
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index+=1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append((lat / 100000.0, lng / 100000.0))

    return coordinates



# adresse de l'API
api ='http://api.openeventdatabase.org'

# base sqlite pour suivre l'évolution des événements d'un run au suivant
sql = sqlite3.connect('vinci.db')
db = sql.cursor()
db.execute('CREATE TABLE IF NOT EXISTS evt (id text, what text, start text, geom text, label text, stop text)')

if len(sys.argv)<=2:
  # récupération de la date dans le nom du fichier
  e_when=sys.argv[1][-21:]
  e_when=e_when[:16]+':00+01:00'
else:
  e_when=sys.argv[2]

with open(sys.argv[1]) as json_file:
    data = json.load(json_file)
    for e in data['Placemarks']:
      e_what = 'traffic'
      if e['Preview'][:8]=='ACCIDENT':
        e_what = 'traffic.accident'
      if e['Preview'][:6]=='ANIMAL':
        e_what = 'traffic.obstacle'
      if e['Preview'][:12]=='AVERSE DE GR':
        e_what = 'weather.warning.hail'
      if e['Preview'][:10]=='BROUILLARD':
        e_what = 'weather.warning.fog'
      if e['Preview'][:7]=='BOUCHON':
        e_what = 'traffic.jam';
      if e['Preview'][:16]=='CHAUSSÉE INONDÉE':
        e_what = 'weather.warning.flood';
      if e['Preview'][:5]=='FUMÉE':
        e_what = 'traffic.smoke';
      if e['Preview'][:8]=='INCENDIE':
        e_what = 'traffic.fire';
      if e['Preview'][:5]=='NEIGE':
        e_what = 'weather.warning.snow';
      if e['Preview'][:8]=='OBSTACLE':
        e_what = 'traffic.obstacle'
      if e['Preview'][:6]=='PAS DE':
        e_what = 'traffic.nogaz'
      if e['Preview'][:6]=='PIETON':
        e_what = 'traffic.obstacle.pedestrian'
      if e['Preview'][:19]=='PLUIES VERGLACANTES':
        e_what = 'weather.warning.hail';
      if e['Preview'][:7]=='TRAVAUX':
        e_what = 'traffic.roadwork';
      if e['Preview'][:15]=='VÉHICULE ARRÊTÉ':
        e_what = 'traffic.obstacle.vehicule';
      if e['Preview'][:15]=='VÉHICULE EN FEU':
        e_what = 'traffic.fire.vehicule';
      if e['Preview'][:9]=='VENT FORT':
        e_what = 'weather.warning.wind';
      if e['Preview'][:7]=='VERGLAS':
        e_what = 'weather.warning.hail';

      label = e['Metadatas']['AUTOROUTE']
      if e['Metadatas']['DIRECTION'] != '':
        label = label +' vers '+e['Metadatas']['DIRECTION']
      label = label + ': ' + e['Preview']

      e_type = "unplanned"
      e_source = "http://www.vinci-autoroutes.com/"

      # décodage polyline pour récupérer la bonne extrémité
      geo = decode_polyline(e['Lines'][0])
      lat,lon = geo[0]
      geometry = dict(type = 'Point', coordinates = [lon,lat])

      # a-t-on un évènement en cours ?
      db.execute('SELECT * FROM evt WHERE start <= ? AND what = ? AND geom = ? AND label = ?',(e_when, e_what, json.dumps(geometry,sort_keys=True), label))
      last = db.fetchone()
      if last is not None:
        # on a déjà un événement similaire en cours... on le prolonge
        geojson=json.dumps(dict(properties=dict(type = e_type, what = e_what, start = last[2], stop = e_when, source=e_source, label = label), geometry = geometry))
        if e_when > last[2]:
          #print("PUT: "+last[0]+" "+last[2] +">"+e_when)
          r = requests.put(api+'/event/'+last[0], data = geojson)
          db.execute("UPDATE evt SET stop = ? WHERE id = ?", (e_when, last[0]))
      else:
        geojson=json.dumps(dict(properties=dict(type = e_type, what = e_what, when = e_when, source= e_source, label = label), geometry = geometry))
        r = requests.post(api+'/event', data = geojson)
        if r.status_code == 201:
          event = json.loads(r.text)
          print(e_when+" POST:"+event['id'])
          db.execute("INSERT INTO evt VALUES ( ? , ? , ? , ? , ? , ? )", (event['id'], e_what, e_when, json.dumps(geometry,sort_keys=True), label, e_when))

# on supprime les événements qui n'ont plus court
if e_when is not None:
  db.execute("DELETE FROM evt WHERE stop < ?", (e_when,))

sql.commit()
db.close()

