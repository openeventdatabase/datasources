# Ecrit par Christian Quest le 25/7/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

import requests
import sys
import json
import re
import sqlite3
import psycopg2

# adresse de l'API
api ='http://api.openeventdatabase.org'

# base sqlite pour suivre l'évolution des événements d'un run au suivant
sql = sqlite3.connect('ratp.db')
db = sql.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS events (id text, what text,
  start text, geom text, label text, stop text)''')

# base postgis avec les géométries des lignes
pg = psycopg2.connect("dbname=oedb")
cur = pg.cursor()

if len(sys.argv)<=2:
  # récupération de la date dans le nom du fichier
  e_when=sys.argv[1][-21:]
  e_when=e_when[:16]+':00+02:00'
else:
  e_when=sys.argv[2]

with open(sys.argv[1]) as json_file:
    events = json.load(json_file)
    for reseau in events['status']:
      for ligne in events['status'][reseau]['lines']:
        e_what = None
        message = events['status'][reseau]['lines'][ligne]['message']

        e_type = 'unscheduled'
        e_text = reseau+'-'+ligne+': '+message

        match = re.search('la rame stationne à (.*) en dir. de (.*) \((.*)\)',message)
        if match:
          e_what = 'public_transport.incident'

        match = re.search('panne',message)
        if match:
          e_what = 'public_transport.incident.breakdown'

        match = re.search('colis suspect',message)
        if match:
          e_what = 'public_transport.incident.unattended_luggage'

        match = re.search('accident grave de voyageur',message)
        if match:
          e_what = 'public_transport.accident.suicide'

        match = re.search('voyageur sur la voie',message)
        if match:
          e_what = 'public_transport.incident.pedestrian'

        match = re.search('dégagement de fumée',message)
        if match:
          e_what = 'public_transport.incident.smoke'

        match = re.search('incident technique',message)
        if match:
          e_what = 'public_transport.incident.smoke'

        match = re.search('malaise voyageur',message)
        if match:
          e_what = 'public_transport.incident.passenger'

        match = re.search('obstacle sur la voie',message)
        if match:
          e_what = 'public_transport.incident.obstacle'

        match = re.search("déclenchement d'un signal d'alarme",message)
        if match:
          e_what = 'public_transport.incident.alarm'

        match = re.search('acte de malveillance',message)
        if match:
          e_what = 'public_transport.incident'

        match = re.search('aiguillage bloqué',message)
        if match:
          e_what = 'public_transport.incident.breakdown'

        match = re.search('animal sur la voie',message)
        if match:
          e_what = 'public_transport.incident.animal'

        match = re.search('arrêt de travail spontané',message)
        if match:
          e_what = 'public_transport.incident.strike'

        match = re.search("incident d'exploitation",message)
        if match:
          e_what = 'public_transport.incident'

        match = re.search('divers incidents',message)
        if match:
          e_what = 'public_transport.incident'

        match = re.search('incident voyageur',message)
        if match:
          e_what = 'public_transport.incident.passenger'

        match = re.search('intervention des équipes techniques',message)
        if match:
          e_what = 'public_transport.incident'

        match = re.search('manifestation',message)
        if match:
          e_what = 'public_transport.incident'

        match = re.search('mesure de sécurité',message)
        if match:
          e_what = 'public_transport.incident.safety'

        match = re.search('mouvement social',message)
        if match:
          e_what = 'public_transport.incident.strike'


        if e_what is not None:
            properties = dict(type=e_type, what=e_what, start=e_when, stop=e_when,
              name=e_text, source='http://www.ratp.fr')
            res_com=events['status'][reseau]['lines'][ligne]['icon']
            res_com=res_com.replace('bis','b').replace('R','RER ')
            cur.execute("""SELECT ST_asgeojson(st_linemerge(st_collect(st_snaptogrid(wkb_geometry,0.00001)))) as geom,
              res_com FROM stif_lignes WHERE res_com ~* %s GROUP BY 2;""", (res_com, ))
            g = cur.fetchone()
            geometry = json.loads(g[0])

            # a-t-on un évènement en cours ?
            db.execute('SELECT * FROM events WHERE start <= ? AND what = ? AND geom = ? AND label = ?',(e_when, e_what, json.dumps(geometry,sort_keys=True), e_text))
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
              r = requests.post(api+'/event', data = geojson)
              event = json.loads(r.text)
              #print("POST:"+event['id']+" "+message)
              db.execute("INSERT INTO events VALUES ( ? , ? , ? , ? , ? , ? )",
                (event['id'], e_what, e_when, json.dumps(geometry,sort_keys=True), e_text, e_when))

# on supprime les événements qui n'ont plus court
db.execute("DELETE FROM events WHERE stop < ?", (e_when,))
db.execute("VACUUM")
sql.commit()
db.close()
