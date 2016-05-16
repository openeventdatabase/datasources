wget -nc "http://osm13.openstreetmap.fr/~cquest/openfla/export/communes-20160119-shp.zip"
unzip -o communes-20160119-shp.zip
ogr2ogr -f postgresql PG:"dbname=oedb" communes-20160119.shp -nln communes -nlt geometry

psql oedb -c "
create index communes_insee on communes (insee);
alter table communes drop ogc_fid;
alter table communes drop surf_ha;
"

wget -nc "http://osm13.openstreetmap.fr/~cquest/openfla/export/departements-20160218-shp.zip"
unzip -o departements-20160218-shp.zip
ogr2ogr -f postgresql PG:"dbname=oedb" departements-20160218.shp -nln departements -nlt geometry

psql oedb -c "
create index departements_insee on departements (insee);
alter table departements drop ogc_fid;
alter table departements drop surf_ha;
"
