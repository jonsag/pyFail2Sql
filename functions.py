#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, sys, os, urllib2, socket
import mysql.connector, json

import xml.etree.ElementTree as ET

#from mysql.connector import errorcode
from datetime import datetime

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser, NmapParserException

from time import sleep

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
    

    
def siteHasData(api, ip, verbose):
    responseCode = ""
    response = ""
    if verbose:
        print "--- Checking if %s is up..." % api
    try:
        responseCode = urllib2.urlopen(api, timeout = timeOut).getcode()
    except urllib2.URLError, e:
        if verbose:
            print "*** There was an error: %r" % e
    if responseCode and verbose:
        print "--- Response code: %s" % responseCode
    if responseCode == 200:
        if verbose:
            print "--- Site is up"
            print "--- Checking for data at: %s%s" % (api, ip)
        try:
            response = urllib2.urlopen("%s%s" % (api, ip), timeout = timeOut).read() # get data from server
            if verbose:
                print "--- Got data"
        except urllib2.URLError, e:
            if verbose:
                print "*** There was an error: %r" % e
                print "*** Could not get data"
    else:
        if verbose:
            print "*** Site is down"
    return response

def lookupIP(ip, verbose): # get geographical data for ip
    response = siteHasData(freegeoipAPI, ip, verbose)
    if response:
        if verbose:
            print "--- Parsing geographical information..."
        ipInfo = freegeoipLookup(response, verbose)
    else:
        response = siteHasData(telizeAPI, ip, verbose)
        if response:
            if verbose:
                print "--- Parsing geographical information..."
            ipInfo = telizeLookup(response, verbose) 
        else:
            if verbose:
                print "*** Returning empty values"
            ipInfo = {'longitude': "na", 'latitude': "na", 'countryCode': "na",
                  'city': "na", 'country': "na", 'regionCode': "na", 'region': "na",
                  'geoSource': "na",'offset': "na", 'timeZone': "na",
                  'countryCode3': "na", 'isp': "na",'postalCode': "na",
                  'metroCode': "na", 'areaCode': "na"}
        
    return ipInfo

def telizeLookup(response, verbose):
    longitude = "na"
    latitude = "na"
    countryCode = "na"
    countryCode3 = "na"
    country = "na"
    isp = "na"
    continentCode = "na"
    city = "na"
    timeZone = "na"
    regionCode = "na"
    offset = "na"
    areaCode = "na"
    postalCode = "na"
    dmaCode = "na"
    asn = "na"
    geoSource = "telize.com"

    if verbose:
        print "--- Response:\n%s" % response
    data = json.loads(response)        
            
    if data.has_key('longitude'): # longitude
        longitude = data['longitude']
        if verbose:
            print "--- Longitude: %s" % longitude
    if data.has_key('latitude'): # latitude
        latitude = data['latitude']
        if verbose:
            print "--- Latitude: %s" % latitude
    if data.has_key('country_code'): # country code
        countryCode = data['country_code']
        if verbose:
            print "--- Country code: %s" % countryCode
    if data.has_key('country_code3'): # 3-letter country code
        countryCode3 = data['country_code3']
        if verbose:
            print "--- 3-letter country code: %s" % countryCode3
    if data.has_key('country'): # country
        country = data['country']
        if verbose:
            print "--- Country: %s" % country
    if data.has_key('isp'): # ISP
        isp = data['isp']
        if verbose:
            print "--- ISP: %s" % isp
    if data.has_key('continent_code'): # continent code
        continentCode = data['continent_code']
        if verbose:
            print "--- Continent code: %s" % continentCode
    if data.has_key('city'): # city
        city = data['city']
        if verbose:
            print "--- City: %s" % city
    if data.has_key('timezone'): # time zone
        timeZone = data['timezone']
        if verbose:
            print "--- Time zone: %s" % timeZone
    if data.has_key('region'): # region
        region = data['region']
        if verbose:
            print "--- Region: %s" % region
    else:
        region = "na"
        if verbose:
            print "*** Region not retreived"
    if data.has_key('region_code'): # region code
        regionCode = data['region_code']
        if verbose:
            print "--- Region code: %s" % regionCode
    if data.has_key('offset'): # offset
        offset = data['offset']
        if verbose:
            print "--- Offset: %s" % offset
    if data.has_key('area_code'): # area code
        areaCode = data['area_code']
        if verbose:
            print "--- Area code: %s" % areaCode
    if data.has_key('postal_code'): # postal code
        postalCode = data['postal_code']
        if verbose:
            print "--- postal code: %s" % postalCode
    if data.has_key('dma_code'): # dma code
        dmaCode = data['dma_code']
        if verbose:
            print "--- postal code: %s" % dmaCode
    if data.has_key('asn'): # asn
        asn = data['asn']
        if verbose:
            print "--- postal code: %s" % asn     

    ipInfo = {'longitude': longitude, 'latitude': latitude, 'countryCode': countryCode,
              'city': city, 'country': country, 'regionCode': regionCode, 'region': region,
              'geoSource': geoSource,'offset': offset, 'timeZone': timeZone,
              'countryCode3': countryCode3, 'isp': isp, 'continentCode': continentCode,
              'areaCode': areaCode, 'postalCode': postalCode, 'dmaCode': dmaCode,
              'asn': asn}
    
    return ipInfo

