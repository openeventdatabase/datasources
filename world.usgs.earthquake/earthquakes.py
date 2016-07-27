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
    e_magnitude = e['properties']['mag']
    e_magnitude_type = e['properties']['magType']

    # other Key/Vals
    e_id = e['id']
    e_type = 'observed'
    e_what = 'nature.' + e['properties']['type']
    e_source = 'http://earthquake.usgs.gov'
    e_label = e['properties']['title']
    e_where_place = e['properties']['place']
    e_status = e['properties']['status']

    e_lon = e['geometry']['coordinates'][0]
    e_lat = e['geometry']['coordinates'][1]
    e_depth = e['geometry']['coordinates'][2]

    geometry = dict(type='Point', coordinates=[round(e_lon, 6), round(e_lat, 6)])

    # chercher dans la base si présent
    db.execute('SELECT id FROM earthquake where id = ?', (e_id,))
    rec = db.fetchone()

    if rec is None:
        try :
            properties = dict(type=e_type, what=e_what, when=e_when, source=e_source)

            properties['where:place'] = e_where_place
            properties['source'] = e_source
            properties['name'] = "%s - %s" % (e_magnitude, e_start)
            properties['status'] = e_status
            properties['magnitude'] = e_magnitude
            properties['magnitude_type'] = e_magnitude_type

            # Constituer le geoJson
            geojson = json.dumps(dict(type='Feature', properties=properties, geometry=geometry), sort_keys=True)

            # Pousser dans OEDB --
            r = requests.post(api + '/event', data=geojson)

            # Ajouter dans la BDD
            db.execute("INSERT INTO earthquake VALUES ( ? , ? , ? , ? , ? , ?, ? )", (
                e_id, e_what, e_when, json.dumps(geometry, sort_keys=True), e_label, e_when, e_magnitude)
            )
            sql.commit()

        except:
            print("Unexpected error:", sys.exc_info()[0])

db.execute("VACUUM")
db.close()





