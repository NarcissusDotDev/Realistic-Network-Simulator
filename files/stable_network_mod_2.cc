#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/iolsr-module.h"
#include "ns3/mobility-module.h"
#include "ns3/wifi-module.h"
#include "ns3/dsdv-module.h"
#include "ns3/output-stream-wrapper.h"
#include "ns3/netanim-module.h"
#include "ns3/udp-client-server-helper.h"
#include<string>
using namespace ns3;

// New
#include "ns3/topology.h"
#include <fstream>
#include <iterator>

NS_LOG_COMPONENT_DEFINE ("StableNetworkRouteMod");

bool isPartOf6Cycle(Ipv4Address m_mainAddress, std::map<Ipv4Address, std::set<Ipv4Address> > graph){
	if (graph[m_mainAddress].size() != 2) {
		return false; // Must have exectly 2 neighbors for cycle
	}
	{
		// This code doesn't account for fictives...
		// Both cases can be united but for sake of simplicity they are seperate.
		// Case middle:
		bool ok = true;
		std::set<Ipv4Address> parts;
		std::set<Ipv4Address> level2;
		parts.insert(m_mainAddress);
		for (std::set<Ipv4Address>::const_iterator it = graph[m_mainAddress].begin(); it != graph[m_mainAddress].end(); ++it){
			const Ipv4Address& u = *it;
			if (graph[u].size() != 2) {
				ok = false;
				break;
			}
			parts.insert(u);
			for (std::set<Ipv4Address>::const_iterator it = graph[u].begin(); it != graph[u].end(); ++it){
				if (*it != m_mainAddress) level2.insert(*it);
			}
		}
		parts.insert(level2.begin(), level2.end());
		if (ok && (level2.size() == 2) && (parts.size() == 5)) {
			// Possible middle case
			std::set<Ipv4Address>::const_iterator it = level2.begin();
			std::set<Ipv4Address> &a = graph[*it];
			++it;
			std::set<Ipv4Address> &b = graph[*it];
			std::set<Ipv4Address> intersect;
			std::set_intersection(a.begin(), a.end(), b.begin(), b.end(), std::inserter(intersect, intersect.begin()));

			std::vector<Ipv4Address> intersectionWithoutPrev;
			std::set_difference(intersect.begin(), intersect.end(), parts.begin(), parts.end(), std::inserter(intersectionWithoutPrev, intersectionWithoutPrev.begin()));
			if (intersectionWithoutPrev.size() > 0) return true;
		}

		parts.clear();
		level2.clear();

		// Case side:
		ok = true;
		Ipv4Address neiWithMany = "0.0.0.0", neiWithTwo = "0.0.0.0", neiOfNei = "0.0.0.0";
		//Ipv4Address neiWithMany = uint32_t(0), neiWithTwo = uint32_t(0), neiOfNei = uint32_t(0);
		for (std::set<Ipv4Address>::const_iterator it = graph[m_mainAddress].begin(); it != graph[m_mainAddress].end(); ++it){
			const Ipv4Address& u = *it;
			if (graph[u].size() != 2) {
				if (!ok) break; // If the second one doesn't have rank 2
				ok = false;
				neiWithMany = u;
				continue;
			}
			neiWithTwo = u;
			std::set<Ipv4Address>::const_iterator itTmp = it;
			if (neiWithMany == "0.0.0.0") neiWithMany = *(++itTmp);
			parts.insert(m_mainAddress);
			parts.insert(neiWithMany);
			parts.insert(neiWithTwo);
			for (std::set<Ipv4Address>::const_iterator it2 = graph[u].begin(); it2 != graph[u].end(); ++it2){
				const Ipv4Address& v = *it2;
				if (v == m_mainAddress) continue;
				if (graph[v].size() != 2) return false;
				neiOfNei = v;
				parts.insert(v);
			}
			if (graph[neiWithTwo].count(neiWithMany) > 0) return false;
			if (graph[neiWithMany].count(neiOfNei) > 0) return false;

			std::set<Ipv4Address> ringCandidates;
			// Gather neighbors of neiWithMany
			for (std::set<Ipv4Address>::const_iterator it = graph[neiWithMany].begin(); it != graph[neiWithMany].end(); ++it){
				std::set<Ipv4Address> tmp;
				std::set_union(ringCandidates.begin(), ringCandidates.end(), graph[*it].begin(), graph[*it].end(), std::inserter(tmp, tmp.begin()));
				ringCandidates = tmp;
			}

			std::set<Ipv4Address> intersect;
			//std::set_intersection(graph[neiWithMany].begin(), graph[neiWithMany].end(), graph[neiOfNei].begin(), graph[neiOfNei].end(), std::inserter(intersect, intersect.begin()));
			std::set_intersection(ringCandidates.begin(), ringCandidates.end(), graph[neiOfNei].begin(), graph[neiOfNei].end(), std::inserter(intersect, intersect.begin()));
			if (intersect.size() > 0) return true;
			return false;
		}
	}
	return false;
}

