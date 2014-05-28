#! /usr/bin/python
#############################################################################
#   get_cpu_load.py
#
#   Created: 10/12/09
#   Author : Krishna Sandeep Reddy Dubba    
#   Email  : scksrd@leeds.ac.uk
#   Purpose: Get load of the cpu
#
#   This program is part of the CO-FRIEND project, partially funded by the
#   European Commission under the 7th Framework Program.
#
#   See http://www.co-friend.net
#
#   (C) University of Leeds - Co-friend Consortium
#############################################################################

import time

TIMEFORMAT = "%m/%d/%y %H:%M:%S"
INTERVAL = 2

def getTimeList():
    statFile = file("/proc/stat", "r")
    timeList = statFile.readline().split(" ")[2:6]
    statFile.close()
    for i in range(len(timeList)) :
        timeList[i] = int(timeList[i])
    return timeList

def deltaTime(interval) :
    x = getTimeList()
    time.sleep(interval)
    y = getTimeList()
    for i in range(len(x)) :
        y[i] -= x[i]
    return y

def print_cpu_load():
    # On remote systems we can get the printed stuff using ssh
    dt = deltaTime(INTERVAL)
    timeStamp = time.strftime(TIMEFORMAT)
    cpuPct = 100 - (dt[len(dt) - 1] * 100.00 / sum(dt))
    print str('%.4f' %cpuPct)

def mem_avail():
    lines = open("/proc/meminfo").readlines()
    mem_total = eval(lines[0].split()[1])
    buffers   = eval(lines[2].split()[1])
    cache     = eval(lines[3].split()[1])
    mem_avail = (mem_total + buffers - cache)/1024
    return mem_avail
    
if __name__ == "__main__" :
    lines = open("/proc/meminfo").readlines()
    # second line has memory available info. Ex: 'MemTotal:  3995052 kB\n'
    mem_total = eval(lines[0].split()[1])
    buffers   = eval(lines[2].split()[1])
    cache     = eval(lines[3].split()[1])
    mem_avail = (mem_total + buffers - cache)/1024
    dt = deltaTime(INTERVAL)
    timeStamp = time.strftime(TIMEFORMAT)
    cpuPct = 100 - (dt[len(dt) - 1] * 100.00 / sum(dt))
    print str('%.4f %.d' %(cpuPct, mem_avail))
    