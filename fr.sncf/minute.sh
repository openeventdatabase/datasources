mkdir -p `date +%Y-%m`
f=`date +%Y-%m`/transilien-trafic-`date +%Y-%m-%dT%H:%M:00%z`.xml
l="last-transilien-traffic.xml"
curl "https://www.transilien.com/flux/rss/trafic" -s > $f
# ~/.virtualenvs/oedb/bin/python parks.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

f=`date +%Y-%m`/transilien-travaux-`date +%Y-%m-%dT%H:%M:00%z`.xml
l="last-transilien-travaux.xml"
curl "https://www.transilien.com/flux/rss/travaux" -s > $f
# ~/.virtualenvs/oedb/bin/python parks.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi
