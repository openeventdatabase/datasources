# récupération des données sur openagenda
mkdir 2016
for i in `seq 1 140`; do curl "https://openagenda.com/agendas/7633600/events.json?page=$i" -s > 2016/fete$i; echo $i; done

# extraction en geojson des infos nous intéressant
jq .events[] 2016/fete{1..140} | jq -s '.[]|([.title.fr, " / ", .range.fr] | add) as $name | {type: "Feature",properties:{type:"scheduled",what:"culture.music","openagenda:uid": .uid,"where:name": .locationName,"where:address": .address,"openagenda:url":.canonicalUrl,name: .title.fr,"name:en":.title.en,"when":.timings[].start, "when:fr": .range.fr},geometry:{type:"Point",coordinates:[.longitude,.latitude]}}' -c > fete2016.json

# envoi vers l'API
IFS=$'\n'
for e in `cat fete2016.json`; do
  echo $e | http POST http://api.openeventdatabase.org/event
done
