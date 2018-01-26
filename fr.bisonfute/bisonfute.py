import requests
import json
import time
from pyproj import Proj, transform

"""
Scrapping des données de circulation sur bisonfute.fr
export en stream geojson avec 1 événement par ligne
"""

def charge(x,y,z):
    nb = 0
    deeper = False
    url = dataurl+("trafic/maintenant/tfs/evenements/%s/%s/%s.json" % (z,x,y))
    datareq = requests.get(url=url)
    datajson = json.loads(datareq.text)
    if not datajson['empty']:
      for e in datajson['features']:
        if e['properties']['urlImage'][7]=='1':
          deeper = True
        lon,lat = transform(s_srs,t_srs,e['geometry']['coordinates'][0],e['geometry']['coordinates'][1])
        geometry=dict(type = 'Point', coordinates = [round(lon,6),round(lat,6)])
        quoi = e['properties']['urlImage'][11:-4]
        if quoi == 'travaux':
          quoi = 'roadwork'
        if quoi == 'bouchon':
          quoi = 'jam'
        e_what = 'traffic.'+quoi

        detailreq = requests.get('http://www.bison-fute.gouv.fr/' + e['properties']['urlcpc'])
        detail = json.loads(detailreq.text)
        if len(detail)>1:
            deeper = True
        else:
            for d in detail:
              print(json.dumps({"geometry":geometry, "properties":{"data":d}}))

      if deeper:
        charge(2*x, 2*y, z+1)
        charge((2*x)+1, 2*y, z+1)
        charge(2*x, (2*y)+1, z+1)
        charge((2*x)+1, (2*y)+1, z+1)

    return nb

# projections utilisées pour transformation en WGS84
s_srs = Proj(init='EPSG:2154')
t_srs = Proj(init='EPSG:4326')

# récupération date courante
datereq = requests.get(url='http://www.bison-fute.gouv.fr/data/iteration/date.json')
datejson = json.loads(datereq.text)
dernier = time.strftime('%Y%m%d-%H%M%S', time.localtime(datejson[0]/1000))
dataurl = "http://www4.bison-fute.gouv.fr/data/data-%s/" % dernier
for x0 in range(0,5):
  for y0 in range (0,5):
    charge(x0,y0,1)
