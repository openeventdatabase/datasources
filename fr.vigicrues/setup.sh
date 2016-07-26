# récupération liste et position des stations de mesure
wget -nc http://services.sandre.eaufrance.fr/telechargement/geo/HYD/StationHydro/FXX/StationHydro_FXX-shp.zip
unzip StationHydro_FXX-shp.zip
# conversion en geojson
ogr2ogr -f GeoJSON stations.json StationHydro_FXX.shp



# récup liste des stations sur vigicrue
rm stations.txt
for z in `seq 1 25` 200; do
  curl -s http://www.vigicrues.gouv.fr/niveau2.php?CdEntVigiCru=$z | grep niveau3 | sed 's/^.*CdStationHydro=//;s/" target.*$//' >> stations.txt
done

# récup infos de chaque station
mkdir -p stations
for s in `cat stations.txt`; do
  curl -s "http://www.vigicrues.gouv.fr/niveau3.php?CdStationHydro=$s&ong=3" > stations/$s.html
done
echo "id,X,Y" > stations.csv
# extraction X/Y lambert
for s in `cat stations.txt`; do
  echo -n "$s," >> stations.csv
  egrep "X=.* m, Y=.* m" -o stations/$s.html | sed 's/X=//;s/ m, Y=/,/;s/ m//'  >> stations.csv
done

# récupération mesures en HTML (site public)
mkdir -p mesures
for s in `cat stations.txt`; do
  curl -s "http://www.vigicrues.gouv.fr/hackathon2016/observations.xml/?CdStationHydro=$s" > mesures/$s.xml
done


# récupération mesures en XML
mkdir -p mesures
for s in `cat stations.txt`; do
  curl -s "http://www.vigicrues.gouv.fr/hackathon2016/observations.xml/?CdStationHydro=$s" > mesures/$s.xml
done

# download troncons vigicrues (source SANDRE)
wget -nc http://services.sandre.eaufrance.fr/telechargement/geo/VIC/EntVigiCru/FXX/EntVigiCru_FXX-shp.zip
unzip EntVigiCru_FXX-shp.zip
# import postgis
ogr2ogr -f "PostgreSQL" PG:"dbname=oedb" -t_srs EPSG:4326 -nlt GEOMETRY -nln vigicrues-troncons EntVigiCru_FXX-shp/EntVigiCru.shp
rm -rf EntVigiCru_FXX*
# make index
psql oedb -c "
alter table vigicrues_troncons drop column ogc_fid;
update vigicrues_troncons set wkb_geometry = st_snaptogrid(wkb_geometry,0.000001);
create index vigicrues_troncons_idx_id on vigicrues_troncons (cdentvigic);
"

