# Ecrit par Christian Quest le 19/4/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

from bs4 import BeautifulSoup
import requests
import sys
import re
import json
import iso8601
import psycopg2
import sqlite3

api = 'http://api.openeventdatabase.org'

# base sqlite pour suivre l'évolution des événements d'un run au suivant
sql = sqlite3.connect('vigilance.db')
db = sql.cursor()
db.execute('CREATE TABLE IF NOT EXISTS evt (id text, what text, start text, geom text, label text, stop text)')


x = BeautifulSoup(open(sys.argv[1]),'lxml')

d = x.cv.ev['dateinsert']
date_start = iso8601.parse_date(d[0:8]+' '+d[-6:])
d = x.cv.ev['dateprevue']
date_end = iso8601.parse_date(d[0:8]+' '+d[-6:])

pg = psycopg2.connect("dbname=oedb")
cur = pg.cursor()

for d in x.find_all('dv'):
  dep = d['dep']
  niveau = d['coul']
  if d.risque is not None:
    risque = d.risque['val']
    if risque == "1":
      risque = "wind"
      label = "Vent violent"
    if risque == "2":
      risque = "rain"
      label = "Pluie-inondation"
    if risque == "3":
      risque = "thunderstorm"
      label = "Orages"
    if risque == "4":
      risque = "flood"
      label = "Inondation"
    if risque == "5":
      risque = "snow-ice"
      label = "Neige-verglas"
    if risque == "6":
      risque = "hightemp"
      label = "Canicule"
    if risque == "7":
      risque = "lowtemp"
      label = "Grand-froid"
    if risque == "8":
      risque = "avalanche"
      label = "Avalanche"
    if niveau == "2":
      niveau = "warning"
      label = "Soyez attentif: "+label
    if niveau == "3":
      niveau = "alert"
      label = "Soyez vigilant: "+label
    if niveau == "4":
      niveau = "danger"
      label = "Vigilance absolue, danger: "+label

    if dep == "75" :
      cur.execute("""SELECT ST_asgeojson(st_snaptogrid(st_union(wkb_geometry),0.000001)) as geom, 'Paris petite couronne' as nom FROM departements WHERE insee in ('75','92','93','94');""")
    elif dep == "69" :
      cur.execute("""SELECT ST_asgeojson(st_snaptogrid(st_union(wkb_geometry),0.000001)) as geom, 'Rhône' as nom FROM departements WHERE insee in ('69D','69M');""")
    else:
      cur.execute("""SELECT ST_asgeojson(st_snaptogrid(wkb_geometry,0.000001)) as geom, nom FROM departements WHERE insee=%s;""", (dep, ))
    g = cur.fetchone()

    e_start = str(date_start)
    e_stop = str(date_end)
    e_type="forecast"
    e_what = "weather."+niveau+"."+risque
    e_geom = json.loads(g[0])
    e_text = label
    e_source = "http://vigilance.meteo.fr"

    # a-t-on un évènement en cours ?
    db.execute('SELECT id,start,stop FROM evt WHERE start <= ? AND stop < ? AND what = ? AND geom = ? AND label = ?',(e_start, e_stop, e_what, json.dumps(e_geom,sort_keys=True), e_text))
    last = db.fetchone()
    if last is not None:
      # on a déjà un événement similaire en cours... on le prolonge
      geojson=json.dumps(dict(type='Feature', properties=dict(type = e_type, what = e_what, start = last[1], stop = e_stop, source=e_source, label = e_text), geometry = e_geom))
      print("PUT: "+last[0]+" "+last[1] +">"+e_stop)
      r = requests.put(api+'/event/'+last[0], data = geojson)
      db.execute("UPDATE evt SET stop = ? WHERE id = ?", (e_stop, last[0]))
    else:
      geojson=json.dumps(dict(type='Feature', properties=dict(type = e_type, what = e_what, start = e_start, stop = e_stop, source= e_source, label = e_text), geometry = e_geom))
      r = requests.post(api+'/event', data = geojson)
      if r.status_code == 201 :
        event = json.loads(r.text)
        print("POST:"+event['id'])
        #print(geojson)
        db.execute("INSERT INTO evt VALUES ( ? , ? , ? , ? , ? , ? )", (event['id'], e_what, e_start, json.dumps(e_geom,sort_keys=True), e_text, e_stop))
      if r.status_code == 409 :
        print(r.text)
      else:
        print(r.status_code)

# on supprime les événements qui n'ont plus court
if e_stop is not None:
  db.execute("DELETE FROM evt WHERE stop < ?", (e_stop,))
  db.execute("VACUUM")

sql.commit()
db.close()
