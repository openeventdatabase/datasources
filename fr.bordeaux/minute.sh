HIERYY=$(date --date="-1 day" +'%Y')
HIERMM=$(date --date="-1 day" +'%m')
HIER=$(date --date="-1 day" +'%Y-%m-%d')

mkdir -p `date +%Y-%m`
f=`date +%Y-%m`/trafic-`date +%Y-%m-%dT%H:%M:00%Z`.csv
l="last-trafic.csv"
curl -L "https://data.bordeaux-metropole.fr/files.php?gid=80&format=6" -s > $f

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
curl -L "https://data.bordeaux-metropole.fr/files.php?gid=599&format=6" -s | iconv -f iso8859-1 -t utf-8 - > $f
# ~/.virtualenvs/oedb/bin/python trafic.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

7z a $HIERYY.7z $HIERYY-$HIERMM/*$HIER* && rm $HIERYY-$HIERMM/*$HIER*
