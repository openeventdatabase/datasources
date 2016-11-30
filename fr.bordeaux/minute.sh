mkdir -p `date +%Y-%m`
f=`date +%Y-%m`/trafic-`date +%Y-%m-%dT%H:%M:00%Z`.csv
l="last-trafic.csv"
curl "http://data.bordeaux-metropole.fr/files.php?gid=80&format=6" -s > $f
# ~/.virtualenvs/oedb/bin/python trafic.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

mkdir -p `date +%Y-%m`
f=`date +%Y-%m`/message-`date +%Y-%m-%dT%H:%M:00%Z`.csv
l="last-messages.csv"
curl "http://data.bordeaux-metropole.fr/files.php?gid=599&format=6" -s | iconv -f iso8859-1 -t utf-8 - > $f
# ~/.virtualenvs/oedb/bin/python trafic.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi
