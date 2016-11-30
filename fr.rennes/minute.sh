mkdir -p `date +%Y-%m`
f=`date +%Y-%m`/parks-`date +%Y-%m-%dT%H:%M:00%z`.json
l="last-parks.json"
curl "http://data.citedia.com/r1/parks?crs=EPSG:4326" -s > $f
# ~/.virtualenvs/oedb/bin/python parks.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

f=`date +%Y-%m`/star-altertes-`date +%Y-%m-%dT%H:%M:00%z`.json
l="last-star-alertes.json"
curl "https://data.rennesmetropole.fr/explore/dataset/alertes-trafic-en-temps-reel-sur-les-lignes-du-reseau-star/download/?format=json&timezone=Europe/Paris" -s > $f
# ~/.virtualenvs/oedb/bin/python parks.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

f=`date +%Y-%m`/star-position-bus-`date +%Y-%m-%dT%H:%M:00%z`.json
l="last-star-position-bus.json"
curl "https://data.rennesmetropole.fr/explore/dataset/position-des-bus-en-circulation-sur-le-reseau-star-en-temps-reel/download/?format=geojson&timezone=Europe/Paris" -s > $f
# ~/.virtualenvs/oedb/bin/python parks.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

f=`date +%Y-%m`/star-etat-metro-`date +%Y-%m-%dT%H:%M:00%z`.json
l="last-star-etat-metro.json"
curl "https://data.rennesmetropole.fr/explore/dataset/etat-des-lignes-de-metro-du-reseau-star-en-temps-reel/download/?format=json&timezone=Europe/Paris" -s > $f
# ~/.virtualenvs/oedb/bin/python parks.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

f=`date +%Y-%m`/star-etat-equip-`date +%Y-%m-%dT%H:%M:00%z`.json
l="last-star-etat-equip.json"
curl "https://data.rennesmetropole.fr/explore/dataset/etat-des-equipements-des-stations-de-metro-du-reseau-star-en-temps-reel/download/?format=geojson&timezone=Europe/Paris" -s > $f
# ~/.virtualenvs/oedb/bin/python parks.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

f=`date +%Y-%m`/etat-park-relais-`date +%Y-%m-%dT%H:%M:00%z`.json
l="last-etat-park-relais.json"
curl "https://data.rennesmetropole.fr/explore/dataset/etat-des-parcs-relais-du-reseau-star-en-temps-reel/download/?format=geojson&timezone=Europe/Paris" -s > $f
# ~/.virtualenvs/oedb/bin/python parks.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

f=`date +%Y-%m`/travaux-`date +%Y-%m-%dT%H:%M:00%z`.json
l="last-travaux.json"
curl "http://travaux.data.rennesmetropole.fr/api/roadworks?epsg=4326" -s > $f
# ~/.virtualenvs/oedb/bin/python parks.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

