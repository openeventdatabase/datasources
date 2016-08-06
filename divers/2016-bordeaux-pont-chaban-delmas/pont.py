import json
import requests
import csv
from datetime import tzinfo, timedelta, datetime

api = 'http://api.openeventdatabase.org'
csvreader = csv.DictReader(open('pont.csv'), delimiter=';')
for row in csvreader:
    try:
        p = dict(type='scheduled',what='traffic.closed',source='http://data.bordeaux-metropole.fr/data.php?layer=PREVISIONS_PONT_CHABAN')
        geometry = json.loads("""{"type": "LineString","coordinates": [[-0.55370,44.86017],[-0.54954,44.85614]]}""")
        dt_start = datetime.strptime(row['Date passage']+row['Fermeture a la circulation'], "%d/%m/%Y%H:%M")
        dt_stop = datetime.strptime(row['Date passage']+row['Re-ouverture a la circulation'], "%d/%m/%Y%H:%M")
        if row['Fermeture a la circulation']>row['Re-ouverture a la circulation']:
            dt_stop = e_stop + timedelta(days=1)
        if dt_start.isoformat()<'2016-03-27T03:00:00': # heure d'hiver 2015-2016
            e_start = dt_start.isoformat()+'+01:00'
        else:
            e_start = dt_start.isoformat()+'+02:00'
        if dt_stop.isoformat()<'2016-03-27T03:00:00': # heure d'hiver 2015-2016
            e_stop = dt_stop.isoformat()+'+01:00'
        else:
            e_stop = dt_stop.isoformat()+'+02:00'
        p['start'] = e_start
        p['stop'] = e_stop
        p['name'] = 'Fermeture %s du pont Chaban-Delmas (%s)' % (row['Type de fermeture'],row['Bateau'].strip())
        geojson = json.dumps(dict(type='Feature', properties=p, geometry=geometry))
        r = requests.post(api+'/event', data=geojson)
        print(r.text)
    except:
        pass