size_t nodesIn6Ring (NodeContainer* cont){
	// Build directed graph from Hello
	std::map<Ipv4Address, std::set<Ipv4Address> > graph;
	std::set<Ipv4Address> n;
	for (size_t i=0;i<cont->GetN();++i){
		const std::pair<Ipv4Address, std::vector<Ipv4Address> > r = cont->Get(i)->GetObject<RoutingProtocol>()->GetSymNeighbors();
		for (std::vector<Ipv4Address>::const_iterator it = r.second.begin(); it != r.second.end(); ++it){
			graph[r.first].insert(*it);
		}
		n.insert(r.first);
	}

	size_t count=0;
	for (std::set<Ipv4Address>::const_iterator it = n.begin(); it != n.end(); ++it){
		if (isPartOf6Cycle(*it, graph)) ++count;
	}
	return count;
}
// Count and print the amount of nodes that have detected themselves to be in a 6ring
static void PrintCount6Ring(NodeContainer* cont){
	size_t count = 0;
	for (size_t i=0;i<cont->GetN();++i){
		Ptr<RoutingProtocol> pt = cont->Get(i)->GetObject<RoutingProtocol>();
		//NS_LOG_INFO("Node id: " << i << "\tTime: " << Simulator::Now().GetSeconds() << "\tRequireFake? " << pt->RequireFake());
		if (pt->isPartOf6Cycle()) ++count;
	}
	//NS_LOG_INFO("Total fakes required: " << count << " out of " << cont->GetN());
	std::cout << "In 6 ring: " << count << "/" << cont->GetN() << " Inside" << std::endl;
	std::cout << "In 6 ring: " << nodesIn6Ring(cont) << "/" << cont->GetN() << " Outside" << std::endl;
}

// Count the nodes that will require fake nodes
static void PrintCountFakeNodes(NodeContainer* cont){
	//ns3::iolsr::RoutingProtocol rp;
	unsigned int count = 0;
	for (unsigned int i=0;i<cont->GetN();++i){
		Ptr<RoutingProtocol> pt = cont->Get(i)->GetObject<RoutingProtocol>();
		//NS_LOG_INFO("Node id: " << i << "\tTime: " << Simulator::Now().GetSeconds() << "\tRequireFake? " << pt->RequireFake());
		if (pt->RequireFake()) ++count;
	}
	NS_LOG_INFO("Total fakes required: " << count << " out of " << cont->GetN());
	std::cout << "Fictive: " << count << "/" << cont->GetN() << std::endl;
}

static void PrintMprFraction(NodeContainer* cont){
	double sum = 0;
	for (unsigned int i=0;i<cont->GetN();++i){
		Ptr<RoutingProtocol> pt = cont->Get(i)->GetObject<RoutingProtocol>();
		//NS_LOG_INFO("Node id: " << i << "\tTime: " << Simulator::Now().GetSeconds() << "\tFraction: " << pt->FractionOfMpr());
		sum += pt->FractionOfMpr();
	}
	NS_LOG_INFO("Total fraction of MPR: " << sum / (double) cont->GetN());
	NS_LOG_INFO(sum / (double) cont->GetN());
	//... NS_LOG_INFO broke. Using cout...
	//std::cout << "Total fraction of MPR: " << sum / (double) cont->GetN() << std::endl;
	std::cout << "MPR: " << (sum / (double) cont->GetN()) << std::endl;
}

static void PrintRiskyFraction(NodeContainer* cont, Ipv4Address ignore = Ipv4Address("0.0.0.0")){
	double sum = 0;
	for (unsigned int i=0;i<cont->GetN();++i){
		Ptr<RoutingProtocol> pt = cont->Get(i)->GetObject<RoutingProtocol>();
		sum += pt->FractionOfNodesMarkedAsRisky(ignore);
	}
	std::cout << "Risky%: " << (sum / double(cont->GetN())) << std::endl;
}

