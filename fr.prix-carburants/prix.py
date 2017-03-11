# Ecrit par Christian Quest le 10/3/2017
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

# récupération des nom/marque des stations services et sortie en stream json

from bs4 import BeautifulSoup
import requests
import sys
import json
import sqlite3
import datetime

api = 'http://localhost:8000/'

# base sqlite pour infos stations (nom/marque)
conn = sqlite3.connect('stations.db')
conn.execute('CREATE TABLE IF NOT EXISTS events (id text PRIMARY KEY, event text, start text)')

xml = open(sys.argv[1],encoding="iso8859-1")

if len(sys.argv)>2:
    stop = sys.argv[2] # timestamp de fin pour ce prix
else:
    # par défaut prix valable 4 semaines
    stop = (datetime.datetime.now()+datetime.timedelta(days=28)).isoformat()

print('stop=',stop)

prix = BeautifulSoup(xml.read(),'lxml')
for pdv in prix.find_all(name='pdv'):
    maj = ''
    s=dict(id_pdv=pdv['id'],
        postcode=pdv['cp'],
        pop=pdv['pop'],
        adresse=pdv.find('adresse').string,
        ville=pdv.find('ville').string,
        where_name=pdv.find('adresse').string + ' ' + pdv['cp'] + ' ' + pdv.find('ville').string,
        ouverture_debut=pdv.find('ouverture')['debut'][:5],
        ouverture_fin=pdv.find('ouverture')['fin'][:5],
        ouverture_sauf=pdv.find('ouverture')['saufjour'],
        services=[],
        carburants=[],
        label=''
    )

    if s['ouverture_debut']==s['ouverture_fin']:
        s['ouverture:fr'] = '24/7'
    else:
        s['ouverture:fr'] = (s['ouverture_debut']+'-'+s['ouverture_fin']).replace(':','h')
        if s['ouverture_sauf'] != '':
            s['ouverture:fr'] = s['ouverture:fr'] + ' sauf '+ s['ouverture_sauf']

    for service in pdv.find_all('service'):
        s['services'].append(service.string)

    for carburant in pdv.find_all('prix'):
        if carburant['valeur'].find('.')>=0:
            prix = float(carburant['valeur'])
        else:
            prix = float(carburant['valeur'])/1000
        s['carburants'].append(dict(carburant=carburant['nom'],
            carburant_id=carburant['id'],
            prix=prix,
            maj=carburant['maj']))
        s['label'] = s['label'] + carburant['nom']+': '+str(prix)+'€, '
        if carburant['maj']>maj:
            maj = carburant['maj']
    s['label'] = s['label'][:-2]
    maj = maj.replace('T',' ')

    station = conn.execute('SELECT * FROM stations where id=?', (pdv['id'],)).fetchone()
    if station is not None:
        s['nom']=station[1]
        s['marque']=station[2]
        s['where_name']=station[1]+', '+s['where_name']

    s['start']=maj
    s['stop']=stop
    s['type']='observed'
    s['what']='fuel.price'
    s['source']='www.prix-carburants.gouv.fr'

    if pdv['longitude'] != '' and pdv['latitude'] != '':
        g = dict(type='Point',coordinates=[float(pdv['longitude'])/100000,float(pdv['latitude'])/100000])
        if len(s['carburants'])>0:
            last = None
            prev = None
            try:
                # on avait un événement en cours
                e = conn.execute("SELECT * FROM  events WHERE id=?", (pdv['id'],)).fetchone()
                # on change sa date de fin
                if maj != e[2]:
                    r = requests.patch(api+'/event/'+e[1], json.dumps(dict(properties=dict(what='fuel.price.old', type='observed', start=e[2], stop=s['start']))))
                    print('PUT',e[1])
                last = e[2]
                prev = e[1]
            except:
                pass

            if last is None or last != maj:
                # on crée le nouvel événement
                if prev is not None:
                    s['prev_event'] = 'http://api.openeventdatabase.org/event/'+prev
                r = requests.post(api+'/event', data = json.dumps(dict(type='Feature', properties=s, geometry=g),sort_keys=True))
                # on récupère l'id
                event = json.loads(r.text)
                # que l'on stocke pour future mise à jour
                if 'id' in event:
                    conn.execute("INSERT OR REPLACE INTO events VALUES (?,?,?)", (pdv['id'],event['id'],maj))
                    conn.commit()
                    print("POST",event['id'])
