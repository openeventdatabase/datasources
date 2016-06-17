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

db = psycopg2.connect("dbname=oedb")
cur = db.cursor()

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
        p = dict(type="unplanned", what="flood."+niveau, source="http://www.vigicrues.gouv.fr/rss/", when=str(date_start)+tz, alert_level=niveau, label=label)
        geojson = json.dumps(dict(geometry=json.loads(g[0]), properties=p, type='Feature'))
        #r = requests.post('http://localhost:8000/event', data = geojson)