def freegeoipLookup(response, verbose):
    countryCode = "na"
    country = "na"
    regionCode = "na"
    region = "na"
    city = "na"
    postalCode = "na"
    latitude = "na"
    longitude = "na"
    metroCode = "na"
    areaCode = "na"
    geoSource = "freegeoip.net"
    
    if verbose:
        print "--- Response:\n%s" % response
    xmlRoot = ET.fromstring(response) # read xml
    
    for xmlChild in xmlRoot:

        if 'CountryCode' in xmlChild.tag:
            countryCode = xmlChild.text
            if verbose:
                print "--- Country code: %s" % countryCode
        elif 'CountryName' in xmlChild.tag:
            country = xmlChild.text
            if verbose:
                print "--- Country: %s" % country
        elif 'RegionCode' in xmlChild.tag:
            regionCode = xmlChild.text
            if verbose:
                print "--- Region code: %s" % regionCode
        elif 'RegionName' in xmlChild.tag:
            region = xmlChild.text
            if verbose:
                print "--- Region: %s" % region
        elif 'City' in xmlChild.tag:
            city = xmlChild.text
            if verbose:
                print "--- City: %s" % city
        elif 'ZipCode' in xmlChild.tag:
            postalCode = xmlChild.text
            if verbose:
                print "--- Zip code: %s" % postalCode
        elif 'Latitude' in xmlChild.tag:
            latitude = xmlChild.text
            if verbose:
                print "--- Latitude: %s" % latitude
        elif 'Longitude' in xmlChild.tag:
            longitude = xmlChild.text
            if verbose:
                print "--- Longitude: %s" % longitude
        elif 'MetroCode' in xmlChild.tag:
            metroCode = xmlChild.text
            if verbose:
                print "--- Metro code: %s" % metroCode
        elif 'AreaCode' in xmlChild.tag:
            areaCode = xmlChild.text
            if verbose:
                print "--- Area code: %s" % areaCode
    
    ipInfo = {'longitude': longitude, 'latitude': latitude, 'countryCode': countryCode,
              'city': city, 'country': country, 'regionCode': regionCode, 'region': region,
              'geoSource': geoSource, 'postalCode': postalCode,
              'metroCode': metroCode, 'areaCode': areaCode}
    
    return ipInfo

