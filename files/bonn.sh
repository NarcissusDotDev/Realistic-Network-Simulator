#!/bin/bash

# Vars
B1="13.3863801,52.510189,13.3928171,52.5158761"
B2=`echo $B1 | tr ',' ' '`
OFFSET=10

#netconvert --remove-edges.isolated --keep-edges.in-geo-boundary ${B1} --osm-files ../maps/berlin-latest.osm -o ../maps/berlin-latest-${B1}.net.xml
#polyconvert --prune.in-net --osm.keep-full-type --net-file ../maps/berlin-latest-${B1}.net.xml --osm-files ../maps/berlin-latest.osm --type-file ../maps/buildings.typ.xml -o ../maps/berlin-latest-${B1}.buildings.xml  

function oneRound() {
	i=$1
	
	if [ ! -f berlin-latest-${B1}-${N}-${i}.movements.gz ]; then
		# Run script
		../bin/bm -f berlin-latest-${B1}-${N}-${i} RandomStreet -n ${N} -B ${B2} -u http://localhost:5000 -s 1.5 2 -C 1 -p 30 -d 300 -o ../maps/berlin-latest.osm.pbf
		retVal=$?
		if [ $retVal -ne 0 ]; then
			echo "ERROR"
			exit 1
		fi
	fi
	
	python3 convert.py berlin-latest-${B1}-${N}-${i}.movements.geo.gz ../maps/berlin-latest-${B1}.buildings.xml ${OFFSET}
	retVal=$?
	if [ $retVal -ne 0 ]; then
		echo "ERROR"
		exit 1
	fi
	../bin/bm NSFile -f berlin-latest-${B1}-${N}-${i} -b > /dev/null
	retVal=$?
	if [ $retVal -ne 0 ]; then
	    echo "ERROR"
	    exit 1
	fi
}

function runScript () {
  R=$1

  for ((i=$2;i<$3;i+=1)); do
    #echo "This is run $i" >> $LOGFILE
    # if [ ! -f berlin-latest-${B1}-${N}-${i}.ns_params ]; then
	oneRound $i > /dev/null
	local d=`date`
	echo Finished run $i on process $R at $d
    # fi
  done
  echo Finished all runs at $d
}

# Call function to run on cores
function runOnCores(){
for ((i=0;i<$CORES;i+=1)); do
  FROM=$(( $FIRSTI + $PERCORE * $i ))
  TO=$(( $FROM + $PERCORE ))
  runScript $i $FROM $TO &
  #echo $i $FROM $TO
done

# Leftovers
FROM=$(($FIRSTI + $PERCORE*$CORES)) 
if [ $TOTALRUNS -gt $FROM ]; then
  #echo $CORES $FROM $TOTALRUNS
  runScript $CORES $FROM $TOTALRUNS
fi
wait
}


set -m # Don\'t lose job control!
# Make sure TOTALRUNS % CORES = 0. Otherwise there would be leftover process.
TOTALRUNS=500
CORES=10
FIRSTI=0
PERCORE=$(($TOTALRUNS/$CORES))

for ((N=30; N<= 100; N+=100)); do
  runOnCores&
  wait
done