static void PrintTcPowerLevel(NodeContainer* cont){
	double sumLsr = 0;
	double sumOlsr = 0;
	for (unsigned int i=0;i<cont->GetN();++i){
		Ptr<RoutingProtocol> pt = cont->Get(i)->GetObject<RoutingProtocol>();
		sumLsr += pt->tcPowerLevel(true);
		sumOlsr += pt->tcPowerLevel(false);
	}
	//NS_LOG_INFO("TC Level: " << sumOlsr / (double) cont->GetN() << " (lsr: " << sumLsr / (double) cont->GetN() << ")");
	std::cout << "TC Level: " << sumOlsr / (double) cont->GetN() << " \nlsr: " << sumLsr / (double) cont->GetN() << "\n";
}

static void ExecuteIsolationAttack(NodeContainer* cont){
	// Make it pick a node at random later...
	Ipv4Address target = cont->Get(2)->GetObject<RoutingProtocol>()->ExecuteIsolationAttack();
	target.IsBroadcast(); // Kill the unused warning
	//NS_LOG_INFO("Executing node isolation attack on: " << target);
	//NS_LOG_INFO("Attacker address: " << cont->Get(2)->GetObject<Ipv4>()->GetAddress(1,0));
	//NS_LOG_INFO("Victim  test: " << cont->Get(25)->GetObject<Ipv4>()->GetAddress(1,0));
	//std::cout << "Executing node isolation attack on: " << target << std::endl;
	//std::cout << "Attacker address: " << cont->Get(2)->GetObject<Ipv4>()->GetAddress(1,0) << std::endl;
}

static void ExecuteIsolationAttackMassive(NodeContainer* cont){
	// Let the first 30% nodes attack and see what happens
	for (uint32_t i=5;i<cont->GetN() * 0.3 + 5; ++i){
		// cont->Get(i)->GetObject<RoutingProtocol>()->ExecuteIsolationAttack();
		cont->Get(i)->GetObject<RoutingProtocol>()->ExecuteIsolationAttack(Ipv4Address("10.0.0.1"));
	}
}

static void ExecuteIsolationAttackBug(NodeContainer* nodes, Ipv4Address target){
	for (uint32_t i=2; i< nodes->GetN(); ++i){
		if (nodes->Get(i)->GetObject<RoutingProtocol>()->isItNeighbor(target)){
			nodes->Get(i)->GetObject<RoutingProtocol>()->ExecuteIsolationAttack(target);
			break;
		}
	}
}

static void PercentageWithFullConnectivity(NodeContainer* cont){
	uint32_t count = 0;
	for (uint32_t i=0;i<cont->GetN();++i){
		uint32_t routingTableSize = cont->Get(i)->GetObject<RoutingProtocol>()->getRoutingTableSize();
		if (routingTableSize == cont->GetN() - 1) {
			++count;
		}
	}
	double result = count / (double) cont->GetN();
	std::cout << "Routing Precentage: " << result << "\n";
	Simulator::Schedule(Seconds (10), &PercentageWithFullConnectivity, cont);
}

static void ActivateFictiveDefence(NodeContainer* cont){
	for (unsigned int i=0; i < cont->GetN(); ++i){
		cont->Get(i)->GetObject<RoutingProtocol>()->activateFictiveDefence();
	}
}

static void PrintReceivedPackets(Ptr<UdpServer> udpServer){
	uint32_t count = udpServer->GetReceived();
	std::cout << "Received Udp Packets: " << count << std::endl;
}

static void AssertConnectivity(NodeContainer* cont){
	//for (unsigned int i=0; i < cont->GetN(); ++i){
	//	if (cont->Get(i)->GetObject<RoutingProtocol>()->getRoutingTableSize() != cont->GetN() - 1) {
	//		Simulator::Stop();
	//	}
	//}
	if (cont->Get(0)->GetObject<RoutingProtocol>()->getRoutingTableSize() != cont->GetN() - 1) {
                std::cout << "AbortOnNoRouting\n";
		Simulator::Stop();
	}
}
static void AbortOnNeighbor (Ptr<Node> node, Ipv4Address address){
	if (node->GetObject<RoutingProtocol>()->isItUpToTwoHop(address)){
		// New
		std::cout << "AbortOnNeighbor\n";
		Simulator::Stop();
	}
}