def logSql(log, ipInfo, verbose): # create sql for the log
    name, protocol, port, ip, event = log
    sql = (
        "INSERT INTO %s"
        " (`name`, `protocol`, `port`, `ip`, `event`, `longitude`, `latitude`,"
        " `countryCode`, `city`, `country`, `regionCode`,"
        " `region`, `geoSource`)"
        " VALUES"
        " ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
        % (tableName,
           name, protocol, port, ip, event, ipInfo['longitude'], ipInfo['latitude'],
           ipInfo['countryCode'], ipInfo['city'], ipInfo['country'], ipInfo['regionCode'],
           ipInfo['region'], ipInfo['geoSource']))
           
    if verbose:
        print "+++ sql = %s" % sql
    return sql

def connect(dbName, verbose): # connect to database as normal user
    if verbose:
        print "--- Connecting to db server %s..." % dbHost
        
    try:
        cnx = mysql.connector.connect(user = dbUser, password = dbPass, host = dbHost, port = dbPort, database = dbName)
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            onError(4, "*** Something is wrong with your user name or password\n    Have you run with argument '--setupdb' yet?")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            onError(5, "*** Database does not exists\n    Run again with argument '--setupdb'")
        else:
            onError(6, "*** %s" % err)
            
    if verbose:
        print "    OK"
    return cnx
    
def disconnect(cnx, verbose): # disconnect from database
    if verbose:
        print "--- Disconnecting from db server %s..." % dbHost
    cnx.close()
        
def doQuery(sql, verbose): # write log to database
    result = False
    cnx =connect(dbName, verbose) # connect to database
    
    if cnx:
        cursor = cnx.cursor() # create cursor
        if verbose:
            print "--- Writing to database"
            
        try: # write log
            cursor.execute(sql)
        except mysql.connector.Error as err:
            onError(9, err.msg)
        else:
            result = True
            if verbose:
                print "    OK"
            
        cnx.commit() # commit changes
        cursor.close() 
    disconnect(cnx, verbose) # disconnect from database
    return result

def executeSql(cursor, sql, verbose):
    if verbose:
        print "--- Querying database"
        print "+++ sql = %s" % sql
    try: # get answer
        cursor.execute(sql)
    except mysql.connector.Error as err:
        onError(9, err.msg)
    else:
        if verbose:
            print "    OK"
    return cursor  

def showStatistics(extendedStats, verbose):
    stat = []
    statCount = 0
    
    cnx =connect(dbName, verbose) # connect to database
    print "Statistics:"
    print "------------------------------------------------------------------"

    cursor = cnx.cursor() # create cursor
        
    fieldList = (["ip", "IP"], ["country", "Country"], ["name", "Service"])
        
    for field, text in fieldList:
        temp = []
        print "%s:" % text
        sql = "SELECT %s, COUNT(*) FROM %s GROUP BY %s" % (field, tableName, field)            
        cursor = executeSql(cursor, sql, verbose)
        for field, count in cursor:
            if count == 1:
                word = "time"
            else:
                word = "times"
            print "%s\tbanned: %s %s" % (field, count, word)
            temp.append(field)
        print
        stat.append(temp)
        
    if extendedStats:
        for searchField, text in fieldList:
            for searchTerm in stat[statCount]:
                showExtendedStats(searchField, searchTerm, verbose)
            statCount += 1
        
    cursor.close()
    disconnect(cnx, verbose) # disconnect from database
    
def showExtendedStats(searchField, searchTerm, verbose):
    cnx =connect(dbName, verbose) # connect to database
    print "Statistics on %s %s:" % (searchField, searchTerm)
    print "------------------------------------------------------------------"
    
    cursor = cnx.cursor() # create cursor
    
    sql = "SELECT %s, COUNT(*) FROM %s WHERE %s = '%s'" % (searchField, tableName, searchField, searchTerm)
    cursor = executeSql(cursor, sql, verbose)
    for field, count in cursor:
        if count > 0:
            if count == 1:
                word = "time"
            else:
                word = "times"
            print "banned: %s %s" % (count, word)
            
            sql = "SELECT `timeStamp`, `ip`, `city`, `country`, `countryCode` FROM %s WHERE %s = '%s'" % (tableName, searchField, searchTerm)
            cursor = executeSql(cursor, sql, verbose)
            for timeStamp, ip, city, country, countryCode in cursor:
                print "%s\t%s\t%s, %s" % (timeStamp, ip, city, country)
            print
        else:
            print "%s does not occur in database" % field
            print
            
    cursor.close()
    disconnect(cnx, verbose) # disconnect from database  
    
