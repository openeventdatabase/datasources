import requests
import json
import hashlib
import sqlite3
import time
import re

api = 'http://api.openeventdatabase.org'

def extractAndPush(nelat, nelon, swlat, swlon):
  url = 'https://carte.dondusang.com/gmap_regionchanged.php?nelat=%s&nelon=%s&swlat=%s&swlon=%s&marker=2&fb=0&t1=0&t2=4' % (nelat, nelon, swlat, swlon)
  r = requests.get(url)
  events = json.loads(r.text)
  nb = events['num_results']
  if nb>=30:
    # découpage dichotomique en 4 de la carte... et appel récursif
    extractAndPush(nelat, nelon, (nelat+swlat)/2, (nelon+swlon)/2)
    extractAndPush(nelat, (nelon+swlon)/2, (nelat+swlat)/2, swlon)
    extractAndPush((nelat+swlat)/2, nelon, swlat, (nelon+swlon)/2)
    extractAndPush((nelat+swlat)/2, (nelon+swlon)/2, swlat, swlon)
  else:
    for n in range(0, nb-1):
      e = events[str(n)]
      if e['icon'] == 'rou0':
        e_type = 'scheduled'
        e_what = 'health.blood.collect'
        e_source = 'https://carte.dondusang.com'
        e_text = e['lp_libconv']

        e_start = None
        if e['c_hdebutaprem'] is not None:
          # heure fournie dans le json, on l'utilise...
          e_start = time.strftime('%Y-%m-%dT'+e['c_hdebutaprem']+'CET', time.localtime(e['c_date']))
        elif e['text'] is not None:
          # extraction heure depuis le texte de description
          match = re.search('de (.....) à (.....)',e['text'])
          if match:
            e_start = time.strftime('%Y-%m-%dT'+match.group(1).replace('h',':')+':00CET', time.localtime(e['c_date']))
        if e_start is None:
          # heure par défaut (midi)
          e_start = time.strftime('%Y-%m-%dT12:00:00CET', time.localtime(e['c_date']))

        e_stop = None
        if e['c_hfin'] is not None:
          e_stop = time.strftime('%Y-%m-%dT'+e['c_hfin']+'CET', time.localtime(e['c_date']))
        elif e['text'] is not None:
          match = re.search('de (.....) à (.....)',e['text'])
          if match:
            e_stop = time.strftime('%Y-%m-%dT'+match.group(2).replace('h',':')+':00CET', time.localtime(e['c_date']))
        if e_stop is None:
          e_stop = time.strftime('%Y-%m-%dT18:00:00CET', time.localtime(e['c_date']))

        e_geom = dict(type = 'Point', coordinates = [round(float(e['lon']),6), round(float(e['lat']),6)])

        properties = dict(type=e_type, what=e_what, source=e_source, start=e_start, stop=e_stop, name=e_text)

        properties['source:id'] = e['c_id']
        if e['ville'] is not None:
          properties['where:name'] = e['ville']

        geojson = json.dumps(dict(type='Feature', geometry=e_geom, properties=properties),sort_keys=True)

        last =  db.execute('SELECT oedb_id, hash FROM evt WHERE id = ?',(e['c_id'],)).fetchone()
        # do we have an existing event ?
        md5 = hashlib.md5(str(geojson).encode()).hexdigest()
        if last is not None:
          # update if event has changed (different hash)
          if last[1] != md5:
            #print("PUT: "+last[0])
            r = requests.put(api+'/event/'+last[0], data = geojson)
            db.execute("UPDATE evt SET hash = ? WHERE oedb_id = ?", (md5, last[0]))
        else:
          r = requests.post(api+'/event', data = geojson)
          if r.status_code == 201:
            oedb = json.loads(r.text)
            #print("POST:"+oedb['id'])
            db.execute("INSERT INTO evt VALUES ( ? , ? , ? )", (oedb['id'], e['c_id'], md5))


# base sqlite pour suivre l'évolution des événements d'un run au suivant
sql = sqlite3.connect('efs.db')
db = sql.cursor()
db.execute('CREATE TABLE IF NOT EXISTS evt (oedb_id text, hash text, id text)')

# récupération France (métropolitaine)
extractAndPush(52, 8, 42, -4)

sql.commit()
db.close()
