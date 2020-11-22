# Installation and Use

## Requirements:

*   Ubuntu 16.04.4 LTS (Xenial Xerus)
*   JDK
*   Non-root user with sudo privileges

1. [Install the software-properties-common package](http://lifeonubuntu.com/ubuntu-missing-add-apt-repository-command/):
`sudo apt install software-properties-common` 

2. Add missing repositories:
`sudo add-apt-repository universe`
`sudo add-apt-repository ppa:sumo/stable`

3. Update apt:
`sudo apt update`

4. Install requirements:
`sudo apt install default-jdk build-essential git cmake pkg-config libbz2-dev libstxxl-dev libstxxl1v5 libxml2-dev libzip-dev libboost-all-dev lua5.2 liblua5.2-dev libtbb-dev libluabind-dev libluabind0.9.1v5 gcc-4.7 g++-4.7 g++-4.7-multilib python python-dev python-setuptools mercurial bzr libc6-dev libc6-dev-i386 libxml2 sqlite sqlite3 libsqlite3-dev tcpdump flex bison libfl-dev uncrustify vtun lxc libboost-signals-dev libboost-filesystem-dev openmpi-bin openmpi-common openmpi-doc libopenmpi-dev gsl-bin libgsl-dev libgsl2 libcgal-dev qt5-default sumo sumo-tools sumo-doc osmctools python3 python3-pip`

5. Install python packages:
`sudo pip3 install pyproj numpy`

## Setup:

### [BonnMotion](http://sys.cs.uos.de/bonnmotion/)

1.  Go to home directory:
`cd ~`

2.  Download BonnMotion:
`wget http://sys.cs.uos.de/bonnmotion/src/bonnmotion-3.0.0.zip`

3.  Extract:
`unzip bonnmotion-3.0.0.zip` 

4.  [Optional] Remove the zip:
`rm bonnmotion-3.0.0.zip`

5.  Change directory to extracted folder:
`cd bonnmotion-3.0.0/`

6.  Run the installation script:
`./install`  (it finds your Java installation path automatically).

7. After successfully installing it should print something like this:
     ```bash
     $ ./bin/bm -h
     BonnMotion 3.0.0
     
     OS: YOUR_LINUX_DISTRIBUTION
     Java: YOUR_JAVA_VERSION
     
     
     Help:
       -h                    	Print this help

     Scenario generation:
       -f <scenario name> [-I <parameter file>] <model name> [model options]
       -hm                           Print available models
       -hm <module name>             Print help to specific model
     
     Application:
       <application name> [Application-Options]
       -ha                           Print available applications
       -ha <application name>        Print help to specific applications
     ```

8. Change GC options:
`sed -i -e 's/-Xmx512m -Xss10m/-XX:-UseGCOverheadLimit -XX:+UseConcMarkSweepGC -Xmx10G -Xss1G/g' ./bin/bm`

### [OSRM](https://github.com/Project-OSRM/osrm-backend)

1.  Go to home directory using:
`cd ~`

2.  Download OSRM v4.8.1:
`wget https://github.com/Project-OSRM/osrm-backend/archive/v4.8.1.tar.gz`

3.  Extract:
`tar -xzf v4.8.1.tar.gz` 

4.  [Optional] Remove  the tar:
`rm v4.8.1.tar.gz`

5.  Change directory to the following folder:
`cd osrm-backend-4.8.1/third_party/variant`

Now we need to replace some files with files from [this](https://github.com/Project-OSRM/osrm-backend/tree/a62c10321c0a269e218ab4164c4ccd132048f271/third_party/variant) version.

1.  Download the zip from GitHub using:
`wget https://github.com/NarcissusDotDev/Realistic-Network-Simulator/raw/master/files/variant.zip`

2.  Extract:
`unzip -o variant.tar.gz`

3.  [Optional] Remove  the zip:
`rm variant.zip`

4.  Copy source code changes from BonnMotion:
`cp -a ~/bonnmotion-3.0.0/doc/OSRM/osrm-backend-4.8.1/descriptors/* ../../descriptors/`

5.  Make a build folder and build OSRM: [Note: This needs to be run with gcc 5.4.0]
`mkdir ../build; cd ../build; cmake ..; make`

6.  Copy files from BonnMotion:
`cp -a ~/bonnmotion-3.0.0/doc/OSRM/osrm-backend-4.8.1/build/* .`

10.  Edit start_routed.sh:
`sed -i '$ d' start_routed.sh; printf "trap 'kill -TERM \$PID' TERM\n./osrm-routed \$osrmfile -i 0.0.0.0 -p \$port -t \$threads\nPID=\$!\nwait \$PID" >> start_routed.sh`

### SUMO

1.  Set SUMO_HOME variable:
`echo 'export SUMO_HOME="/usr/share/sumo"' >> ~/.bashrc`
`source ~/.bashrc`

### [NS-3](https://www.nsnam.org/docs/release/3.28/tutorial/singlehtml/index.html#downloading-ns3)

1.	Return to home directory using:
`cd ~`

2.  Download ns-3 tarball:
`wget http://www.nsnam.org/release/ns-allinone-3.24.1.tar.bz2`

3.  Extract:
`tar xjf ns-allinone-3.24.1.tar.bz2`

4. [Optional] Delete the tar:
`rm ns-allinone-3.24.1.tar.bz2`

5.  Move to ns-3 modules directory:
`cd ns-allinone-3.24.1/ns-3.24.1/src`

6.  Download iolsr module:
`wget https://github.com/NarcissusDotDev/Realistic-Network-Simulator/raw/master/files/iolsr.tar.gz`

7.  Extract:
`tar xzf iolsr.tar.gz`

8.  [Optional] Delete the tar:
`rm iolsr.tar.gz

9.  Download obstacle module:
`wget https://github.com/NarcissusDotDev/Realistic-Network-Simulator/raw/master/files/obstacle.tar.gz`

10.  Extract:
`tar zxf obstacle.tar.gz`

11.  [Optional] Delete the tar:
`rm obstacle.tar.gz`

12.  Move to ns-3 home:
`cd ../`

13.  Set gcc version:
`sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.7 40 --slave /usr/bin/g++ g++ /usr/bin/g++-4.7`

14.  Build:
`./waf configure --build-profile=optimized --enable-examples --enable-tests`

#### [Optional] NetAnim

1. Enter NetAnim directory:
`cd ~/ns-allinone-3.24.1/netanim-3.106`

2. Build NetAnim:
`qmake NetAnim.pro; make`

## Run RNS:

1.  Download script files:
`wget https://github.com/NarcissusDotDev/Realistic-Network-Simulator/raw/master/files/magic.sh`
`wget https://github.com/NarcissusDotDev/Realistic-Network-Simulator/raw/master/files/config.shlib`
`wget https://github.com/NarcissusDotDev/Realistic-Network-Simulator/raw/master/files/config.cfg`

2.  Edit configuration file:
`nano config.cfg`

3.   Run:
`nohup ./magic.sh &`

## Running (What RNS does automagically):

1.  Go back to BonnMotion directory:
`cd ~/bonnmotion-3.0.0`

2.  Create a new folder for map files:
`mkdir maps; cd maps`

3.  Download a pbf file:
`wget http://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf`

4.  Download types file:
`wget https://github.com/NarcissusDotDev/Realistic-Network-Simulator/raw/master/files/buildings.typ.xml`

5.  Convert pbf to osm:
`osmconvert ../maps/berlin-latest.osm.pbf -o=berlin-latest.osm`

6.  Go to OSRM build directory:
`cd ~/osrm-backend-4.8.1/build`

7.  Prepare the map:
`./prepare_pbf.sh ../../bonnmotion-3.0.0/maps/berlin-latest`

8.  Run an OSRM server instance (in the background):
`sudo -b ./start_routed.sh ~/bonnmotion-3.0.0/maps/berlin-latest.osrm 5000 8`

9.  Create a new folder to run out of:
`mkdir ~/bonnmotion-3.0.0/out; cd ~/bonnmotion-3.0.0/out`

10.  Run BonnMotion:
`../bin/bm -f s1 RandomStreet -n 50 -B 13.387442 52.510168 13.393 52.515104 -u http://127.0.0.1:5000 -s 5 14 -C 1 -o ../maps/berlin-latest.osm.pbf`

11.  Generate network:
`netconvert --remove-edges.isolated --keep-edges.in-geo-boundary 13.387442,52.510168,13.393000,52.515104 --osm-files ../maps/berlin-latest.osm -o ../maps/berlin-latest.net.xml` 

12.  Generate buildings:
`polyconvert --prune.in-net --osm.keep-full-type --net-file ../maps/berlin-latest.net.xml --osm-files ../maps/berlin-latest.osm --type-file ../maps/buildings.typ.xml -o ../maps/berlin-latest.buildings.xml`

13.  Download the projection connection script:
`wget https://github.com/NarcissusDotDev/Realistic-Network-Simulator/raw/master/files/convert.py`

14.  Run the script:
`python3 convert.py s1.movements.geo.gz ../maps/berlin-latest.buildings.xml`

15.  Export to ns file:
`~/bonnmotion-3.0.0/bin/bm NSFile -f s1 -b`

16.  Download ns script:
`wget https://github.com/NarcissusDotDev/Realistic-Network-Simulator/raw/master/files/stable_network_mod_2.cc -P ~/ns-allinone-3.24.1/ns-3.24.1/scratch/`

17.  Move to build directory:
`cd ~/ns-allinone-3.24.1/ns-3.24.1`

18.  Run:
`./waf build`
