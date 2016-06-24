# Ecrit par Christian Quest le 2/6/2016
#
# ce code est sous licence WTFPL
# derniere version disponible sur https://github.com/openeventdatabase/datasources

from bs4 import BeautifulSoup
import requests
import sys
import json
import psycopg2
import datetime
import email.utils
import sqlite3

# adresse de l'API
api ='http://api.openeventdatabase.org'

db = psycopg2.connect("dbname=oedb")
cur = db.cursor()

# base sqlite pour suivre l'évolution des événements d'un run au suivant
sql = sqlite3.connect('vigicrues.db')
db = sql.cursor()
db.execute('CREATE TABLE IF NOT EXISTS evt (id text, what text, start text, geom text, label text, stop text)')

rss = requests.get('http://www.vigicrues.gouv.fr/rss/').content
r = BeautifulSoup(rss,'lxml')

for item in r.find_all('item'):
  label = item.find('title').string
  troncon = label[:label.find(':')-1]
  cur.execute("""SELECT ST_AsGeoJSON(wkb_geometry), cdentvigic FROM vigicrues_troncons WHERE nomentvigi = %s;""", (troncon,))
  g = cur.fetchone()
  if g is not None:
      niveau = ''
      if label[-5:] == 'Rouge':
        niveau = 'danger'
      if label[-6:] == 'Orange':
        niveau = 'alert'
      if label[-5:] == 'Jaune':
        niveau = 'warning'

      if niveau!='':
        rfc_date = item.find('pubdate').string
        start = email.utils.parsedate(rfc_date)
        tz=rfc_date[-5:]
        date_start = datetime.datetime(*start[:7]).isoformat()

        e_type = "unplanned"
        e_when = str(date_start)+tz
        e_what = "flood."+niveau
        geometry = json.loads(g[0])
        e_source = "http://www.vigicrues.gouv.fr/rss/"
 
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
            #print("POST:"+event['id'])
            db.execute("INSERT INTO evt VALUES ( ? , ? , ? , ? , ? , ? )", (event['id'], e_what, e_when, json.dumps(geometry,sort_keys=True), label, e_when))

# on supprime les événements qui n'ont plus court
if e_when is not None:
  db.execute("DELETE FROM evt WHERE stop < ?", (e_when,))

sql.commit()
db.close()

