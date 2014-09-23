#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import getopt
from functions import *

writeLog = False
verbose = False
setupDatabase = False
statistics = False

name = ""
protocol = ""
port = ""
ip = ""
event = ""
country = ""

############### handle arguments ###############
try:
    myopts, args = getopt.getopt(sys.argv[1:],'wsn:q:p:i:e:c:vh' ,
    ['write', 'statistics', 'name=', 'protocol=', 'port=', 'ip=', 'event=', 'country=', 'setupdb', 'verbose', 'help'])

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
    elif option in ('--setupdb'):
        setupDatabase = True   
    elif option in ('-h', '--help'):
        usage(0)
        
if setupDatabase:
    setupDB(verbose)    
    
if writeLog:
    log = (name, protocol, port, ip, event) # declare the log to write
    ipInfo = lookupIP(ip, verbose) # get geographical info of ip
    sql = logSql(log, ipInfo, verbose) # construct sql
    if verbose:
        print sql
    result = doQuery(sql, verbose) # write to log
    
if statistics and not ip and not country and not name:
    showStatistics(verbose)
elif statistics and ip:
    #showIpStats(ip, verbose)
    showExtendedStats("ip", ip, verbose)
elif statistics and country:
    #showCountryStats(country, verbose)
    showExtendedStats("country", country, verbose)
elif statistics and name:
    #showServiceStats(name, verbose)
    showExtendedStats("name", name, verbose)
    