def scanIp(ip, verbose):
    openPorts = []
    startPort = int(config.get('attack','startPort'))
    endPort = int(config.get('attack','endPort'))
    
    # Print a nice banner with information on which host we are about to scan
    print "Scanning remote ip %s from port %s to %s..." %  (ip, startPort, endPort)

    # Check what time the scan started
    startTime = datetime.now()
    if verbose:
        print "--- Start time: %s" % startTime
        
    # Using the range function to specify ports (here it will scans all ports between 1 and 1024)
    # We also put in some error handling for catching errors

    try:
        for port in range(startPort, endPort):
            if verbose:
                print "--- Trying port %s" % port
            else:
                sys.stdout.write("%s " % port)
                sys.stdout.flush()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((ip, port))
            if result == 0:
                if verbose:
                    print "Port {}: \t Open".format(port)
                else:
                    print "\nPort {}: \t Open".format(port)
                openPorts.append(port)
            sock.close()
    except KeyboardInterrupt:
        print "*** You pressed Ctrl+C"
        sys.exit()
    except socket.gaierror:
        print '*** Hostname could not be resolved. Exiting'
        sys.exit()
    except socket.error:
        print "*** Couldn't connect to server"
        sys.exit()

    # Checking the time again
    endTime = datetime.now()
    if verbose:
        print "Finished time: %s" % endTime

    # Calculates the difference of time, to see how long it took to run the script
    totalTime =  endTime - startTime

    # Printing the information to screen
    print '\nScanning completed in: ', totalTime
    
    if openPorts:
        print "\nThese ports were open:"
        for openPort in openPorts:
            print openPort
    else:
        print "\nCould not find any open ports"
        
def nmapScan(targets, options, verbose):
    parsed = None
    nmproc = NmapProcess(targets, options)
    
    #rc = nmproc.run()
    rc = nmproc.run_background()
    
    #if rc != 0:
    #    print("nmap scan failed: {0}".format(nmproc.stderr))
    #print(type(nmproc.stdout))
    
    while nmproc.is_running():
        print("Nmap Scan running: ETC: {0} DONE: {1}%".format(nmproc.etc, nmproc.progress))
        sleep(2)

    print("rc: {0} output: {1}".format(nmproc.rc, nmproc.summary))

    try:
        nmap_report = NmapParser.parse(nmproc.stdout)
    except NmapParserException as e:
        print("Exception raised while parsing scan: {0}".format(e.msg))

    return nmap_report

def printScan(nmap_report, verbose):
    print("\nStarting Nmap {0} ( http://nmap.org ) at {1}".format(
        nmap_report.version,
        nmap_report.started))

    for host in nmap_report.hosts:
    
        
        if len(host.hostnames):
            tmp_host = host.hostnames.pop()
        else:
            tmp_host = host.address

        print("Nmap scan report for {0} ({1})".format(tmp_host,
                                                      host.address))
        print("\nHost is {0}.".format(host.status))
        print("\n  PORT     STATE         SERVICE      VERSION")

        for serv in host.services:
            pserv = "{0:>5s}/{1:3s}  {2:12s}  {3:10s}  {4}".format(str(serv.port),
                                                                 serv.protocol,
                                                                 serv.state,
                                                                 serv.service,
                                                                 serv.servicefp)
            if len(serv.banner):
                pserv += " ({0})".format(serv.banner)
            print(pserv)
        
    print("\n{}".format(nmap_report.summary))

def nmap(ip, verbose):
    startPort = int(config.get('attack','startPort'))
    endPort = int(config.get('attack','endPort'))
    
    report = nmapScan(ip, "-sV -p %s-%s" % (startPort, endPort), verbose)
    if report:
        printScan(report, verbose)
    else:
        print("No results returned")

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
        