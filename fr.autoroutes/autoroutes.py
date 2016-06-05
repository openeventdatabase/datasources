# Ecrit par Christian Quest le 8/5/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/openeventdatabase/datasources

import requests
import sys
import json
import re
import psycopg2

# This function is free of any dependencies.
# source: https://github.com/mgd722/decode-google-maps-polyline
def decode_polyline(polyline_str):
    '''Pass a Google Maps encoded polyline string; returns list of lat/lon pairs'''
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']: 
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index+=1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append((lat / 100000.0, lng / 100000.0))

    return coordinates


e_when=sys.argv[2]

db = psycopg2.connect("dbname=osm")
cur = db.cursor()

with open(sys.argv[1]) as json_file:
    data = json.load(json_file)
    for e in data['Placemarks']:
      e_what = 'traffic'
      if e['Preview'][:8]=='ACCIDENT':
        e_what = 'traffic.accident'
      if e['Preview'][:8]=='OBSTACLE':
        e_what = 'traffic.obstacle'
      if e['Preview'][:10]=='BROUILLARD':
        e_what = 'weather.warning.fog'
      if e['Preview'][:7]=='BOUCHON':
        e_what = 'traffic.jam';

      label = e['Metadatas']['AUTOROUTE']
      if e['Metadatas']['DIRECTION'] != '':
        label = label +' vers '+e['Metadatas']['DIRECTION']
      label = label + ': ' + e['Preview']

      # décodage polyline pour récupérer la bonne extrémité
      geo = decode_polyline(e['Lines'][0])
      lat,lon = geo[0]

      geometry = dict(type = 'Point', coordinates = [lon,lat])
      geojson=dict(type='Feature', properties=dict(type='unscheduled', what=e_what, when=e_when, source='http://www.vinci-autoroutes.com/', label=label), geometry=geometry)
      r = requests.post('http://api.openeventdatabase.org/event', data = json.dumps(geojson))
      #print(json.dumps(geojson))
