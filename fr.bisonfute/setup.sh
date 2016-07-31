psql oedb -c "create table bison_fute_zones (dep text, zone text);"
psql oedb -c "\copy bison_fute_zones from ZonesBisonFuté.csv with (format csv, header true);"
psql oedb -c "create materialized view bison_fute_geo as select zone, st_snaptogrid(st_union(wkb_geometry),0.00001) as geom FROM bison_fute_zones b join departements d on (d.insee=b.dep) group by 1;"

