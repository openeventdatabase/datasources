import requests
import json
import time
import csv
import psycopg2

pg = psycopg2.connect("dbname=oedb")
db = pg.cursor()

api = 'http://api.openeventdatabase.org'

with open('bisonfute2016.csv') as csvfile:
  trafic = csv.DictReader(csvfile, delimiter=',', quotechar='"')
  for row in trafic:
    start = '20'+row['date'][6:8]+'/'+row['date'][3:5]+'/'+row['date'][0:2]+'T00:00:00CET'
    stop = '20'+row['date'][6:8]+'/'+row['date'][3:5]+'/'+row['date'][0:2]+'T23:59:59CET'
    for sens in ['aller','retour']:
      if row[sens] != '':
        if row[sens][0]>'A':
          defaut = row[sens][0]
        else:
          defaut = ''
        for zone in range(1,7):
          if row[sens].find(str(zone)):
            couleur = row[sens][row[sens].find(str(zone))+1]
          else:
            couleur = defaut
          if couleur > 'A':
            db.execute('SELECT ST_asgeojson(geom) FROM bison_fute_geo WHERE zone = %s', (str(zone),))
            geo = db.fetchone()
            if geo is not None:
              what = 'traffic.forecast'
              if couleur == 'O':
                what = what + '.orange'
              if couleur == 'R':
                what = what + '.red'
              if couleur == 'N':
                what = what + '.black'
              if sens == 'aller':
                what = what + '.out'
              if sens == 'retour':
                what = what + '.return'
              p = dict(type='forecast',what=what, start=start, stop=stop, source='http://www.bison-fute.gouv.fr')
              geojson = json.dumps(dict(type='Feature',properties=p, geometry=json.loads(geo[0])))
              r = requests.post(api+'/event', data = geojson, )
              print("%s POST: %s %s" % (r.status_code, r.text,json.dumps(p)))

