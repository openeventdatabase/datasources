import sys
import json
import requests
import psycopg2
from metar import Metar

api = 'http://api.openeventdatabase.org'

pg = psycopg2.connect("dbname=oedb")
cur = pg.cursor()

# open text file containing one METAR per line
txt = open(sys.argv[1])
for station in txt:
  try:
    # decode METAR message with python-metar
    obs = Metar.Metar(station)
    # get station data (name, location, etc)
    cur.execute("""SELECT ST_asgeojson(st_snaptogrid(wkb_geometry,0.00001)) as geom, wikidata, name FROM icao_stations WHERE icao=%s;""", (obs.station_id, ))
    g = cur.fetchone()
    if g is not None:
        # prepare basic properties
        properties = dict(type='observed', what='weather.measure', when=obs.time.isoformat()+'Z', source='METAR')

        # add location properties
        if g[1] is not None:
          properties['where:wikidata']=g[1]
        if g[2] is not None:
          properties['where:name']=g[2]

        # add available weather data
        if obs.temp is not None:
          properties['temperature:C']=float(obs.temp.string('C').replace(' C',''))
          properties['temperature:F']=float(obs.temp.string('F').replace(' F',''))
          properties['temperature:K']=float(obs.temp.string('K').replace(' K',''))
        if obs.dewpt is not None:
          properties['dew_point:C']=float(obs.dewpt.string('C').replace(' C',''))
          properties['dew_point:F']=float(obs.dewpt.string('F').replace(' F',''))
          properties['dew_point:K']=float(obs.dewpt.string('K').replace(' K',''))
        if obs.press is not None:
          properties['pressure:hPa']=float(obs.press.string('HPA').replace(' hPa',''))
          properties['pressure:in']=float(obs.press.string('IN').replace(' inches',''))
        if obs.wind_dir is not None:
          properties['wind_dir:compass']=obs.wind_dir.compass()
          properties['wind_dir:degrees']=float(obs.wind_dir.string().replace(' degrees',''))
        if obs.wind_speed is not None:
          properties['wind_speed:kmh']=float(obs.wind_speed.string('KMH').replace(' km/h',''))
          properties['wind_speed:mph']=float(obs.wind_speed.string('MPH').replace(' mph',''))
          properties['wind_speed:ms']=float(obs.wind_speed.string('MPS').replace(' mps',''))
        if obs.wind_gust is not None:
          properties['wind_gust:kmh']=float(obs.wind_gust.string('KMH'))
          properties['wind_gust:mph']=float(obs.wind_gust.string('MPH').replace(' mph',''))
          properties['wind_gust:ms']=float(obs.wind_gust.string('MPS').replace(' mps',''))
        if obs.vis is not None:
          properties['visibility:km']=obs.vis.string('KM').replace('greater than ','>').replace(' km','')
          properties['visibility:miles']=obs.vis.string('MI').replace('greater than ','>').replace(' miles','')

        # create geojson
        geojson = json.dumps(dict(type='Feature', properties=properties, geometry=json.loads(g[0])),sort_keys=True)

        # send it to OEDB API
        r = requests.post(api+'/event', data = geojson)
        if r.status_code == 201 :
          event = json.loads(r.text)
          #print("POST:"+event['id'])
        else:
          # something went wrong...
          if r.text>'':
            print(r.status_code+": "+r.text)
  except:
    pass
