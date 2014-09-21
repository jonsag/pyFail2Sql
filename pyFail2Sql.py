#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import getopt
from functions import *

writeLog = False
verbose = False
setupDatabase = False

############### handle arguments ###############
try:
    myopts, args = getopt.getopt(sys.argv[1:],'wn:q:p:i:e:vh' , ['write', 'name=', 'protocol=', 'port=', 'ip=', 'event=', 'setupdb', 'verbose', 'help'])

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
    elif option in ('-v', '--verbose'):
        verbose = True
    elif option in ('--setupdb'):
        setupDatabase = True
    elif option in ('-h', '--help'):
        usage(0)
        
if setupDatabase:
    setupDB(verbose)    
    
if writeLog:
    log = (name, protocol, port, ip, event)
    ipInfo = lookupIP(ip, verbose)
    sql = logSql(log, ipInfo, verbose)
    if verbose:
        print sql
    doQuery(sql, verbose)
    
    