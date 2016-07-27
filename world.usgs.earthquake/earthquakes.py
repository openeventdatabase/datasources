import requests
import json
import psycopg2
import time
import datetime
import pytz
import sqlite3
import sys
# adresse de l'API
api ='http://api.openeventdatabase.org'

sql = sqlite3.connect("earthquake.usgs.gov.db")

db = sql.cursor()
db.execute('CREATE TABLE IF NOT EXISTS earthquake (id text UNIQUE, what text, start text, geom text, label text, stop text, magnitude text)')

# Récupérer earthquake > 2.5 magnitude
# --> https://fr.wikipedia.org/wiki/Magnitude_d%27un_s%C3%A9isme

url = 'http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson'

resp = requests.get(url=url)

jsonResp = json.loads(resp.text)

for e in jsonResp['features']:

    # Gestion des dates locale et avec la TZ
    # convert localt time in UTC time TZ value is minutes from UTC
    # print 'TZ:%s' % e['properties']['tz']
    dt_local_earthquake = datetime.datetime.fromtimestamp(e['properties']['time'] / 1000).strftime(
        '%Y-%m-%d %H:%M:%S.%f')
    dt_earthquake = datetime.datetime.fromtimestamp(e['properties']['time'] / 1000) + datetime.timedelta(
        minutes=e['properties']['tz'])

    e_when = dt_earthquake.strftime('%Y-%m-%dT%H:%M:%S.%f')

    # other Key/Vals
    e_id = e['id']
    e_type = 'observed'
    e_what = 'nature.' + e['properties']['type']+'.'+str(e['properties']['mag'])[0]
    e_source = 'http://earthquake.usgs.gov'
    e_label = e['properties']['title']

    geometry = dict(type='Point', coordinates=[round(e['geometry']['coordinates'][0], 6), round(e['geometry']['coordinates'][1], 6)])

    # chercher dans la base si présent
    db.execute('SELECT id FROM earthquake where id = ?', (e_id,))
    rec = db.fetchone()

    if rec is None:
            properties = dict(type=e_type, what=e_what, when=e_when, source=e_source)

            properties['where:place'] = e['properties']['place']
            properties['name'] = "%s @ %s, %s" % (e['properties']['mag'], e_when[0:19].replace('T',' '), e['properties']['place'])
            properties['status'] = e['properties']['status']
            properties['magnitude'] = e['properties']['mag']
            properties['magnitude_type'] = e['properties']['magType']
            properties['url'] = e['properties']['url']
            properties['depth:km'] = e['geometry']['coordinates'][2]
            properties['tsunami'] = e['properties']['tsunami']

            # Constituer le geoJson
            geojson = json.dumps(dict(type='Feature', properties=properties, geometry=geometry), sort_keys=True)

            # Pousser dans OEDB --
            r = requests.post(api + '/event', data=geojson)

            # Ajouter dans la BDD
            db.execute("INSERT INTO earthquake VALUES ( ? , ? , ? , ? , ? , ?, ? )", (
                e_id, e_what, e_when, json.dumps(geometry, sort_keys=True), e_label, e_when, e['properties']['mag'])
            )
            sql.commit()


db.execute("VACUUM")
db.close()
