import csv
import json
import requests
import sys
import psycopg2

api = 'http://api.openeventdatabase.org'

pg = psycopg2.connect("dbname=oedb")
cur = pg.cursor()

def aaaamm2iso(dt):
  return(dt[0:4]+"/"+dt[4:6]+"/"+dt[6:8]+"T"+dt[8:10]+":"+dt[10:12]+":"+dt[12:14])

synops = csv.DictReader(open(sys.argv[1]), delimiter=';')
for synop in synops:
    cur.execute("""SELECT ST_asgeojson(st_snaptogrid(wkb_geometry,0.00001)) as geom, nom, altitude FROM fr_synop_stations WHERE id=%s;""", (synop['numer_sta'], ))
    g = cur.fetchone()
    if g is not None:
        # prepare basic properties

        properties = dict(type='observed', what='weather.measure',
            when=aaaamm2iso(synop['date'])+"Z",
            source="SYNOP (donneespubliques.meteofrance.fr)",
            name=g[1])
        properties['where:omm_station_id'] = synop['numer_sta']
        if synop['pmer'] != 'mq':
          properties['pressure:hPa'] = float(synop['pmer'])/100
        if synop['dd'] != 'mq':
          properties['wind_dir:degrees'] = float(synop['dd'])
        if synop['ff'] != 'mq':
          properties['wind_speed:ms'] = float(synop['ff'])
          properties['wind_speed:kmh'] = round(float(synop['ff'])*3.6,2)
        if synop['raf10'] != 'mq':
          properties['wind_gust:ms'] = float(synop['raf10'])
          properties['wind_gust:kmh'] = round(float(synop['raf10'])*3.6,2)
        if synop['t'] != 'mq':
          properties['temperature:K'] = float(synop['t'])
          properties['temperature:C'] = round(float(synop['t'])-273.15,2)
        if synop['td'] != 'mq':
          properties['dew_point:K'] = round(float(synop['td'])-273.15,2)
          properties['dew_point:C'] = round(float(synop['td'])-273.15,2)
        if synop['u'] != 'mq':
          properties['humidity:pct'] = float(synop['u'])
        if synop['vv'] != 'mq':
          properties['visibility:km'] = round(float(synop['vv'])/1000,0)
        if synop['n'] != 'mq':
          properties['nebulosity:pct'] = synop['n']
        if synop['pres'] != 'mq':
          properties['local_pressure:hPa'] = round(float(synop['pres'])/100,2)
        if synop['ht_neige'] != 'mq':
          properties['snow_height:m'] = float(synop['ht_neige'])

        # create geojson
        geojson = json.dumps(dict(type='Feature', properties=properties, geometry=json.loads(g[0])),sort_keys=True)
        r = requests.post(api+'/event', data = geojson)
        if r.status_code == 201 :
          event = json.loads(r.text)
          print("POST:"+event['id'])
