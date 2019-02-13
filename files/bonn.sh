#!/bin/bash

# Vars
B1=$1 #"13.3863801,52.510189,13.3928171,52.5158761"
B2=`echo $B1 | tr ',' ' '`
MIN_SPEED=$6
MAX_SPEED=$7
DURATION=$8
CLIPPING=$9
PAUSE=$10
map_files_location=$11
pbf_file_name=$12
convert_file_name=$13
OFFSET=$14

function oneRound() {
	i=$1
	if [ ! -f berlin-latest-${B1}-${N}-${i}.movements.gz ]; then
		# Run script
		../bin/bm -f berlin-latest-${B1}-${N}-${i} RandomStreet -n ${N} -B ${B2} -u http://localhost:5000 -s ${MIN_SPEED} ${MAX_SPEED} -C ${CLIPPING} -p ${PAUSE} -d ${DURATION} -o ${map_files_location}/${pbf_file_name}.osm.pbf
		retVal=$?
		if [ $retVal -ne 0 ]; then
			echo "ERROR"
			exit 1
		fi
	fi
	
	python3 ${convert_file_name} ${pbf_file_name}-${B1}-${N}-${i}.movements.geo.gz ${map_files_location}/${pbf_file_name}-${B1}.buildings.xml ${OFFSET}
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
		# if [ ! -f ${pbf_file_name}-${B1}-${N}-${i}.ns_params ]; then
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
TOTALRUNS=$2 #500
CORES=$3 #10
FIRSTI=$4 #0
PERCORE=$(($TOTALRUNS/$CORES))

for i in ${$5[@]}; do
	N=$i
	runOnCores&
	wait
done

