#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, sys

##### read config file
config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(os.path.realpath(__file__))) # read config file

dbHost = config.get('mysql','dbHost')
dbPort = int(config.get('mysql','dbPort'))
dbName = config.get('mysql','dbName')
tableName = config.get('mysql','tableName')

dbUser = config.get('mysql','dbUser')
dbPass = config.get('mysql','dbPass')

freegeoipAPI = config.get('geoLookup', 'freeGeoIpAPI')  
telizeAPI = config.get('geoLookup', 'telizeAPI')
timeOut = int(config.get('geoLookup', 'timeOut'))

##### what to do on errors
def onError(errorCode, extra):
    print "\n*** Error:"
    if errorCode == 1:
        print extra
        usage(errorCode)
    elif errorCode == 2:
        print "    No options given"
        usage(errorCode)
    elif errorCode == 3:
        print "    No program part chosen"
        usage(errorCode)
    elif errorCode in (4, 5, 6, 8, 12, 13):
        print "    %s" % extra
        sys.exit(errorCode)
    elif errorCode in (7, 9, 10, 11):
        print "    %s" % extra

##### some help
def usage(exitCode):
    print "\nUsage:"
    print "----------------------------------------"
    print "%s --setupdb [-v]" % sys.argv[0]
    print "      Initial 's'etup. Add required databases, tables and users"
    print "        Options: 'v'erbose output"
    print "    OR"
    print "%s -w -n <name> -q <protocol> -p <port> -i <ip> -e <event> [-v]" % sys.argv[0]
    print "      'W'rite log to database"
    print "        Arguments: 'n'ame of service"
    print "                   'q' protocol, tcp, udp etc."
    print "                   'p'ort"
    print "                   'i'p number"
    print "                   'e'vent causing this log"
    print "        Options: 'v'erbose output"
    print "    OR"
    print "%s -s [-i <ip>]|[-n <service>]|[-c <country> [-v]" % sys.argv[0]
    print "      View 's'tatistics from the database"
    print "        Options: view extended info of 'i'p"
    print "                 view extended info of services 'n'ame"
    print "                 view extended info of 'c'ountry"
    print "                 'v'erbose output"
    print "%s -x [-v]" % sys.argv[0]
    print "      View normal statisitcs and e'x'tended info on all items"
    print "        Options: 'v'erbose output"
    print "    OR"
    print "%s -h" % sys.argv[0]
    print "      Prints this"
    sys.exit(exitCode)
    
def displayIpInfo(ipInfo, verbose):
    textKeyPairs = (
                    ('City', 'city'),
                    ('Region', 'region'),
                    ('Country', 'country'),
                    ('Latitude', 'latitude'),
                    ('Longitude', 'longitude'),
                    ('Region code', 'regionCode'),
                    ('Country code', 'countryCode'),
                    ('3-letter country code', 'countryCode3'),
                    ('Continent code', 'continentCode'),
                    ('Time Zone', 'timeZone'),
                    ('Offset', 'offset'),
                    ('Postal code', 'postalCode'),
                    ('Area code', 'areaCode'),
                    ('Metro code', 'metroCode'),
                    ('DMA code', 'dmaCode'),
                    ('ASN', 'asn'),
                    ('ISP', 'isp'),
                    ('Geo source', 'geoSource')
                    )
    
    for text, key in textKeyPairs:
        if ipInfo.has_key(key):
            print "--- %s: %s" % (text, ipInfo[key])