#!/usr/bin/env python3
import sys, re, os
import numpy
import csv

if (len(sys.argv) < 4):
    print("Usage is " + sys.argv[0] + " [NumberOfNodes] [AttackTypes] [DefenceNumbers]")
    exit()

def parseFile(file_name):
    with open(file_name, 'r') as f:
        contents = f.read()
        it = re.finditer('This is[ \w]*$', contents, re.MULTILINE)
        regex = re.compile('^This is[ \w]*$', re.MULTILINE)
        tmp = regex.sub('', contents)
        tmp = re.sub('[a-zA-Z:\n]', '', tmp)
        tmp = re.sub('^\s+', '', tmp)
        tmp = re.split('[\s]+', tmp)
        lst = list()
        for x in tmp:
            lst.append(int(x))
        #print(sum(lst)/len(lst))
        #print("File: " + sys.argv[1])
        return [numpy.mean(lst), numpy.std(lst), numpy.median(lst), len(lst)]

def parseAll():
    with open('Isolation.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, dialect='excel')
        name_template = "Blackhole_n%s_AttackType-%s_Defence-%s_log.txt"
        number_of_nodes = sys.argv[1].split(' ')
        attack_types = sys.argv[2].split(' ')
        defence_numbers = sys.argv[3].split(' ')

        csv_writer.writerow(["", "mean", "std", "median", "length"])
        for n in number_of_nodes:
            for attack in attack_types:
                for defence in defence_numbers:
                    mean, std, median, length = parseFile(name_template % (n, attack, defence))
                    csv_writer.writerow([name_template % (n, attack, defence), mean, std, median, length])

if __name__ == "__main__":
    parseAll()
