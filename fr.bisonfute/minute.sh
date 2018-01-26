HIERYY=$(date --date="-1 day" +'%Y')
HIERMM=$(date --date="-1 day" +'%m')
HIER=$(date --date="-1 day" +'%Y-%m-%d')

mkdir -p `date +%Y-%m`
f=`date +%Y-%m`/bison-fute-`date +%Y-%m-%dT%H:%M:00%z`.json
l="last.json"
~/.virtualenvs/oedb/bin/python bisonfute.py > $f
# ~/.virtualenvs/oedb/bin/python parks.py
if diff $f $l  >/dev/null
then
  rm $f
  touch -h $l
else
  ln -fs $f $l
fi

# archivage des données de la veille
7z a $HIERYY.7z $HIERYY-$HIERMM/*$HIER* && rm $HIERYY-$HIERMM/*$HIER*