/*static void AbortOnNoRouting (Ptr<Node> node, Ipv4Address address){

        if (node->GetObject<RoutingProtocol>()->cantRouteTo(address)){

                std::cout << "AbortOnNoRouting\n";

                Simulator::Stop();

        }

}*/

static void TrackTarget (Ptr<Node> target, Ptr<Node> tracker){
		Vector vec = target->GetObject<MobilityModel>()->GetPosition();
		vec.x += 8;
		vec.y += 0;
		tracker->GetObject<MobilityModel>()->SetPosition(vec);
}

static void PrintTables(Ptr<Node> n, std::string fname){
	std::ofstream o;
	o.open((std::string("_TwoHop") + fname + std::string(".txt")).c_str());
	const TwoHopNeighborSet &two = n->GetObject<RoutingProtocol>()->getTwoHopNeighborSet();
	for (TwoHopNeighborSet::const_iterator it = two.begin(); it!=two.end(); ++it){
		o << *it << "\n";
	}
	o.close();
	o.open((std::string("_Topology") + fname + std::string(".txt")).c_str());
	const TopologySet &tp = n->GetObject<RoutingProtocol>()->getTopologySet();
	for (TopologySet::const_iterator it = tp.begin(); it!=tp.end(); ++it){
		o << *it << "\n";
	}
	o.close();
	o.open((std::string("_Neighbor") + fname + std::string(".txt")).c_str());
	const NeighborSet &nei = n->GetObject<RoutingProtocol>()->getNeighborSet();
	for (NeighborSet::const_iterator it = nei.begin(); it!=nei.end(); ++it){
		o << *it << "\n";
	}
	o.close();
}

static void IneffectiveNeighorWrite(NodeContainer *cont){
	std::ofstream o;
	o.open ("_mpr.txt");
	for (unsigned int i=0; i< cont->GetN(); ++i){
		const MprSet mpr = cont->Get(i)->GetObject<RoutingProtocol>()->getMprSet();
		o << cont->Get(i)->GetObject<Ipv4>()->GetAddress(1,0).GetLocal() << ":";
		for (MprSet::const_iterator it = mpr.begin(); it != mpr.end(); ++it){
			o << *it << ",";
		}
		o << "\n";
	}
	o.close();
	o.open ("_neighbors.txt");
	for (unsigned int i=0; i< cont->GetN(); ++i){
		const NeighborSet neighbor = cont->Get(i)->GetObject<RoutingProtocol>()->getNeighborSet();
		o << cont->Get(i)->GetObject<Ipv4>()->GetAddress(1,0).GetLocal() << ":";
		for (NeighborSet::const_iterator it = neighbor.begin(); it != neighbor.end(); ++it){
			o << it->neighborMainAddr << ",";
		}
		o << "\n";
	}
	o.close();
}
/*
static void PrintTopologySet(NodeContainer* cont)
{
	ns3::iolsr::RoutingProtocol rp;
	for (unsigned int i=0;i<cont->GetN();i++)
	{
		Ptr<RoutingProtocol> pt = cont->Get(i)->GetObject<RoutingProtocol>();
		NS_LOG_INFO("Node id: "<<i<<"   "<<"Time: "<<Simulator::Now().GetSeconds());
		pt->PrintTopologySet();
	} 
}
*/




