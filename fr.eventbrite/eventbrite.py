import config
import requests
import json
import hashlib
import sqlite3

api_eventbrite = 'https://www.eventbriteapi.com/v3'

# adresse de l'API
api ='http://api.openeventdatabase.org'

# base sqlite pour suivre l'évolution des événements d'un run au suivant
sql = sqlite3.connect('eventbrite.db')
db = sql.cursor()
db.execute('CREATE TABLE IF NOT EXISTS evt (oedb_id text, eventbrite_id text, hash text)')


r = requests.get(api_eventbrite+'/events/search?expand=venue&location.latitude=48.85&location.longitude=2.35&location.within=30km&categories=103,104,105,108,109', headers=config.auth_eventbrite)

events = json.loads(r.text)

for e in events['events']:
  if e['category_id']=='103':
    e_what = 'culture.music'
  elif e['category_id']=='104':
    e_what = 'culture.entertainment'
  elif e['category_id']=='105':
    e_what = 'culture.arts'
  elif e['category_id']=='108':
    e_what = 'sport'

  if 'subcatecory_id' in e:
    if e['subcategory_id']=='5002':
      e_what = 'culture.arts.musical'
    elif e['subcategory_id']=='5003':
      e_what = 'culture.arts.ballet'
    elif e['subcategory_id']=='5004':
      e_what = 'culture.arts.dance'
    elif e['subcategory_id']=='5001':
      e_what = 'culture.arts.theatre'
    elif e['subcategory_id']=='4004':
      e_what = 'culture.entertainment.gaming'
    elif e['subcategory_id']=='4003':
      e_what = 'culture.entertainment.anime'
    elif e['subcategory_id']=='4002':
      e_what = 'culture.entertainment.film'
    elif e['subcategory_id']=='4001':
      e_what = 'culture.entertainment.tv'
    elif e['subcategory_id']=='3017':
      e_what = 'culture.music.rock'
    elif e['subcategory_id']=='3016':
      e_what = 'culture.music.religious'
    elif e['subcategory_id']=='3015':
      e_what = 'culture.music.reggae'
    elif e['subcategory_id']=='3014':
      e_what = 'culture.music.rnb'
    elif e['subcategory_id']=='3013':
      e_what = 'culture.music.pop'
    elif e['subcategory_id']=='3012':
      e_what = 'culture.music.opera'
    elif e['subcategory_id']=='3011':
      e_what = 'culture.music.metal'
    elif e['subcategory_id']=='3010':
      e_what = 'culture.music.latin'
    elif e['subcategory_id']=='3009':
      e_what = 'culture.music.indie'
    elif e['subcategory_id']=='3008':
      e_what = 'culture.music.rap'
    elif e['subcategory_id']=='3007':
      e_what = 'culture.music.folk'
    elif e['subcategory_id']=='3006':
      e_what = 'culture.music.electronic'
    elif e['subcategory_id']=='3005':
      e_what = 'culture.music.cultural'
    elif e['subcategory_id']=='3004':
      e_what = 'culture.music.country'
    elif e['subcategory_id']=='3003':
      e_what = 'culture.music.classical'
    elif e['subcategory_id']=='3002':
      e_what = 'culture.music.jazz'
    elif e['subcategory_id']=='3001':
      e_what = 'culture.music.alternative'
    else:
      subcat = dict(s8001='sport.running',s8002='sport.walking',s8003='sport.cycling',
        s8004='sport.mountain_bike',s8006='sport.basketball',s8007='sport.football',s8008='sport.baseball',
        s8009='sport.soccer',s8010='sport.golf',s8011='sport.volleyball',s8012='sport.tennis',
        s8013='sport.swimming',s8014='sport.hockey',s8015='sport.motorsports',s8016='sport.fighting',
        s8017='sport.snow',s8018='sport.rugby',s8019='sport.yoga',s8020='sport.excercise',
        s9001='sport.hiking',s9002='sport.rafting',s9003='sport.kayaking',s9004='canoeing',
        s9005='sport.climbing')
      if 's'+e['subcategory_id'] in subcat:
        e_what = subcat['s'+e['subcategory_id']]

  e_type = 'scheduled'
  e_start = e['start']['utc']
  e_stop = e['end']['utc']
  e_source = e['resource_uri']
  e_text = e['name']['text']
  e_geom = dict(type = 'Point', coordinates = [round(float(e['venue']['longitude']),6), round(float(e['venue']['latitude']),6)])

  properties = dict(type=e_type, what=e_what, source=e_source, start=e_start, stop=e_stop, name=e_text, url=e['url'])

  if e['venue']['name'] is not None:
    properties['where:name'] = e['venue']['name']
  if e['capacity'] is not None:
    properties['capacity'] = e['capacity']
  if e['logo'] is not None:
    properties['image'] = e['logo']['url']

  geojson = json.dumps(dict(type='Feature', geometry=e_geom, properties=properties),sort_keys=True)

  md5 = hashlib.md5(str(geojson).encode()).hexdigest()
  db.execute('SELECT oedb_id, hash FROM evt WHERE eventbrite_id = ?',(e['id'],))
  last = db.fetchone()
  # do we have an existing event ?
  if last is not None:
    # update if event has changed (different hash)
    if last[1] != md5:
      #print("PUT: "+last[0])
      r = requests.put(api+'/event/'+last[0], data = geojson)
      db.execute("UPDATE evt SET hash = ? WHERE oedb_id = ?", (md5, last[0]))
  else:
    r = requests.post(api+'/event', data = geojson)
    if r.status_code == 201:
      oedb = json.loads(r.text)
      #print("POST:"+oedb['id'])
      db.execute("INSERT INTO evt VALUES ( ? , ? , ? )", (oedb['id'], e['id'], md5))

sql.commit()
db.close()

