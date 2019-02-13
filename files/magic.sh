#!/bin/bash

# Load paramaters from config files
source config.shlib; # load the config library functions

map_files_location="$(config_get map_files_location)"
buildings_typ_link="$(config_get buildings_typ_link)"
osrm_build_folder="$(config_get osrm_build_folder)"
convert_file_link="$(config_get convert_file_link)"
convert_file_name="$(config_get convert_file_name)"
bm_run_location="$(config_get bm_run_location)"
bm_script_link="$(config_get bm_script_link)"
bm_script_name="$(config_get bm_script_name)"
ns_script_link="$(config_get bm_script_link)"
ns_script_name="$(config_get bm_script_name)"
pbf_continent="$(config_get pbf_continent)"
pbf_file_name="$(config_get pbf_file_name)"
ns_code_link="$(config_get ns_code_link)"
ns_code_name="$(config_get ns_code_name)"
pbf_country="$(config_get pbf_country)"
ns_location="$(config_get ns_location)"
num_cores="$(config_get num_cores)"
port="$(config_get port)"
MIN_SPEED="$(config_get MIN_SPEED)"
MAX_SPEED="$(config_get MAX_SPEED)"
DURATION="$(config_get DURATION)"
CLIPPING="$(config_get CLIPPING)"
PAUSE="$(config_get PAUSE)"
OFFSET="$(config_get OFFSET)"
B="$(config_get B)"
BM_TOTALRUNS="$(config_get BM_TOTALRUNS)"
BM_CORES="$(config_get BM_CORES)"
BM_FIRSTI="$(config_get BM_FIRSTI)"
BM_NODES="$(config_get BM_NODES)"
NS_NODES="$(config_get NS_NODES)"
NS_ATTACKTYPE="$(config_get NS_ATTACKTYPE)"
NS_ATTACKLOC="$(config_get NS_ATTACKLOC)"
NS_DEFENCE="$(config_get NS_DEFENCE)"



#Prepare maps

if [ ! -f ${map_files_location}/${pbf_file_name}.osm.pbf ]; then
	wget "http://download.geofabrik.de/${pbf_continent}/${pbf_country}/${pbf_file_name}.osm.pbf" -P ${map_files_location}/
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi
fi

if [ ! -f ${map_files_location}/${buildings_typ_link} ]; then
	wget ${buildings_typ_link} -P ${map_files_location}/
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi
fi

if [ ! -f ${map_files_location}/${pbf_file_name}.osm ]; then
	cd ${map_files_location}
	osmconvert ${pbf_file_name}.osm.pbf -o=${pbf_file_name}.osm
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi

	cd ${osrm_build_folder}
	./prepare_pbf.sh ${map_files_location}/${pbf_file_name}
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi
fi


sudo killall -q start_routed.sh
#Run map server
sudo -b ./start_routed.sh ${map_files_location}/${pbf_file_name}.osrm ${port} ${num_cores}
if [ $retVal -ne 0 ]; then
	echo "ERROR"
	exit 1
fi

#Create map files
if [ ! -f ${map_files_location}/${pbf_file_name}-${B}.net.xml ]; then
	if [ ! -d ${bm_run_location} ]; then
		mkdir ${bm_run_location}
	fi
	cd ${bm_run_location}
	netconvert --remove-edges.isolated --keep-edges.in-geo-boundary ${B} --osm-files ${map_files_location}/${pbf_file_name}.osm -o ${map_files_location}/${pbf_file_name}-${B}.net.xml
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi
fi

if [ ! -f ${map_files_location}/${pbf_file_name}-${B}.buildings.xml ]; then
	if [ ! -d ${bm_run_location} ]; then
		mkdir ${bm_run_location}
	fi
	cd ${bm_run_location}
	polyconvert --prune.in-net --osm.keep-full-type --net-file ${map_files_location}/${pbf_file_name}-${B}.net.xml --osm-files ${map_files_location}/${pbf_file_name}.osm --type-file ${map_files_location}/buildings.typ.xml -o ${map_files_location}/${pbf_file_name}-${B}.buildings.xml
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi
fi

if [ ! -f ${bm_run_location}/${convert_file_name} ]; then
	wget ${convert_file_link}
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi
fi

if [ ! -f ${bm_run_location}/${bm_script_name} ]; then
	wget ${bm_script_link}
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi
fi

nohup ./${bm_script_name} ${B} ${BM_TOTALRUNS} ${BM_CORES} ${BM_FIRSTI} "${BM_NODES[*]}" ${MIN_SPEED} ${MAX_SPEED} ${DURATION} ${CLIPPING} ${PAUSE} ${map_files_location} ${pbf_file_name} ${convert_file_name} ${OFFSET} &

#Run ns simulation
if [ ! -f ${ns_location}/scratch/${ns_code_name} ]; then
	wget ${ns_code_link} -P ${ns_location}/scratch/
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi
fi
cd ${ns_location}
./waf configure --build-profile=optimized --enable-examples --enable-tests
./waf --run scratch/${ns_code_name}

if [ ! -f ${ns_location}/run/${ns_script_name} ]; then
	wget ${ns_script_link} -P ${ns_location}/run/
	chmod +x ${ns_location}/run/${ns_script_name}
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi
fi
cd ${ns_location}/run/
nohup ./${ns_script_name} ${bm_run_location} ${B} ${map_files_location} ${pbf_file_name} ${ns_location} ${ns_code_name} ${NS_TOTALRUNS} ${NS_CORES} ${NS_FIRSTI} "${NS_NODES[*]}" "${NS_ATTACKTYPE[*]}" "${NS_ATTACKLOC[*]}" "${NS_DEFENCE[*]}" &

python3 getAvg.py "${NS_NODES[*]}" "${NS_ATTACKTYPE[*]}" "${NS_ATTACKLOC[*]}" "${NS_DEFENCE[*]}"
