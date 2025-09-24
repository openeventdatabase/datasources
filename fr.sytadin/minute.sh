#! /bin/bash

# sytadin
mkdir -p `date +%Y-%m`
t=`date +%Y-%m-%dT%H:%M:00%z -d '+2 minutes'`
f="`date +%Y-%m`/fr.sytadin-$t.json"
l="last.json"
curl -sL "http://www.sytadin.fr/carto/dynamique/`curl -sL 'http://www.sytadin.fr/carto/dynamique/cartoTempsReel.json' | jq .dossier -r`/evenements/troncon.json" > $f
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
elif [ $(wc -c < $f) -lt 250 ]
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi
~/.virtualenvs/oedb/bin/python sytadin.py $l "$t"
