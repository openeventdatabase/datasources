# Ecrit par Christian Quest le 1/6/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

from bs4 import BeautifulSoup
import requests
import sys
import re
import json

with open('vigicrue-stations.geojson') as json_file:
  data = json.load(json_file)
  for s in data['features']:
    url = 'http://www.vigicrues.gouv.fr/niveau3.php?AffProfondeur=168&nbrstations=5&ong=2&CdStationHydro='+s['properties']['id']
    # données des hauteurs d'eau
    hauteurs=requests.get(url+'&typegraphe=h').content.decode('utf-8')
    mesure_html = BeautifulSoup(hauteurs,'lxml')
    mesure_h = mesure_html.find(class_="liste")
    if mesure_h is not None:
      mesure_h = mesure_h.find_all("tr")
      nom_station=mesure_html.find("title").string[12:]
      print(nom_station)
      for m in mesure_h:
        mesure = m.find_all("td")
        if len(mesure)>0:
          when=mesure[0].string
          # remise en forme de l'heure
          when=when[6:10]+'-'+when[3:5]+'-'+when[0:2]+'T'+when[11:]+':00+02:00'
          if when > '2016-06-01':
            # préparation du geojson

            geojson = json.dumps(dict(type='Feature',properties=dict(source='http://www.vigicrues.gouv.fr/niveau3.php?CdStationHydro='+s['properties']['id'], type='observed', what='water.level', when=when, hauteur=mesure[1].string, id_station=s['properties']['id'], label=nom_station+" : "+mesure[1].string+"m"), geometry=s['geometry']))
            # envoi à l'API OpenEventDatabase
            r = requests.post('http://api.openeventdatabase.org/event', data = geojson)

