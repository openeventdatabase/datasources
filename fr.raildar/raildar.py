# Ecrit par Christian Quest le 29/10/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

import requests
import sys
import json
import re
import sqlite3
import psycopg2
import requests

# adresse de l'API
api ='http://api.openeventdatabase.org'

# base sqlite pour suivre l'évolution des événements d'un run au suivant
sql = sqlite3.connect(sys.argv[2])
db = sql.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS events (id text, what text,
  start text, geom text, label text, stop text)''')

pgdb = psycopg2.connect("dbname=oedb")
pg = pgdb.cursor()
pg.execute('CREATE TABLE IF NOT EXISTS raildar_geom (id_train bigint, geom geometry)')

# récupération de la date dans le nom du fichier
e_when=sys.argv[1][-26:]
e_when=e_when[:21]

with open(sys.argv[1]) as json_file:
    events = json.load(json_file)
    for ev in events['features']:
      evp = ev['properties']
      if evp['retard'] != 0:
        e_what = 'public_transport.delay'
        e_text = message = "%s %s (vers %s) retard de %s mn" % (evp['brand'],evp['id_mission'],evp['terminus'],evp['retard'])
        e_type = 'unscheduled'
        if evp['retard'] >= 30:
            e_what = 'public_transport.delay.major'
        if evp['retard'] < 0:
            e_what = 'public_transport.cancelled'

        properties = dict(type=e_type, what=e_what, start=e_when, stop=e_when,
          name=e_text, source='http://raildar.fr')

        # trajet du train (geometry)
        pg.execute('SELECT ST_asgeojson(geom) FROM raildar_geom WHERE id_train = %s',(evp['id_train'],))
        train = pg.fetchone()
        if train is None:
            # on récupère le trajet de ce train sur l'API raildar
            r = requests.get('http://raildar.fr/json/show_trajet?id_train=%s' % evp['id_train'])
            train_json = json.loads(r.text)
            if r.text is not None:
                # construction d'une géométrie complète pour le trajet via postgis
                for geom in train_json['features']:
                    # ajout des segments entre gares
                    if geom['geometry']['type'] == 'LineString':
                        pg.execute('INSERT INTO raildar_geom VALUES (%s, ST_geomfromgeojson(%s))',(-evp['id_train'], json.dumps(geom['geometry'])))
                # jointure des segments
                pg.execute('''INSERT INTO raildar_geom SELECT -id_train, ST_LineMerge(ST_Collect(geom)) FROM raildar_geom WHERE id_train = %s GROUP BY 1''',(-evp['id_train'],))
                # suppression des segments
                #pg.execute('DELETE FROM raildar_geom WHERE id_train = %s',(-evp['id_train'],))
                pg.execute('COMMIT')
                # récupération du trajet complet
                pg.execute('SELECT ST_asgeojson(geom) FROM raildar_geom WHERE id_train = %s',(evp['id_train'],))
                train = pg.fetchone()

        try:
            geometry = json.loads(train[0])
            # a-t-on un évènement en cours ?
            db.execute('SELECT * FROM events WHERE start <= ? AND what = ? AND geom = ? AND label = ?',(e_when, e_what, train[0], e_text))
            last = db.fetchone()
            if last is not None:
              # on a déjà un événement similaire en cours... on le prolonge
              properties['start']=last[2]
              geojson = json.dumps(dict(properties=properties, geometry = geometry), sort_keys=True)
              #print("PUT: "+last[0]+" "+last[2] +">"+e_when+" "+message)
              r = requests.put(api+'/event/'+last[0], data = geojson)
              db.execute("UPDATE events SET stop = ? WHERE id = ?", (e_when, last[0]))
            else:
              geojson = json.dumps(dict(properties=properties, geometry = geometry), sort_keys=True)
              #print(geojson)
              r = requests.post(api+'/event', data = geojson)
              try:
                  event = json.loads(r.text)
                  #print("POST:"+event['id']+" "+message)
                  if 'id' in event :
                    db.execute("INSERT INTO events VALUES ( ? , ? , ? , ? , ? , ? )",
                      (event['id'], e_what, e_when, train[0], e_text, e_when))
              except:
                  print(r.text)
                  pass
        except:
            pass

# on supprime les événements qui n'ont plus court
#for row in db.execute("SELECT id,what,start,stop,label FROM events WHERE stop < ?", (e_when,)):
#    print(row)
db.execute("DELETE FROM events WHERE stop < ?", (e_when,))
db.execute("VACUUM")
sql.commit()
db.close()
