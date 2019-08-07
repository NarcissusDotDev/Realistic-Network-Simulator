#!/bin/bash
HOME=$(readlink -f ~)
export LD_LIBRARY_PATH="${HOME}/ns-allinone-3.19/ns-3.19/build/"

bm_run_location=$1
B=$2
map_files_location=$3
pbf_file_name=$4
ns_location=$5
ns_code_name=$6
buildings=${13}
BLDGFILE="${map_files_location}/${pbf_file_name}-${B}.buildings.xml"

function runScript() {
	OFFSET=$1

	local NS_NAME="${bm_run_location}/${pbf_file_name}-${B}-${N}-${OFFSET}"
	local NS_PARAMS="${NS_NAME}.ns_params"
	local NS_MOVEMENTS="${NS_NAME}.ns_movements"
		
    # Run script
    NS_GLOBAL_VALUE="RngRun=$((OFFSET+FIRSTI))" ${ns_location}/build/scratch/${ns_code_name}--paramsFile=$NS_PARAMS --traceFile=$NS_MOVEMENTS --bMobility=true --bHighRange=true --bUdpServer=true --bMakeBets=true --bFixPos=1 --bRigPath=false --bPrintNeighbors=true --bPrintTwoHops=false --bPrintSelectedTC=true --bPrintMPR=true --bldgFile=$BLDGFILE --bBuildings=${buildings} >> $BETSFILE
    if [ $? -ne 0 ]; then
        echo "ERROR"
        exit 1
    fi
}


function runMultiple() {
    R=$1

    # Create temp folder to run from
    MYTEMPDIR=$(mktemp -dp .)
    local FILE="../BottleNeckNeighbors_n${N}_${X}x${Y}_FixPos-${FIXPOS}-Mobility-${MOBILITY}-"
    local BETSFILE="${FILE}betlist-r${R}.txt"
    local PACKETSFILE="${FILE}packets-r${R}.txt"
    local NEIGHBORSFILE="${FILE}neighbors-r${R}.txt"
    local TCSFILE="${FILE}tcs-r${R}.txt"
    local MPRFILE="${FILE}mpr-r${R}.txt"
    #local TWOHOPFILE="${FILE}twohops-r${R}.txt"
    local BETSFILETOTAL="${FILE}betlist.txt"
    local PACKETSFILETOTAL="${FILE}packets.txt"
    local NEIGHBORSFILETOTAL="${FILE}neighbors.txt"
    local TCSFILETOTAL="${FILE}tcs.txt"
    local MPRFILETOTAL="${FILE}mpr.txt"
    #local TWOHOPFILETOTAL="${FILE}twohops.txt"
	
    cd $MYTEMPDIR

    for ((i=$2;i<$3;i+=1)); do
        echo "This is run $i" >> $BETSFILE
        echo "This is run $i" >> $PACKETSFILE
        echo "This is run $i" >> $NEIGHBORSFILE
        echo "This is run $i" >> $TCSFILE
        echo "This is run $i" >> $MPRFILE
        # echo "This is run $i" >> $TWOHOPFILE
		
		runScript $i
		# Extract packets
        mergecap -w tmp.pcap BottleNeck_FixPos_1*.pcap
        tcpdump -n -tt -e -r tmp.pcap | grep -i UDP | uniq -u | awk '{print $1, $2, $3, $4}' >> $PACKETSFILE
	    
        # Extract Neighbors / Two Hops / MPR / TC
        cat neighbors_solsr.txt >> $NEIGHBORSFILE
        cat tcs_solsr.txt >> $TCSFILE
        cat mpr_solsr.txt >> $MPRFILE
        #cat twohops_solsr.txt >> $TWOHOPFILE
	    
        # Clean
        rm BottleNeck_FixPos_1*.pcap
        rm tmp.pcap
        rm neighbors_solsr.txt
        rm tcs_solsr.txt
        rm mpr_solsr.txt
        #rm twohops_solsr.txt
		
		local d=`date`
		echo Finished ns run $i on process $R at $d
	done
	
    # Pack result
    flock -e $PACKETSFILETOTAL cat $PACKETSFILE >> $PACKETSFILETOTAL
    flock -e $BETSFILETOTAL cat $BETSFILE >> $BETSFILETOTAL
    flock -e $NEIGHBORSFILETOTAL cat $NEIGHBORSFILE >> $NEIGHBORSFILETOTAL
    flock -e $TCSFILETOTAL cat $TCSFILE >> $TCSFILETOTAL
    flock -e $MPRFILETOTAL cat $MPRFILE >> $MPRFILETOTAL
    #flock -e $TWOHOPFILETOTAL cat $TWOHOPFILE >> $TWOHOPFILETOTAL

    mkdir -p ../tmpdel
    mv $PACKETSFILE ../tmpdel
    mv $BETSFILE ../tmpdel
    mv $NEIGHBORSFILE ../tmpdel
    mv $TCSFILE ../tmpdel
    mv $MPRFILE ../tmpdel
    # delete temp folder
    cd ..
    rm -R $MYTEMPDIR
}

# Call function to run on cores
function runOnCores(){
    for ((i=0;i<$CORES;i+=1)); do
      FROM=$(( $FIRSTI + $PERCORE * $i ))
      TO=$(( $FROM + $PERCORE ))
      runMultiple $i $FROM $TO &
    done

    wait
    # Leftovers
    FROM=$(($FIRSTI + $PERCORE*$CORES))
    if [ $TOTALRUNS -gt $FROM ]; then
      runMultiple $CORES $FROM $TOTALRUNS
    fi
    wait
}

set -m # Don\'t lose job control!
# Make sure TOTALRUNS % CORES = 0. Otherwise there would be leftover process.
TOTALRUNS=$7
CORES=$8
FIRSTI=$9
PERCORE=$(($TOTALRUNS/$CORES))

for i in ${10}; do
	N=$i
	#for MOBILITY in "false" "true"; do
	# for MOBILITY in "true"; do
	runOnCores&
	wait
	# done
done
