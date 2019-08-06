#!/usr/bin/env python3
from collections import defaultdict, deque
from operator import itemgetter
import sys
import re
import random
import statistics
import csv


class Infection:
    """
    This is the base class for parsing a couple of files to find if a prediction of bottleneck came true
    With or without an infection
    """
    # Regex
    re_bet = re.compile(r'(?:[A-Za-z]+ ){3}(?P<run>\d+)|(?:[\d]+.){3}(?P<node>\d+)[ -]+(?P<paths>\d+)|(?P<noprediction>[a-zA-Z]+ [a-zA-Z]+)\n|[a-zA-Z]+ [a-zA-Z]+ - (?:\d+.){3}(?P<real>\d+)')
    re_packet = re.compile(r'(?:[A-Za-z]+ ){3}(?P<run>\d+)|DA:(?:[\da-fA-F]+.){5}(?P<node>[a-fA-F\d]+)')
    # re_mpr = re.compile(r'(?:[A-Za-z]+ ){3}(?P<run>\d+)|(?:\+)(?P<time>\d+\.\d+)ns|Node: (?P<node>[a-fA-F\d]+)|(?:[\d]+.){3}(?P<via>[\d]+)')
    # re_neighbors = re.compile(r'(?:[A-Za-z]+ ){3}(?P<run>\d+)|(?:\+)(?P<time>\d+\.\d+)ns|Node: (?P<node>[a-fA-F\d]+)|(?:[\d]+.){3}(?P<via>[\d]+)(?:[\s,a-z]+)=SYM')
    re_mpr = re.compile(r'(?:[\d]+.){3}(?P<via>[\d]+)|Node: (?P<node>[a-fA-F\d]+)|(?:[A-Za-z]+ ){3}(?P<run>\d+)|(?:\+)(?P<time>\d+\.\d+)ns')
    re_neighbors = re.compile(r'(?:[\d]+.){3}(?P<via>[\d]+)(?:[\s,a-z]+)=SYM|Node: (?P<node>[a-fA-F\d]+)|(?:[A-Za-z]+ ){3}(?P<run>\d+)|(?:\+)(?P<time>\d+\.\d+)ns')
    # re_tcs = re.compile(r'(?:[\d]+.){3}(?P<dest>[\d]+)(?:[,a-zA-Z ]+)=(?:[\d]+.){3}(?P<last>[\d]+)(?:[,\w= ]+)\+(?P<exp>\d+\.\d+)ns|Node: (?P<node>[a-fA-F\d]+)|(?:[A-Za-z]+ ){3}(?P<run>\d+)|(?:\+)(?P<time>\d+\.\d+)ns')
    re_tcs = re.compile(r'(?:[\d]+.){3}(?P<dest>[\d]+)(?:[,a-zA-Z ]+)=(?:[\d]+.){3}(?P<last>[\d]+)(?:[,\w= ]+)\+(?P<exp>\d+)\.(?:\d+)ns|Node: (?P<node>[a-fA-F\d]+)|(?:[A-Za-z]+ ){3}(?P<run>\d+)|(?:\+)(?P<time>\d+)\.(?:\d+)ns')

    def __init__(self, prefix='BottleNeckNeighbors_n100_1000x750_FixPos-1-Mobility-false-'):
        """
        Initialize the object. Expecting filenames starting with prefix ending with the required types
        :param prefix: Prefix of filenames
        :return:The object?
        """
        # File names
        self.csv = prefix + ".csv"
        self.bets_filename = prefix + "betlist.txt"
        self.packets_filename = prefix + "packets.txt"
        self.mpr_filename = prefix + "mpr.txt"
        self.neighbors_filename = prefix + "neighbors.txt"
        self.tcs_filename = prefix + "tcs.txt"

        # Variables per run
        self.run_number = None
        self.next_run_number = None
        self.next_run_number_bet = None
        self.next_run_number_mpr = None
        self.next_run_number_packet = None
        self.next_run_number_neighbors = None
        self.next_run_number_tcs = None
        self.nodes = set()
        self.real_nodes = set()
        self.nodes_random = set()
        self.mpr = {}
        self.mprs = defaultdict(set)
        self.neighbors = {}
        self.tcs = {}
        self.max_paths = 0
        self.no_prediction_bool = False

        # Variables for statistics
        self.total = 0
        self.prediction = 0
        self.prediction_count_one = 0
        self.prediction_count_one_success = 0
        self.prediction_no_bottleneck = 0
        self.low_path_count = 0 # Cases with paths of 1/2
        self.real_bottleneck = 0
        self.real_bottleneck_found = 0
        self.no_prediction = 0
        self.success = 0
        self.no_real_bottleneck_found = 0  # Cases where the guess of no bottleneck was correct
        self.no_real_bottleneck = 0  # Cases where there was no bottleneck
        self.lucky_bets = 0  # No bottleneck, but bet was still correct
        self.unlucky_bets = 0  # No bottleneck, bet was incorrect
        self.avg_bet_amount = 0  # Excluding 1's
        self.avg_bet_amount_count = 0  # For calculating average
        self.rand_bet_success = 0  # Choose 1 hop at random
        self.rand_bet = 0  # Choose 1 hop at random
        self.infection_all_mprs = 0  # Infect hops that were marked as bet and those who chose them as MPR
        self.infection_all_neighbors = 0  # Infect hops that were marked as bet and those who chose them as MPR
        self.infection_random_mprs = 0  # Infect random hos that was marked as bet and those who chose it as MPR
        self.infection_random_neighbors = 0  # Infect random hos that was marked as bet and all its neighbors
        self.infection_all_mprs_count = 0
        self.infection_all_neighbors_count = 0
        self.infection_random_mprs_count = 0
        self.infection_random_neighbors_count = 0

        self.infection_true_random_mprs = 0
        self.infection_true_random_neighbors = 0
        self.infection_true_random_mprs_count = 0
        self.infection_true_random_neighbors_count = 0

        # When we thought there was bottleneck and there wasn't
        self.infection_all_mprs_no_bottleneck = 0  # Infect hops that were marked as bet and those who chose them as MPR
        self.infection_all_neighbors_no_bottleneck = 0  # Infect hops that were marked as bet and those who chose them as MPR
        self.infection_random_mprs_no_bottleneck = 0  # Infect random hos that was marked as bet and those who chose it as MPR
        self.infection_random_neighbors_no_bottleneck = 0  # Infect random hos that was marked as bet and all its neighbors
        self.infection_all_mprs_count_no_bottleneck = 0
        self.infection_all_neighbors_count_no_bottleneck = 0
        self.infection_random_mprs_count_no_bottleneck = 0
        self.infection_random_neighbors_count_no_bottleneck = 0

        # New test case. How well does Tirza1 work as compared to random choice.
        # Currently, random does use Tirza1 for calculation of path, and drops the number as there is no algorithm
        # to calculate the path that would be effective and result in all paths for it.
        self.tirza_random_total_random = 0
        self.tirza_random_total_tirza = 0
        self.tirza_random_single_random = 0
        self.tirza_random_single_tirza = 0
        self.tirza_random_mpr_random = 0
        self.tirza_random_mpr_infected_random = 0
        self.tirza_random_mpr_tirza = 0
        self.tirza_random_mpr_infected_tirza = 0
        self.tirza_random_nei_random = 0
        self.tirza_random_nei_infected_random = 0
        self.tirza_random_nei_tirza = 0
        self.tirza_random_nei_infected_tirza = 0

        self.tirza_random_total_random_bfs = 0
        self.tirza_random_single_random_bfs = 0
        self.tirza_random_mpr_random_bfs = 0
        self.tirza_random_mpr_infected_random_bfs = 0
        self.tirza_random_nei_random_bfs = 0
        self.tirza_random_nei_infected_random_bfs = 0

        # Added an option to check fraction of MPR and Neighbors
        self.factors_to_test = range(0,101,10)
        self.factors_tirza_mpr = defaultdict(int)
        self.factors_tirza_mpr_infected = defaultdict(int)
        self.factors_tirza_nei = defaultdict(int)
        self.factors_tirza_nei_infected = defaultdict(int)

        self.factors_random_mpr = defaultdict(int)
        self.factors_random_mpr_infected = defaultdict(int)
        self.factors_random_nei = defaultdict(int)
        self.factors_random_nei_infected = defaultdict(int)

        self.factors_bfs_mpr = defaultdict(int)
        self.factors_bfs_mpr_infected = defaultdict(int)
        self.factors_bfs_nei = defaultdict(int)
        self.factors_bfs_nei_infected = defaultdict(int)

    def mprs_from_mpr(self):
        self.mprs = defaultdict(set)
        # For it is possible, that a node was not selected as an MPR, we have to initialize every node with empty set
        # for k in self.mpr.keys():
        #     self.mprs[k] = set()
        for k, v in self.mpr.items():
            for n in v:
                # s = self.mprs.get(n,set())
                # s.add(k)
                # self.mprs[n] = s
                self.mprs[n].add(k)

    def _read_chunk_from_bets(self, f):
        self.nodes = set()
        self.real_nodes = set()
        self.no_prediction_bool = False
        self.max_paths = 0
        while True:
            l = f.readline()
            if not l:
                # Nothing to read
                self.next_run_number_bet = "EOF"
                break
            m = self.re_bet.search(l)
            if m:
                if m.group('run') is not None:
                    run_number_found = int(m.group('run'))
                    if self.next_run_number_bet is None:
                        self.run_number = run_number_found
                        self.next_run_number_bet = -1
                        # if run_number_found == self.run_number:
                        #     self.next_run_number_bet = run_number_found
                        # else:
                        #     raise RuntimeError("Order of files not identical")
                    else:
                        self.next_run_number_bet = run_number_found
                        # if self.next_run_number_bet != self.next_run_number:
                        #     raise RuntimeError("Order of files is not identical")
                        break
                elif m.group('node'):
                    tmp_paths = int(m.group('paths'))
                    if tmp_paths > self.max_paths: self.max_paths = tmp_paths
                    if tmp_paths == self.max_paths and int(m.group('node')) not in {1, 2}:
                        self.nodes.add(int(m.group('node')))
                elif m.group('noprediction'):
                    self.no_prediction_bool = True
                elif m.group('real'):
                    self.real_nodes.add(int(m.group('real')))

    def _read_chunk_from_packets_who_passed_packet(self, f):
        self.nodes_send = set()
        # for packet in f:
        while True:
            packet = f.readline()
            if not packet:
                self.next_run_number_packet = "EOF"
                # Nothing to read
                break
            m = self.re_packet.search(packet)
            if m:
                if m.group('run') is not None:
                    run_number_found = int(m.group('run'))
                    if self.next_run_number_packet is None:
                        if run_number_found == self.run_number:
                            self.next_run_number_packet = run_number_found
                        else:
                            raise RuntimeError("Order of packets and bets is not identical")
                    else:
                        self.next_run_number_packet = run_number_found
                        if self.next_run_number_packet != self.next_run_number:
                            raise RuntimeError("Order of packets and bets is not identical")
                        break
                elif m.group('node') is not None:
                    self.nodes_send.add(int(m.group('node'), 16))

    def _read_chunk_from_mpr(self, f):
        self.mpr = {}
        curr_node = -1
        while True:
            l = f.readline()
            m = self.re_mpr.search(l)
            if m:
                if m.group('via') is not None:
                    self.mpr[curr_node].add(int(m.group('via')))

                elif m.group('node') is not None:
                    curr_node = int(m.group('node'))+1
                    self.mpr[curr_node] = set()

                elif m.group('run') is not None:
                    run_number_found = int(m.group('run'))
                    if self.next_run_number_mpr is None:
                        if run_number_found == self.run_number:
                            self.next_run_number_mpr = run_number_found
                        else:
                            raise RuntimeError("Order of files is not identical")
                    else:
                        self.next_run_number_mpr = run_number_found
                        if self.next_run_number_mpr != self.next_run_number:
                            raise RuntimeError("Order of files is not identical")
                        break

            elif not l:
                self.next_run_number_mpr = "EOF"
                break

    def _read_chunk_from_neighbors(self, f):
        self.neighbors = {}
        curr_node = -1
        while True:
            l = f.readline()

            m = self.re_neighbors.search(l)
            if m:
                if m.group('via') is not None:
                    self.neighbors[curr_node].add(int(m.group('via')))
                elif m.group('node') is not None:
                    curr_node = int(m.group('node'))+1
                    self.neighbors[curr_node] = set()
                elif m.group('run') is not None:
                    run_number_found = int(m.group('run'))
                    if self.next_run_number_neighbors is None:
                        if run_number_found == self.run_number:
                            self.next_run_number_neighbors = run_number_found
                        else:
                            raise RuntimeError("Order of files is not identical")
                    else:
                        self.next_run_number_neighbors = run_number_found
                        if self.next_run_number_neighbors != self.next_run_number:
                            raise RuntimeError("Order of files is not identical")
                        break

            elif not l:
                self.next_run_number_neighbors = "EOF"
                break

    def _read_chuck_from_tc(self, f):
        self.tcs = {}
        curr_node = -1
        time = 0
        tc_interval = 5000000000
        while True:
            l = f.readline()

            m = self.re_tcs.search(l)
            if m:
                if m.group('last') is not None:
                    # Only new TC
                    if int(m.group('exp')) > time + tc_interval*2:
                        self.tcs[curr_node].add((int(m.group('dest')), int(m.group('last'))))
                elif m.group('node') is not None:
                    curr_node = int(m.group('node'))+1
                    self.tcs[curr_node] = set()
                elif m.group('time'):
                    time = int(m.group('time'))
                elif m.group('run') is not None:
                    run_number_found = int(m.group('run'))
                    if self.next_run_number_tcs is None:
                        if run_number_found == self.run_number:
                            self.next_run_number_tcs = run_number_found
                        else:
                            raise RuntimeError("Order of files is not identical")
                    else:
                        self.next_run_number_tcs = run_number_found
                        if self.next_run_number_tcs != self.next_run_number:
                            raise RuntimeError("Order of files is not identical")
                        break
            elif not l:
                self.next_run_number_tcs = "EOF"
                break

    def run(self):
        with open(self.bets_filename, 'r') as bets, open(self.packets_filename, 'r') as packets, open(self.mpr_filename, 'r') as mpr_file,\
                open(self.neighbors_filename, 'r') as neighbors_file, open(self.tcs_filename) as tcs_file:
            while self.next_run_number != "EOF":
                print(self.next_run_number)
                self._read_chunk_from_bets(bets)
                self.next_run_number = self.next_run_number_bet
                self._read_chunk_from_packets_who_passed_packet(packets)
                self._read_chunk_from_mpr(mpr_file)
                self._read_chunk_from_neighbors(neighbors_file)
                self._read_chuck_from_tc(tcs_file)
                self.mprs_from_mpr()

                s = 2
                t = 1
                adjg = self._build_graph_from_tc(3)
                adjc, topsort = self._build_dag_from_graph(adjg, s, t)
                paths = self._count_paths_in_dag(adjc, topsort, s ,t)
                nodes_calculated, b = self._extract_bets_from_paths(paths, s, t)

                self.nodes = nodes_calculated
                self.no_prediction_bool = b

                self.nodes_random, _ = self._extract_random_from_paths(paths, s, t)
                self.nodes_random_bfs = self._extract_random_from_graph(adjg, s, t)

                self._calculate_success()
                x = self.run_number
                self.run_number = self.next_run_number

                # Todo: remove after testing
                # if nodes_calculated != self.nodes:
                #     print('run', x)
                #     print('nodes', self.nodes)
                #     print('calc', nodes_calculated)
                #     raise RuntimeError("Calculated nodes differ from simulation result")
            self.print_results()
            self.write_csv()

    @staticmethod
    def print_two_vars_rate(t, x, y):
        print(t+":\t", x, '/', y, '=', x/y)


    def write_csv(self):
        with open(self.csv, 'w', newline='') as csvfile:
            spamwriter = csv.writer(csvfile)
            spamwriter.writerow([self.csv] + [''] * 5)
            spamwriter.writerow([''] * 6)
            spamwriter.writerow(['Tirza'] + [''] * 5)
            spamwriter.writerow(['Percentage', 'MPR Success', 'MPR Overhead', 'Nei Overhead', 'Nei Success', ''])
            for i in self.factors_to_test:
                spamwriter.writerow([
                    i,
                    100 * self.factors_tirza_mpr[i] / self.tirza_random_total_tirza,
                    self.factors_tirza_mpr_infected[i] / self.tirza_random_total_tirza,
                    100 * self.factors_tirza_nei[i] / self.tirza_random_total_tirza,
                    self.factors_tirza_nei_infected[i] / self.tirza_random_total_tirza,
                    ''
                    ])
            spamwriter.writerow([''] * 6)

            spamwriter.writerow(['Random'] + [''] * 5)
            spamwriter.writerow(['Percentage', 'MPR Success', 'MPR Overhead', 'Nei Overhead', 'Nei Success', ''])
            for i in self.factors_to_test:
                spamwriter.writerow([
                    i,
                    100 * self.factors_random_mpr[i] / self.tirza_random_total_random,
                    self.factors_random_mpr_infected[i] / self.tirza_random_total_random,
                    100 * self.factors_random_nei[i] / self.tirza_random_total_random,
                    self.factors_random_nei_infected[i] / self.tirza_random_total_random,
                    ''
                    ])
            spamwriter.writerow([''] * 6)

            spamwriter.writerow(['RandomBFS'] + [''] * 5)
            spamwriter.writerow(['Percentage', 'MPR Success', 'MPR Overhead', 'Nei Overhead', 'Nei Success', ''])
            for i in self.factors_to_test:
                spamwriter.writerow([
                    i,
                    100 * self.factors_bfs_mpr[i] / self.tirza_random_total_random_bfs,
                    self.factors_bfs_mpr_infected[i] / self.tirza_random_total_random_bfs,
                    100 * self.factors_bfs_nei[i] / self.tirza_random_total_random_bfs,
                    self.factors_bfs_nei_infected[i] / self.tirza_random_total_random_bfs,
                    ''
                    ])
            spamwriter.writerow([''] * 6)

    def print_results(self):
        # Tirza VS Random
        print('Total:', self.total)
        print('Tirza:')
        self.print_two_vars_rate('Single', self.tirza_random_single_tirza, self.tirza_random_total_tirza)
        self.print_two_vars_rate('MPR', self.tirza_random_mpr_tirza, self.tirza_random_total_tirza)
        print('\tInfected:\t', self.tirza_random_mpr_infected_tirza / self.tirza_random_total_tirza)
        self.print_two_vars_rate('Neighbor', self.tirza_random_nei_tirza, self.tirza_random_total_tirza)
        print('\tInfected:\t', self.tirza_random_nei_infected_tirza / self.tirza_random_total_tirza)
        print('\nRandom:')
        self.print_two_vars_rate('Single', self.tirza_random_single_random, self.tirza_random_total_random)
        self.print_two_vars_rate('MPR', self.tirza_random_mpr_random, self.tirza_random_total_random)
        print('\tInfected:\t', self.tirza_random_mpr_infected_random / self.tirza_random_total_random)
        self.print_two_vars_rate('Neighbor', self.tirza_random_nei_random, self.tirza_random_total_random)
        print('\tInfected:\t', self.tirza_random_nei_infected_random / self.tirza_random_total_random)
        print('\nRandom BFS:')
        self.print_two_vars_rate('Single', self.tirza_random_single_random_bfs, self.tirza_random_total_random_bfs)
        self.print_two_vars_rate('MPR', self.tirza_random_mpr_random_bfs, self.tirza_random_total_random_bfs)
        print('\tInfected:\t', self.tirza_random_mpr_infected_random_bfs / self.tirza_random_total_random_bfs)
        self.print_two_vars_rate('Neighbor', self.tirza_random_nei_random_bfs, self.tirza_random_total_random_bfs)
        print('\tInfected:\t', self.tirza_random_nei_infected_random_bfs / self.tirza_random_total_random_bfs)


        # Print % of nodes
        for i in self.factors_to_test:
            print(i, "%", "Tirza")
            self.print_two_vars_rate('MPR', self.factors_tirza_mpr[i], self.tirza_random_total_tirza)
            print('\tInfected:\t', self.factors_tirza_mpr_infected[i] / self.tirza_random_total_tirza)
            self.print_two_vars_rate('Neighbor', self.factors_tirza_nei[i], self.tirza_random_total_tirza)
            print('\tInfected:\t', self.factors_tirza_nei_infected[i] / self.tirza_random_total_tirza)
            print(i, "%", "Random")
            self.print_two_vars_rate('MPR', self.factors_random_mpr[i], self.tirza_random_total_random)
            print('\tInfected:\t', self.factors_random_mpr_infected[i] / self.tirza_random_total_random)
            self.print_two_vars_rate('Neighbor', self.factors_random_nei[i], self.tirza_random_total_random)
            print('\tInfected:\t', self.factors_random_nei_infected[i] / self.tirza_random_total_random)
            print(i, "%", "Random BFS")
            self.print_two_vars_rate('MPR', self.factors_bfs_mpr[i], self.tirza_random_total_random_bfs)
            print('\tInfected:\t', self.factors_bfs_mpr_infected[i] / self.tirza_random_total_random_bfs)
            self.print_two_vars_rate('Neighbor', self.factors_bfs_nei[i], self.tirza_random_total_random_bfs)
            print('\tInfected:\t', self.factors_bfs_nei_infected[i] / self.tirza_random_total_random_bfs)

        pass
        # print('Total: ', self.total, '  Prediction: ', self.prediction, '  No prediction: ', self.no_prediction, '  No bottleneck ', self.prediction_no_bottleneck)
        # print('Success: ' + str(self.success))
        # print('Rate: ' + str(self.success / self.prediction))
        # # print('Single bet: ' + str(self.prediction_count_one_success) + '/' + str(self.prediction_count_one) + ' = ' + str(self.prediction_count_one_success/self.prediction_count_one))
        # # print('Paths 1/2: ' + str(self.low_path_count) + '/' + str(self.prediction) + ' = ' + str(self.low_path_count/self.prediction))
        # print('Found real: ' + str(self.real_bottleneck_found) + '/' + str(self.real_bottleneck) + ' = ' + str(self.real_bottleneck_found/self.real_bottleneck))
        # # print('Lucky bets (cases out of success): ' + str(self.lucky_bets) + '/' + str(self.success) + ' = ' + str(self.lucky_bets/self.success))
        # print('Lucky bets (cases out of nrbn): ' + str(self.lucky_bets) + '/' + str(self.no_real_bottleneck) + ' = ' + str(self.lucky_bets/self.no_real_bottleneck))
        # print('Unlucky bets (cases out of no real bottleneck): ' + str(self.unlucky_bets) + '/' + str(self.no_real_bottleneck) + ' = ' + str(self.unlucky_bets/self.no_real_bottleneck))
        # # print('Average amount of bets (excluding 1): ' + str(self.avg_bet_amount / self.avg_bet_amount_count))
        # # print('Random choice: ' + str(self.rand_bet_success) + '/' + str(self.avg_bet_amount_count) + ' = ' + str(self.rand_bet_success / self.avg_bet_amount_count))
        # print('No real bottleneck: ' + str(self.no_real_bottleneck_found) + '/' + str(self.no_real_bottleneck) + ' = ' + str(self.no_real_bottleneck_found / self.no_real_bottleneck))
        # self.print_two_vars_rate('Infection All MPR', self.infection_all_mprs, self.prediction)
        # print('\tInfected:\t', self.infection_all_mprs_count / self.prediction)
        # self.print_two_vars_rate('Infection All Nei', self.infection_all_neighbors, self.prediction)
        # print('\tInfected:\t', self.infection_all_neighbors_count / self.prediction)
        # self.print_two_vars_rate('Infection Rand MPR', self.infection_random_mprs, self.prediction)
        # print('\tInfected:\t', self.infection_random_mprs_count / self.prediction)
        # self.print_two_vars_rate('Infection Rand Nei', self.infection_random_neighbors, self.prediction)
        # print('\tInfected:\t', self.infection_random_neighbors_count / self.prediction)
        #
        # self.print_two_vars_rate('Infection True Rand MPR', self.infection_true_random_mprs, self.total)
        # print('\tInfected:\t', self.infection_true_random_mprs_count / self.total)
        # self.print_two_vars_rate('Infection True Rand Nei', self.infection_true_random_neighbors, self.total)
        # print('\tInfected:\t', self.infection_true_random_neighbors_count / self.total)
        #
        # print("Suspected bottleneck when there wasn't:");
        # t = self.no_real_bottleneck - self.no_real_bottleneck_found
        # self.print_two_vars_rate('Infection All MPR', self.infection_all_mprs_no_bottleneck, t)
        # print('\tInfected:\t', self.infection_all_mprs_count_no_bottleneck / t)
        # self.print_two_vars_rate('Infection All Nei', self.infection_all_neighbors_no_bottleneck, t)
        # print('\tInfected:\t', self.infection_all_neighbors_count_no_bottleneck / t)
        # self.print_two_vars_rate('Infection Rand MPR', self.infection_random_mprs_no_bottleneck, t)
        # print('\tInfected:\t', self.infection_random_mprs_count_no_bottleneck / t)
        # self.print_two_vars_rate('Infection Rand Nei', self.infection_random_neighbors_no_bottleneck, t)
        # print('\tInfected:\t', self.infection_random_neighbors_count_no_bottleneck / t)

    def _calculate_success(self):
        if 1 in self.nodes_send:
            self.total += 1
            if self.no_prediction_bool:
                self.no_prediction += 1
            else:
                if len(self.nodes) == 0:
                    self.prediction_no_bottleneck += 1
                else:
                    self.prediction += 1
                    if len(self.nodes & self.nodes_send) > 0:
                        self.success += 1
                        if len(self.real_nodes) == 0:
                            self.lucky_bets += 1
                    else:
                        if len(self.real_nodes) == 0:
                            self.unlucky_bets += 1

                    # Cases where there is only 1 bet
                    if len(self.nodes) == 1:
                        self.prediction_count_one += 1
                        if len(self.nodes & self.nodes_send) > 0:
                            self.prediction_count_one_success += 1

                    # Cases where path count is 1 / 2
                    if self.max_paths < 3:
                        self.low_path_count += 1

                    # Infection test
                    infected_nodes = {x for y in self.nodes for x in self.mprs[y]} | self.nodes
                    infected_nodes -= {1, 2}
                    self.infection_all_mprs_count += len(infected_nodes)
                    if len(infected_nodes & self.nodes_send):
                        self.infection_all_mprs += 1

                    infected_nodes = {x for y in self.nodes for x in self.neighbors[y]} | self.nodes
                    infected_nodes -= {1, 2}
                    self.infection_all_neighbors_count += len(infected_nodes)
                    if len(infected_nodes & self.nodes_send):
                        self.infection_all_neighbors += 1

                    rand_bet_choice = random.choice(list(self.nodes))

                    infected_nodes = {x for x in self.mprs[rand_bet_choice]} | self.nodes
                    infected_nodes -= {1, 2}
                    self.infection_random_mprs_count += len(infected_nodes)
                    if len(infected_nodes & self.nodes_send):
                        self.infection_random_mprs += 1

                    infected_nodes = {x for x in self.neighbors[rand_bet_choice]} | self.nodes
                    infected_nodes -= {1, 2}
                    self.infection_random_neighbors_count += len(infected_nodes)
                    if len(infected_nodes & self.nodes_send):
                        self.infection_random_neighbors += 1

                # Cases where there was a real bottleneck
                if len(self.real_nodes) > 0:
                    self.real_bottleneck += 1
                    if len(self.real_nodes & self.nodes & self.nodes_send) > 0:
                        self.real_bottleneck_found += 1
                    # else:
                    #     print("---")
                    #     print(run_number)
                    #     print(real_nodes)
                    #     print(nodes)
                else:
                    self.no_real_bottleneck += 1
                    if len(self.nodes) == 0:
                        self.no_real_bottleneck_found += 1

                    else:  # No real bottleneck, yet we think there is. Infection test
                        # Infection test
                        infected_nodes = {x for y in self.nodes for x in self.mprs[y]} | self.nodes
                        infected_nodes -= {1, 2}
                        self.infection_all_mprs_count_no_bottleneck += len(infected_nodes)
                        if len(infected_nodes & self.nodes_send):
                            self.infection_all_mprs_no_bottleneck += 1

                        infected_nodes = {x for y in self.nodes for x in self.neighbors[y]} | self.nodes
                        infected_nodes -= {1, 2}
                        self.infection_all_neighbors_count_no_bottleneck += len(infected_nodes)
                        if len(infected_nodes & self.nodes_send):
                            self.infection_all_neighbors_no_bottleneck += 1

                        rand_bet_choice = random.choice(list(self.nodes))

                        infected_nodes = {x for x in self.mprs[rand_bet_choice]} | self.nodes
                        infected_nodes -= {1, 2}
                        self.infection_random_mprs_count_no_bottleneck += len(infected_nodes)
                        if len(infected_nodes & self.nodes_send):
                            self.infection_random_mprs_no_bottleneck += 1

                        infected_nodes = {x for x in self.neighbors[rand_bet_choice]} | self.nodes
                        infected_nodes -= {1, 2}
                        self.infection_random_neighbors_count_no_bottleneck += len(infected_nodes)
                        if len(infected_nodes & self.nodes_send):
                            self.infection_random_neighbors_no_bottleneck += 1

                # Count average amount of bets (Excluding 1's)
                if len(self.nodes) > 1:
                    self.avg_bet_amount += len(self.nodes)
                    self.avg_bet_amount_count += 1

                    rand_bet_choice = random.choice(list(self.nodes))
                    if rand_bet_choice in self.nodes_send:
                        self.rand_bet_success += 1

            # Pure random attack
            rand_bet_choice = random.choice(range(3,101))
            infected_nodes = {x for x in self.mprs[rand_bet_choice]} | self.nodes
            infected_nodes -= {1, 2}
            self.infection_true_random_mprs_count += len(infected_nodes)
            if len(infected_nodes & self.nodes_send):
                self.infection_true_random_mprs += 1

            # infected_nodes = {x for x in self.neighbors[rand_bet_choice]} | self.nodes
            infected_nodes = {x for x in self.neighbors.get(rand_bet_choice, set())} | self.nodes
            infected_nodes -= {1, 2}
            self.infection_true_random_neighbors_count += len(infected_nodes)
            if len(infected_nodes & self.nodes_send):
                self.infection_true_random_neighbors += 1

            # Tirza VS Random test
            # -- Random
            if len(self.nodes_random) > 0:
                self.tirza_random_total_random += 1
                random_choice = random.choice(list(self.nodes_random))
                if random_choice in self.nodes_send:
                    self.tirza_random_single_random += 1
                infected_nodes = {x for x in self.mprs[random_choice]} | {random_choice}
                infected_nodes -= {1, 2}
                self.tirza_random_mpr_infected_random += len(infected_nodes)
                if len(infected_nodes & self.nodes_send) > 0:
                    self.tirza_random_mpr_random += 1
                self._frac_update(random_choice, infected_nodes, self.factors_random_mpr, self.factors_random_mpr_infected)
                infected_nodes = {x for x in self.neighbors[random_choice]} | {random_choice}
                infected_nodes -= {1, 2}
                self.tirza_random_nei_infected_random += len(infected_nodes)
                if len(infected_nodes & self.nodes_send) > 0:
                    self.tirza_random_nei_random += 1
                self._frac_update(random_choice, infected_nodes, self.factors_random_nei, self.factors_random_nei_infected)

            # -- Tirza
            if len(self.nodes) > 0:
                self.tirza_random_total_tirza += 1
                random_choice = random.choice(list(self.nodes))
                if random_choice in self.nodes_send:
                    self.tirza_random_single_tirza += 1
                infected_nodes = {x for x in self.mprs[random_choice]} | {random_choice}
                infected_nodes -= {1, 2}
                self.tirza_random_mpr_infected_tirza += len(infected_nodes)
                if len(infected_nodes & self.nodes_send) > 0:
                    self.tirza_random_mpr_tirza += 1
                self._frac_update(random_choice, infected_nodes, self.factors_tirza_mpr, self.factors_tirza_mpr_infected)
                infected_nodes = {x for x in self.neighbors[random_choice]} | {random_choice}
                infected_nodes -= {1, 2}
                self.tirza_random_nei_infected_tirza += len(infected_nodes)
                if len(infected_nodes & self.nodes_send) > 0:
                    self.tirza_random_nei_tirza += 1
                self._frac_update(random_choice, infected_nodes, self.factors_tirza_nei, self.factors_tirza_nei_infected)

            # -- Bfs
            if len(self.nodes_random_bfs) > 0:
                self.tirza_random_total_random_bfs += 1
                random_choice = random.choice(list(self.nodes_random_bfs))
                if random_choice in self.nodes_send:
                    self.tirza_random_single_random_bfs += 1
                infected_nodes = {x for x in self.mprs[random_choice]} | {random_choice}
                infected_nodes -= {1, 2}
                self.tirza_random_mpr_infected_random_bfs += len(infected_nodes)
                if len(infected_nodes & self.nodes_send) > 0:
                    self.tirza_random_mpr_random_bfs += 1
                self._frac_update(random_choice, infected_nodes, self.factors_bfs_mpr, self.factors_bfs_mpr_infected)
                infected_nodes = {x for x in self.neighbors[random_choice]} | {random_choice}
                infected_nodes -= {1, 2}
                self.tirza_random_nei_infected_random_bfs += len(infected_nodes)
                if len(infected_nodes & self.nodes_send) > 0:
                    self.tirza_random_nei_random_bfs += 1
                self._frac_update(random_choice, infected_nodes, self.factors_bfs_nei, self.factors_bfs_nei_infected)

    def _frac_update(self, random_choice, infected_nodes, success_counters, infection_counters):
        inf = infected_nodes - {random_choice}
        for i in self.factors_to_test:
            success = []
            infection = []
            for j in range(0,100):
                to_sample = round(len(inf) * i / 100)
                sample = set(random.sample(inf, to_sample)) | {random_choice}
                infection.append(len(sample) - 1)
                success.append(int(len(sample & self.nodes_send) > 0))

            success_counters[i] += statistics.mean(success)
            infection_counters[i] += statistics.mean(infection)

    def _build_graph_from_tc(self, pov):
        adjg = defaultdict(set)
        for dest, last in self.tcs[pov]:
            adjg[last].add(dest)

            # Todo: Remove condition later, as it contains magic numbers and we want it 2 sided
            # if dest == 2:
            #     adjg[dest].add(last)
            adjg[dest].add(last)

        return adjg

    @staticmethod
    def _build_dag_from_graph(adjg, s ,t):
        adjc = defaultdict(set)
        topsort = []
        c = defaultdict(set)  # Color False == Not visited, True == Visited
        d = defaultdict(set)  # Distance.
        for f in adjg.keys():
            c[f] = False
            d[f] = float('inf')
        c[t] = False
        d[t] = float('inf') # Because who said t got selected as MPR
        c[s] = True
        d[s] = 0

        q = deque()
        q.append(s)
        while q:
            u = q.popleft()
            topsort.append(u)
            if (u != t) and (d[u]+1 <= d[t]):
                for v in adjg[u]:
                    if not c[v]:
                        c[v] = True
                        d[v] = d[u] + 1
                        adjc[u].add(v)
                        q.append(v)
                    elif d[u] < d[v]:
                        adjc[u].add(v)
        return adjc, topsort

    @staticmethod
    def _count_paths_in_dag(adjc, topsort, s, t):
        paths = []
        pre = defaultdict(int)
        post = defaultdict(int)
        pre[s] = 1
        post[t] = 1

        for x in topsort:
            for y in adjc[x]:
                pre[y] += pre[x]
        for x in reversed(topsort):
            for y in adjc[x]:
                post[x] += post[y]
        for x in adjc.keys():
            paths.append((x, pre[x] * post[x]))

        if post[s] != pre[t]:
            raise RuntimeError("Paths of S != Paths of T")
        paths.sort(key=itemgetter(1), reverse=True)
        return paths

    @staticmethod
    def _extract_bets_from_paths(paths, s, t):
        max_path = paths[0][1]
        calculated_nodes = set()

        # Make sure we got a path
        if max_path == 0:
            return calculated_nodes, True
        for n, p in paths:
            if p == max_path:
                calculated_nodes.add(n)
            else:
                break
        calculated_nodes -= {s, t}
        return calculated_nodes, False

    @staticmethod
    def _extract_random_from_paths(paths, s, t):
        max_path = paths[0][1]
        calculated_nodes = set()

        # Make sure we got a path
        if max_path == 0:
            return calculated_nodes, True
        for n, p in paths:
            if p > 0:
                calculated_nodes.add(n)
            else:
                break
        calculated_nodes -= {s, t}
        return calculated_nodes, False

    @staticmethod
    def _extract_random_from_graph(g, s, t):
        d = {}
        p = {}
        for v in g:
            d[v] = float("inf")
            p[v] = None

        p[t] = None
        q = deque()
        d[s] = 0
        q.append(s)

        while q:
            u = q.popleft()
            if u == t:
                break
            for v in g[u]:
                if d[v] == float("inf"):
                    d[v] = d[u]+1
                    p[v] = u
                    q.append(v)

        n = set()
        if p[t] == None:
            return n
        u = p[t]
        while  u != s:
            n.add(u)
            u = p[u]

        return n


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage is " + sys.argv[0] + " prefix")
        # exit()
        sys.argv.append('BottleNeckNeighbors_n100_1000x750_FixPos-1-Mobility-false-')

    for x in sys.argv[1::]:
        o = Infection(x)
        print(x)
        o.run()
        print()

