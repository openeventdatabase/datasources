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

# création base sqlite pour infos stations
conn = sqlite3.connect('stations.db')
conn.execute('CREATE TABLE IF NOT EXISTS stations (id text PRIMARY KEY, nom text, marque text)')

# récupération du token pour la recherche
session = requests.session()
html = session.get('https://www.prix-carburants.gouv.fr/').text
html_tree = BeautifulSoup(html,'lxml').find(id="recherche_recherchertype__token")
token=html_tree['value']

# préparation de la liste des départements...
depts = ['2A','2B']
for dep in range(1, 19):
    d = '0'+str(dep)
    depts.append(d[-2:])
for dep in range(21, 95):
    depts.append(str(dep))

for d in depts:
    # exécution de la recherche
    html = session.post('https://www.prix-carburants.gouv.fr/',
        {'_recherche_recherchertype[localisation]':d,
        '_recherche_recherchertype[_token]':token,
        '_recherche_recherchertype[choix_carbu]':'1'}).text
    page=1
    while True:
        # réception des résultats (paginés)
        html = session.get('https://www.prix-carburants.gouv.fr/recherche/?page=%s&limit=100' % page).text
        html_tree = BeautifulSoup(html,'lxml')
        try:
            pages = len(html_tree.find(id='page').find_all('option'))
        except:
            pages=1

        for station in html_tree.find_all(class_='data'):
            td = station.find_all(class_='pointer')
            st = dict(id=station['id'], commune=td[1].string, nom=td[2].string, marque=td[3].string)
            print(json.dumps(st,sort_keys=True))
            conn.execute("INSERT INTO stations VALUES (?,?,?) ON CONFLICT REPLACE", (station['id'], td[2].string, td[3].string))

        if page==pages:
            break
        else:
            page = page + 1

conn.commit()
