# Ecrit par Christian Quest le 10/3/2017
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

# récupération des nom/marque des stations services et sortie en stream json
# à appeler par exemple avec: python stations.py > stations.json

from bs4 import BeautifulSoup
import requests
import sys
import json
import sqlite3
import re

# création base sqlite pour infos stations
conn = sqlite3.connect('stations.db')
conn.execute('CREATE TABLE IF NOT EXISTS stations (id text PRIMARY KEY, nom text, marque text)')

# récupération du token pour la recherche
session = requests.session()
html = session.get('https://www.prix-carburants.gouv.fr/').text
html_tree = BeautifulSoup(html,'lxml').find(id="recherche_recherchertype__token")
token=html_tree['value']

# préparation de la liste des départements, dans l'ordre numérique...
depts = ['01']
for dep in range(2, 20):
    d = '0'+str(dep)
    depts.append(d[-2:])
depts.extend(['2A', '2B'])
for dep in range(21, 96):
    depts.append(str(dep))

# Préparation du fichier JSON
print('[')

for d in depts:
    # exécution de la recherche
    html = session.post('https://www.prix-carburants.gouv.fr/',
        {'_recherche_recherchertype[localisation]':d,
        '_recherche_recherchertype[_token]':token}).text
    page=1
    while True:
        # réception des résultats (paginés)
        html = session.get('https://www.prix-carburants.gouv.fr/recherche/?page=%s&limit=100' % page).text
        html_tree = BeautifulSoup(html,'lxml')
        try:
            pages = len(html_tree.find_all(class_=re.compile('^paginationPage')))
        except:
            pages=1

        for station in html_tree.find_all(class_='data'):
            dv = station.find(class_='pdv-description')
            td = dv.find_all(re.compile('span'))
            NomMarque = dv.find('strong').string.split(' | ')
            st = dict(id=station['id'], nom=NomMarque[0], marque=NomMarque[1])
            print(json.dumps(st,sort_keys=True, separators=(',', ':'))+',')
            conn.execute("INSERT INTO stations VALUES (?,?,?) ON CONFLICT REPLACE", (station['id'], NomMarque[0], NomMarque[1]))

        if page==pages:
            break
        else:
            page = page + 1

# Fermeture des fichiers
print('{}]')
conn.commit()