int main (int argc, char *argv[]){
	// Time
	Time::SetResolution (Time::NS);

	// Variables
	uint32_t nNodes = 100;
	double dMaxGridX = 500.0;
	uint32_t nMaxGridX = 500;
	double dMaxGridY = 500.0;
	uint32_t nMaxGridY = 500;
	bool bMobility = false;
	uint32_t nProtocol = 0;
	double dSimulationSeconds = 301.0;
	uint32_t nSimulationSeconds = 301;
	std::string mProtocolName = "Invalid";
	bool bSuperTransmission = false;
	bool bPrintAll = false;
	bool bPrintFakeCount = false;
	bool bPrint6RingCount = false;
	bool bPrintMprFraction = false;
	bool bPrintRiskyFraction = false;
	bool bIsolationAttack = false;
	bool bIsolationAttackBug = false;
	bool bIsolationAttackNeighbor = false;
	bool bEnableFictive = false;
	bool bHighRange = false;
	bool bPrintTcPowerLevel = false;
	bool bNeighborDump = false;
	bool bIsolationAttackMassive = false;
	bool bConnectivityPrecentage = false;
	bool bUdpServer = false;
	bool bBuildings = false;

	// Added variables
	std::string paramsFile = "PATH/???.ns_params";
	std::string bldgFile = "PATH/???.buildings.xml";
	std::string traceFile = "PATH/???.ns_movements";
	
	// Parameters from command line
	CommandLine cmd;
	//cmd.AddValue("nNodes", "Number of nodes in the simulation", nNodes);
	//cmd.AddValue("nMaxGridX", "X of the simulation rectangle", nMaxGridX);
	//cmd.AddValue("nMaxGridY", "Y of the simulation rectangle", nMaxGridY);
	//cmd.AddValue("nSimulationSeconds", "Amount of seconds to run the simulation", nSimulationSeconds);
	// New parameter
	cmd.AddValue("paramsFile", "Ns2 movement params file", paramsFile);
	cmd.AddValue("bldgFile", "SUMO buildings file", bldgFile);
	cmd.AddValue("traceFile", "Ns2 movement trace file", traceFile);
	
	cmd.AddValue("bMobility", "Delcares whenever there is movement in the network", bMobility);
	cmd.AddValue("nProtocol", "IOLSR=0, DSDV=1", nProtocol);
	cmd.AddValue("bSuperTransmission", "Transmission boost to node X?", bSuperTransmission);
	cmd.AddValue("bPrintAll", "Print routing table for all hops", bPrintAll);
	cmd.AddValue("bPrintFakeCount", "Print amount of fake nodes required", bPrintFakeCount);
	cmd.AddValue("bPrint6RingCount", "Print amount of nodes in 6 Ring", bPrint6RingCount);
	cmd.AddValue("bPrintMprFraction", "Print fraction of MPR", bPrintMprFraction);
	cmd.AddValue("bPrintRiskyFraction", "Print fraction of risky", bPrintRiskyFraction);
	cmd.AddValue("bPrintTcPowerLevel", "Print average TC size", bPrintTcPowerLevel);
	cmd.AddValue("bIsolationAttack", "Execute isolation attack by a node", bIsolationAttack);
	cmd.AddValue("bIsolationAttackNeighbor", "Execute isolation attack by a random neighbor", bIsolationAttackNeighbor);
	cmd.AddValue("bIsolationAttackMassive", "Execute isolation attack by many nodes", bIsolationAttackMassive);
	cmd.AddValue("bEnableFictive", "Activate fictive defence mode", bEnableFictive);
	cmd.AddValue("bHighRange", "Higher wifi range", bHighRange);
	cmd.AddValue("bNeighborDump", "Neighbor dump", bNeighborDump);
	cmd.AddValue("bConnectivityPrecentage", "Print connectivity precetage every X seconds", bConnectivityPrecentage);
	cmd.AddValue("bIsolationAttackBug", "Have an attacker stick to it's target", bIsolationAttackBug);
	cmd.AddValue("bUdpServer", "Try to send Udp packets from random nodes to the attacked node", bUdpServer);
	cmd.AddValue("bBuildings", "Load building to simulation", bBuildings);
	cmd.Parse (argc, argv);
	
	// New way of reading parameters
	std::ifstream params;
	std::string dummy;
	params.open (paramsFile.c_str());
	if (params.is_open()) {
		params >> dummy >> dummy >> nMaxGridX >> dummy;
		params >> dummy >> dummy >> nMaxGridY >> dummy;
		params >> dummy >> dummy >> nNodes;
		params >> dummy >> dummy >> nSimulationSeconds;
		params.close();
		
		// Round up the floating point
		nMaxGridX++;
		nMaxGridY++;
		
		//nMaxGridY+=8;
	} else {
		return 1;
	}

	if (nSimulationSeconds > 10.0) dSimulationSeconds = nSimulationSeconds; // Force minimum time
	if (nMaxGridX > 10.0) dMaxGridX = nMaxGridX; // Force minimum size. Revert to default.
	if (nMaxGridY > 10.0) dMaxGridY = nMaxGridY; // Force minimum size. Revert to default.
	
	// Build network
	NodeContainer nodes;
	nodes.Create (nNodes);
	
	// Add wifi
	WifiHelper wifi;
	//wifi.SetStandard(WIFI_PHY_STANDARD_80211g);
	YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
	YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default ();
	NqosWifiMacHelper wifiMac = NqosWifiMacHelper::Default ();
	if (bHighRange){
		//wifiPhy.Set("TxGain", DoubleValue(15));
		wifiPhy.Set("TxGain", DoubleValue(12.4));
		wifiChannel.AddPropagationLoss ("ns3::RangePropagationLossModel", "MaxRange", DoubleValue (250));
	} else {
		wifiChannel.AddPropagationLoss ("ns3::RangePropagationLossModel", "MaxRange", DoubleValue (100));
	}

	// Load buildings topology
	if (bBuildings) {
                Topology::LoadBuildings(bldgFile);
                wifiChannel.AddPropagationLoss ("ns3::ObstacleShadowingPropagationLossModel");
        }

	wifiPhy.SetChannel(wifiChannel.Create());
	wifi.SetRemoteStationManager ("ns3::ConstantRateWifiManager");
	wifiMac.SetType ("ns3::AdhocWifiMac");
	//wifiChannel.AddPropagationLoss ("ns3::RangePropagationLossModel", "MaxRange", DoubleValue (105));
	NetDeviceContainer adhocDevices = wifi.Install (wifiPhy, wifiMac, nodes);

	// Rig Node for huge wifi boost
	if (bSuperTransmission){
		NodeContainer superNodes;
		superNodes.Create (1);
		wifiPhy.Set("RxGain", DoubleValue(500.0));
		wifiPhy.Set("TxGain", DoubleValue(500.0));
		NetDeviceContainer superDevices = wifi.Install (wifiPhy, wifiMac, superNodes);
		adhocDevices.Add(superDevices);
		nodes.Add(superNodes);
	}

	// Install IOLSR / DSDV
	IOlsrHelper iolsr;
	DsdvHelper dsdv;
	Ipv4ListRoutingHelper routeList;
	InternetStackHelper internet;
	std::stringstream tmpStringStream;
	std::string fName = "Stable_Network_Stream";
	fName += "_n";
	tmpStringStream << nNodes;
	fName += tmpStringStream.str();
	tmpStringStream.str("");
	fName += "_x";
	tmpStringStream << nMaxGridX;
	fName += tmpStringStream.str();
	tmpStringStream.str("");
	fName += "_y";
	tmpStringStream << nMaxGridY;
	fName += tmpStringStream.str();
	tmpStringStream.str("");
	fName += "_r";
	tmpStringStream << RngSeedManager::GetRun();
	fName += tmpStringStream.str();
	tmpStringStream.str("");
	fName += ".txt";
	//Ptr<OutputStreamWrapper> stream = Create<OutputStreamWrapper>("Stable_Network_Stream_Run",std::ios::out);	
	//Ptr<OutputStreamWrapper> stream = Create<OutputStreamWrapper>(fName,std::ios::out);	

	switch (nProtocol){
		case 0:
			routeList.Add (iolsr, 100);
			if (!bPrintAll){
				//iolsr.PrintRoutingTableEvery(Seconds(10.0), nodes.Get(1), stream);
			} else {
				Ptr<OutputStreamWrapper> stream = Create<OutputStreamWrapper>(fName,std::ios::out);	
				iolsr.PrintRoutingTableAllEvery(Seconds(10.0), stream);
			}
			break;
		case 1:
			routeList.Add (dsdv, 100);
			if (!bPrintAll) {
				//dsdv.PrintRoutingTableEvery(Seconds(10.0), nodes.Get(1), stream);
			} else {
				Ptr<OutputStreamWrapper> stream = Create<OutputStreamWrapper>(fName,std::ios::out);	
				dsdv.PrintRoutingTableAllEvery(Seconds(10.0), stream);
			}
			break;
		default:
			NS_FATAL_ERROR ("Invalid routing protocol chosen " << nProtocol);
			break;
	}
	internet.SetRoutingHelper(routeList);
	internet.Install (nodes);

	// Install IP
	Ipv4AddressHelper addresses;
	addresses.SetBase ("10.0.0.0", "255.0.0.0");
	Ipv4InterfaceContainer interfaces;
	interfaces = addresses.Assign (adhocDevices);
	
	// Install mobility
	MobilityHelper mobility;
	Ptr<UniformRandomVariable> randomGridX = CreateObject<UniformRandomVariable> ();
	Ptr<UniformRandomVariable> randomGridY = CreateObject<UniformRandomVariable> ();
	randomGridX->SetAttribute ("Min", DoubleValue (0));
	randomGridX->SetAttribute ("Max", DoubleValue (dMaxGridX));
	randomGridY->SetAttribute ("Min", DoubleValue (0));
	randomGridY->SetAttribute ("Max", DoubleValue (dMaxGridY));

	Ptr<RandomRectanglePositionAllocator> taPositionAlloc = CreateObject<RandomRectanglePositionAllocator> ();
	taPositionAlloc->SetX(randomGridX);
	taPositionAlloc->SetY(randomGridY);
	mobility.SetPositionAllocator (taPositionAlloc);

	if (bMobility) {
		/*mobility.SetMobilityModel ("ns3::RandomWalk2dMobilityModel",
				"Bounds", RectangleValue (Rectangle (0, dMaxGridX, 0, dMaxGridY)),
				//"Speed", StringValue("ns3::UniformRandomVariable[Min=0|Max=2.0]"),
				"Speed", StringValue("ns3::UniformRandomVariable[Min=1.5|Max=2.0]"),
				//"Speed", StringValue("ns3::UniformRandomVariable[Min=9.5|Max=10.0]"),
				"Time", TimeValue(Seconds(3.0)),
				"Mode", EnumValue(RandomWalk2dMobilityModel::MODE_TIME));*/
		
		// Install Mobility Model from bonnmotion tool
		Ns2MobilityHelper ns2 = Ns2MobilityHelper(traceFile);
		ns2.Install(nodes.Begin(), nodes.End());
	} else {
		mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
		mobility.Install (nodes);
	}

	if (bUdpServer){
		UdpServerHelper udpServerHelper(80);
		ApplicationContainer apps = udpServerHelper.Install(nodes.Get(0));
		Ptr<UdpServer> udpServer = udpServerHelper.GetServer();
		UdpClientHelper udpClientHelper(Ipv4Address("10.0.0.1"), 80);
		udpClientHelper.SetAttribute("Interval", TimeValue(Seconds(7)));
		udpClientHelper.SetAttribute("MaxPackets", UintegerValue(18));

		
		// Choose random node to become sender
		//Ptr<UniformRandomVariable> rnd = CreateObject<UniformRandomVariable> ();
		//rnd->SetAttribute ("Min", DoubleValue (3));
		//rnd->SetAttribute ("Max", DoubleValue (nodes.GetN()-1));
		

		// Install UdpClient on said node
		//uint32_t sendingNode = rnd->GetInteger();
		uint32_t sendingNode = 1;
		apps.Add(udpClientHelper.Install(nodes.Get(sendingNode)));
		//apps.Add(udpClientHelper.Install(nodes.Get(1)));
		apps.Start(Seconds(60));
		apps.Stop(Seconds(1024));
		for (size_t i=30; i<nSimulationSeconds-5; i=i+1){
			Simulator::Schedule(Seconds (i), &AbortOnNeighbor, nodes.Get(sendingNode), Ipv4Address("10.0.0.1"));
			//Simulator::Schedule(Seconds (i), &AbortOnNoRouting, nodes.Get(sendingNode), Ipv4Address("10.0.0.1"));
			Simulator::Schedule(Seconds (i), &AssertConnectivity, &nodes);
		}
		Simulator::Schedule(Seconds (250), &PrintReceivedPackets, udpServer);
	}

	if (bPrintFakeCount) {
		//Ptr<OutputStreamWrapper> wrap = Create<OutputStreamWrapper>("StableNetwork-Mod-FakeNodes.txt", ios::out);
		Simulator::Schedule(Seconds (120), &PrintCountFakeNodes, &nodes);
		Simulator::Schedule(Seconds (240), &PrintCountFakeNodes, &nodes);
	}
	if (bPrintMprFraction) {
		Simulator::Schedule(Seconds (120), &PrintMprFraction, &nodes);
		Simulator::Schedule(Seconds (240), &PrintMprFraction, &nodes);
	}
	if (bPrintRiskyFraction) {
		Ipv4Address ignore = Ipv4Address("0.0.0.0");
		if (bIsolationAttackBug) ignore = Ipv4Address("10.0.0.3");
		Simulator::Schedule(Seconds (60), &PrintRiskyFraction, &nodes, ignore);
		Simulator::Schedule(Seconds (240), &PrintRiskyFraction, &nodes, ignore);
	}
	if (bPrintTcPowerLevel) {
		Simulator::Schedule(Seconds (120), &PrintTcPowerLevel, &nodes);
		Simulator::Schedule(Seconds (240), &PrintTcPowerLevel, &nodes);
	}
	if (bIsolationAttack){
		Simulator::Schedule(Seconds (8), &ExecuteIsolationAttack, &nodes);
	}
	if (bIsolationAttackMassive){
		Simulator::Schedule(Seconds (8), &ExecuteIsolationAttackMassive, &nodes);
	}
	if (bIsolationAttackBug){
		
		nodes.Get(2)->GetObject<RoutingProtocol>()->ExecuteIsolationAttack(Ipv4Address("10.0.0.1"));
		Vector vec = nodes.Get(0)->GetObject<MobilityModel>()->GetPosition();
		vec.x += 8;
		vec.y += 0;
		nodes.Get(2)->GetObject<MobilityModel>()->SetPosition(vec);
		//DynamicCast<YansWifiPhy>(DynamicCast<WifiNetDevice>(nodes.Get(2)->GetDevice(0))->GetPhy())->SetTxGain(1.2);

		for (size_t i=1; i<nSimulationSeconds; ++i){
			Simulator::Schedule(Seconds (i), &TrackTarget, nodes.Get(0), nodes.Get(2));
		}
	}
	if (bIsolationAttackNeighbor){
			Simulator::Schedule(Seconds (8), &ExecuteIsolationAttackBug, &nodes, Ipv4Address("10.0.0.1"));
	}
	if (bEnableFictive){
		Simulator::Schedule(Seconds (0), &ActivateFictiveDefence, &nodes);
		//Simulator::Schedule(Seconds (121), &ActivateFictiveDefence, &nodes);
	}
	if (bNeighborDump){
		Simulator::Schedule(Seconds (120), &IneffectiveNeighorWrite, &nodes);
	}
	bool bAssertConnectivity = false;
	if (bAssertConnectivity){
		// Assert connectivity
		Simulator::Schedule(Seconds (119), &AssertConnectivity, &nodes);
	}
	if (bConnectivityPrecentage){
		Simulator::Schedule(Seconds (10), &PercentageWithFullConnectivity, &nodes);
	}

	if (bPrint6RingCount) {
		//Ptr<OutputStreamWrapper> wrap = Create<OutputStreamWrapper>("StableNetwork-Mod-FakeNodes.txt", ios::out);
		Simulator::Schedule(Seconds (120), &PrintCount6Ring, &nodes);
		Simulator::Schedule(Seconds (240), &PrintCount6Ring, &nodes);
	}

	if (false){
		Simulator::Schedule(Seconds (251), &PrintTables, nodes.Get(0), std::string("V"));
		Simulator::Schedule(Seconds (251), &PrintTables, nodes.Get(2), std::string("A"));
		Simulator::Schedule(Seconds (251), &IneffectiveNeighorWrite, &nodes);
	}

	// Print Topology Set
	//Simulator::Schedule(Seconds (35) , &PrintTopologySet, &nodes);
	
	/*AnimationInterface anim ("/home/user/ns-allinone-3.24.1/ns-3.24.1/run-only_first_2/Stable_Network_animation.xml");

	anim.SetMobilityPollInterval (Seconds (1));

	for(uint32_t i=0; i<nNodes;i++)

		anim.UpdateNodeSize (i, 10, 10);

		

	anim.UpdateNodeColor(nodes.Get(0), 0, 255, 255);

	anim.UpdateNodeColor(nodes.Get(1), 0, 255, 0);

	anim.UpdateNodeColor(nodes.Get(2), 0, 0, 255);*/
	
	// Animation
	/*AnimationInterface anim ("Stable_Network_animation.xml");
	anim.SetMobilityPollInterval (Seconds (1));
	for(uint32_t i=0; i<nNodes;i++)
		anim.UpdateNodeSize (i, 10, 10);*/

	//AnimationInterface anim("Stable_Network_animation.xml");
	//anim.UpdateNodeColor(nodes.Get(0), 255, 0, 0);
	//anim.UpdateNodeColor(nodes.Get(1), 0, 255, 0);
	//anim.UpdateNodeColor(nodes.Get(2), 0, 0, 255);
	//anim.SetMobilityPollInterval(Seconds(1));

	// Pcap
	//wifiPhy.EnablePcapAll ("Stable_Network_");
	
	// Run simulation
	NS_LOG_INFO ("Run simulation.");
	Simulator::Stop (Seconds (dSimulationSeconds));

	Simulator::Run ();
	Simulator::Destroy ();

	return 0;
}
