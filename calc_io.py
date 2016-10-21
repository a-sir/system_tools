# -*- coding: utf-8 -*-

import os
import re
import time
import operator

# sample /proc/*/io file:
#
# rchar: 3137705814
# wchar: 1553443304
# syscr: 2411962
# syscw: 4794295
# read_bytes: 138502144
# write_bytes: 1190215680
# cancelled_write_bytes: 182579200


def read_proc(fname):
    d = dict()
    with open(fname) as f:
        for line in f:
            tokens = line.split(' ')
            name = tokens[0][0:len(tokens[0])-1]
            value = tokens[1][0:len(tokens[1])-1]
            d[name] = int(value)
    return d


def read_stats():
    pattern = re.compile("^[0-9]+$")
    data = dict()
    for path in os.popen("find /proc/*/io").read().split('\n'):
        tokens = path.split('/')
        if len(tokens) == 4:
            pid = tokens[2]
            if pattern.match(pid):
                try :
                    data[pid] = read_proc(path)
                except IOError:
                    pass
    return data


def calc_diff_for_pid(attr1, attr2):
    res = dict()
    for k, v in attr2.items():
        res[k] = v - attr1[k]
    return res


def calc_diff_for_stats(stats1, stats2):
    diff = dict()
    for pid in stats2:
        if pid in stats1:
            diff[pid] = calc_diff_for_pid(stats1[pid], stats2[pid])
    return diff


def extract_param(pid_to_stats, param_name):
    d = dict()
    for pid, v in pid_to_stats.items():
        d[pid] = v[param_name]
    return d


def top10_by_value(pid_to_value):
    sorted_map = sorted(pid_to_value.items(), key=operator.itemgetter(1))
    sorted_map.reverse()
    return sorted_map[0:min(9, len(sorted_map) - 1)]


def collect_pid_names(pids):
    names = dict()
    for pid in pids:
        names[pid] = os.popen("ps aux | awk '{if ($2==" + str(pid) + ") print $11}'").read().split('\n')[0]
    return names


def print_top(pid_params, pid_names, param):
    i = 1
    print "№ PID\t" + param + "\tprocess"
    for pid, value in pid_params:
        if value > 0:
            name = pid_names[pid]
            print str(i) + " " + str(pid) + "\t" + str(value) + "\t" + str(name)
            i += 1


period_sec=10
print "Script will calculate differences in /proc/PID/io within " + str(period_sec) + " seconds."

orig = read_stats()

time.sleep(period_sec)

updated = read_stats()
names = collect_pid_names(updated.keys())

diff = calc_diff_for_stats(orig, updated)

for param in ['rchar', 'wchar', 'syscr', 'syscw', 'read_bytes', 'write_bytes']:
    print "Parameter " + param
    top = top10_by_value(extract_param(diff, param))
    print_top(top, names, param)
