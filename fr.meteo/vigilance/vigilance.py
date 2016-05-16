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
import time

x = BeautifulSoup(open(sys.argv[1]),'lxml')

d = x.cv.ev['dateinsert']
date_start = iso8601.parse_date(d[0:8]+'T'+d[-6:]+time.strftime('%z'))
d = x.cv.ev['dateprevue']
date_end = iso8601.parse_date(d[0:8]+'T'+d[-6:]+time.strftime('%z'))

db = psycopg2.connect("dbname=oedb")
cur = db.cursor()

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
      label = "soyez attentif: "+label
    if niveau == "3":
      niveau = "alert"
      label = "soyez vigilant: "+label
    if niveau == "4":
      niveau = "danger"
      label = "vigilance absolue, danger: "+label

    if dep == "75" :
      cur.execute("""SELECT ST_asgeojson(st_snaptogrid(st_union(wkb_geometry),0.000001)) as geom, 'Paris petite couronne' as nom FROM departements WHERE insee in ('75','92','93','94');""")
    else:
      cur.execute("""SELECT ST_asgeojson(st_snaptogrid(wkb_geometry,0.000001)) as geom, nom FROM departements WHERE insee=%s;""", (dep, ))
    g = cur.fetchone()
    if g is not None:
      label = g[1]+', '+label
      p = dict(type="forecast", what="weather."+niveau+"."+risque, source="http://vigilance.meteofrance.com/", start=str(date_start), where_name=g[1], where_INSEE=dep, stop=str(date_end), alert_level=niveau, label=label)
      geojson = json.dumps(dict(geometry=json.loads(g[0]), properties=p, type='Feature'))
      r = requests.post('http://api.openeventdatabase.org/event', data = geojson)
      print(r.status_code)
      print(p)
