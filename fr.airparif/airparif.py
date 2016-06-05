# Ecrit par Christian Quest le 5/6/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

from bs4 import BeautifulSoup
import requests
import sys
import re
import json
import psycopg2
import datetime
from   datetime import timedelta

api = 'http://api.openeventdatabase.org'

departements = (75,77,78,91,92,93,94,95)
indices = ['vlow','low','medium','high','vhigh']
alerts = ['','','.warning','.alert','.alert']
niveau = ['très bas','bas','moyen','élevé','très élevé']

# connexion base postgis pour géométries des départements
db = psycopg2.connect("dbname=oedb")
cur = db.cursor()

for dep in departements:
  # download HTML page
  html = requests.get('http://www.airparif.asso.fr/en/indices/indice-europeen-departement/dep/'+str(dep)).text
  # parse HTML
  html_tree = BeautifulSoup(html,'lxml')
  indice_max = 0
  for data in html_tree.find_all(class_='tr_nd'):
    type_mesure = data.find(class_='table_heure_nd').string
    mesures = data.find_all('td')
    indice = mesures[3]['class'][0][7:]
    if indices.index(indice) > indice_max:
      indice_max = indices.index(indice)
    if re.search('NO2',type_mesure):
      mesure_no2 = int(mesures[3].string)
      indice_no2 = indice
    elif re.search('O3',type_mesure):
      mesure_o3 = int(mesures[3].string)
      indice_o3 = indice
    elif re.search('PM10',type_mesure):
      mesure_pm10 = int(mesures[3].string)
      indice_pm10 = indice

  # géométrie du département... et nom
  cur.execute("""SELECT ST_asgeojson(st_snaptogrid(wkb_geometry,0.000001)), nom FROM departements WHERE insee=%s;""", (str(dep), ))
  g = cur.fetchone()
  p = dict(type = 'forecast',
           what = 'air.pollution.level'+alerts[indice_max],
           label = g[1]+" : Niveau de pollution de l'air "+niveau[indice_max],
           where_name = g[1], where_insee = dep,
           start = (datetime.date.today()+timedelta(days=1)).isoformat()+'T00:00:00',
           stop = (datetime.date.today()+timedelta(days=2)).isoformat()+'T00:00:00',
           source = 'http://airparif.fr/',
           level_no2 = mesure_no2, indice_no2 = indice_no2,
           level_o3 = mesure_o3, indice_o3 = indice_o3,
           level_pm10 = mesure_pm10, indice_pm10 = indice_pm10)
  geojson = json.dumps(dict(geometry=json.loads(g[0]), properties=p, type='Feature'),sort_keys=True)
  r = requests.post(api+'/event', data = geojson)

