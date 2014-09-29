#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import getopt
from functions import *

writeLog = False
verbose = False
setupDatabase = False
statistics = False
extendedStats = False
attack = False
lookup = False

name = ""
protocol = ""
port = ""
ip = ""
event = ""
country = ""
rootUser = ""
rootPass = ""

############### handle arguments ###############
try:
    myopts, args = getopt.getopt(sys.argv[1:],'wsxaln:q:p:i:e:c:vh' ,
    ['write', 'statistics', 'extendedstatistics', 'attack', 'lookup'
     'name=', 'protocol=', 'port=', 'ip=', 'event=', 'country=',
     'setupdb', 'rootuser=', 'rootpass=', 'verbose', 'help'])

except getopt.GetoptError as e:
    onError(1, str(e))

if len(sys.argv) == 1: # no options passed
    onError(2, 2)
    
for option, argument in myopts:
    if option in ('-w', '--write'):
        writeLog = True
    elif option in ('-n', '--name'):
        name = argument
    elif option in ('-q', '--protocol'):
        protocol = argument
    elif option in ('-p', '--port'):
        port = argument
    elif option in ('-i', '--ip'):
        ip = argument
    elif option in ('-e', '--event'):
        event = argument
    elif option in ('-c', '--country'):
        country = argument
    elif option in ('-v', '--verbose'):
        verbose = True
    elif option in ('-s', '--statistics'):
        statistics = True
    elif option in ('-x', '--extendedstatististics'):
        statistics = True
        extendedStats = True
    elif option in ('-a', '--attack'):
        attack = True
    elif option in ('-l', '--lookup'):
        lookup = True
    elif option in ('--setupdb'):
        setupDatabase = True
    elif option in ('--rootuser'):
        rootUser = argument
    elif option in ('--rootpass'):
        rootPass = argument
    elif option in ('-h', '--help'):
        usage(0)
        
if not setupDatabase and not writeLog and not statistics and not attack and not lookup:
    onError(3, 3)
        
if setupDatabase:
    setupDB(rootUser, rootPass, verbose)    
    
if writeLog:
    log = (name, protocol, port, ip, event) # declare the log to write
    ipInfo = lookupIP(ip, verbose) # get geographical info of ip
    sql = logSql(log, ipInfo, verbose) # construct sql
    if verbose:
        print sql
    result = doQuery(sql, verbose) # write to log
    
if statistics and not ip and not country and not name:
    showStatistics(extendedStats, verbose)
elif statistics and ip:
    showExtendedStats("ip", ip, verbose)
elif statistics and country:
    showExtendedStats("country", country, verbose)
elif statistics and name:
    showExtendedStats("name", name, verbose)
    
if attack and ip:
    #scanIp(ip, verbose)
    nmap(ip, verbose)
elif attack and not ip:
    onError(12, "Option -a requires -i <ip>")
    
if lookup and ip:
    ipInfo = lookupIP(ip, verbose)

    print "\nResult:"
    print "-" * 60
    displayIpInfo(ipInfo, verbose)
elif lookup and not ip:
    onError(13, "Option -l requires -i <ip>")