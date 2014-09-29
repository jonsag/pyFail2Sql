#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, sys, os, urllib2, socket
import mysql.connector, json

import xml.etree.ElementTree as ET

from mysql.connector import errorcode
from datetime import datetime
from getpass import getpass

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser, NmapParserException

from time import sleep
from pprint import pprint

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
    
def create_database(cursor):
    try:
        cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(dbName))
    except mysql.connector.Error as err:
        onError(7, "Failed creating database: {}".format(err))
    
def setupDB(rootUser, rootPass, verbose): # setup the database with tables and users
    dbExists = False

    tables = {} # these are the tables that will be created
    tables[tableName] = (
    "CREATE TABLE %s ("
    "  `no` int(11) NOT NULL AUTO_INCREMENT,"
    "  PRIMARY KEY (`no`)"
    ") ENGINE=InnoDB" % tableName)
    
    columns = []
    for column, value in (["no", "int(11) NOT NULL AUTO_INCREMENT"],
                          ["timeStamp", "TIMESTAMP"],
                          ["name", "varchar(10)"],
                          ["protocol", "varchar(3)"],
                          ["port", "int(5)"],
                          ["ip", "varchar(15)]"],
                          ["event", "varchar(15)"],
                          ["longitude", "varchar(10)"],
                          ["latitude", "varchar(10)"],
                          ["countryCode", "varchar(2)"],
                          ["city", "varchar(20)"],
                          ["country", "varchar(20)"],
                          ["regionCode", "varchar(3)"],
                          ["region", "varchar(20)"],
                          ["geoSource", "varchar(30)"]):
        
        columns.append(["%s" % tableName, "ALTER TABLE %s ADD `%s` %s" % (tableName, column, value)])
    
    for table, sql in columns:
        print "%s - %s" % (table, sql)
        #print line
    
    if verbose:
        print "--- Setting up database"
    
    if not rootUser:
        rootUser = raw_input("User with rights to create database: ") # get user
    if not rootPass:
        rootPass = getpass("Password: ") # get user's passsword
    
    if verbose:
        print "Username: %s\nPassword: %s" % (rootUser, rootPass)
        print "--- Connecting to db server %s..." % dbHost
    
    try: # connect to database
        cnx = mysql.connector.connect(user = rootUser, password = rootPass, host = dbHost, port = dbPort)
    except mysql.connector.Error as err: # get errors
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            onError(4, "Something is wrong with your user name or password\n    Have you run with argument '--setupdb' yet?")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            onError(5, "Database does not exists\n    Run again with argument '--setupdb'")
        else:
            onError(6, err)
        
    if verbose:
        print "    OK"
        print "--- Creating database %s with all tables we need..." % dbName
        
    cursor = cnx.cursor() # construct cursor to use
    
    sql = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '%s'" % dbName
    if verbose:
        print "--- Checking if database already exists"
        print "+++ sql = %s" % sql
    try: # execute the sql
        cursor.execute(sql)
    except mysql.connector.Error as err:
        onError(10, "Failed checking if database exists: {}".format(err))
    
    result = cursor.fetchall()
    for line in result:
        if line[0] == dbName:
            if verbose:
                print "--- Database exists"
                dbExists = True
    if not dbExists:
        if verbose:
            print "--- Database does not exist. Creating it..." 
    
        sql = "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(dbName) # the sql for creating tables
        if verbose:
            print "+++ sql = %s" % sql
        try: # execute the sql
            cursor.execute(sql)
        except mysql.connector.Error as err:
            onError(7, "Failed creating database: {}".format(err))
    
        if verbose:
            print "    OK"

    if verbose:
        print "--- Setting database..."        
    try:
        cnx.database = dbName
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            cnx.database = dbName
        else:
                onError(8, err)
    
    if verbose:
        print "    OK"
        print "--- Creating tables..."
    
    for name, ddl in tables.iteritems(): # create the tables one by one
        print "--- Creating %s..." % name
        if verbose:
            print "+++ sql = %s" % ddl
        try:
            #print("Creating table {}: ".format(name), end='')
            cursor.execute(ddl)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                onError(11, "Table %s already exists" % name)
            else:
                onError(9, err.msg)
        else:
            if verbose:
                print "    OK"
                print "--- Creating user %s..." % dbUser
            
    sql = "CREATE USER '%s'@'localhost' IDENTIFIED BY '%s'" % (dbUser, dbPass) # sql for creating user
    if verbose:
        print "+++ sql = %s" % sql
    try: # create user
        cursor.execute(sql)
    except mysql.connector.Error as err:
        onError(9, err.msg)
    else:
        if verbose:
            print "    OK"
            print "--- Adding privileges"
        
    sql = "GRANT ALL PRIVILEGES ON %s.* TO '%s'@'localhost' WITH GRANT OPTION" % (dbName, dbUser) # sql for grants
    if verbose:
        print "+++ sql = %s" % sql
    try: # create grants for normal user
        cursor.execute(sql)
    except mysql.connector.Error as err:
        onError(9, err.msg)
    else:
        if verbose:
            print "    OK"

    cursor.close()
    disconnect(cnx, verbose) # dosconnect from database
    sys.exit(0)
    
def siteIsUp(api, verbose):
    responseCode = ""
    siteUp = False
    
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
        siteUp = True
        if verbose:
            print "--- Site is up"
    else:
        if verbose:
            print "*** Site is down"
    return siteUp

def lookupIP(ip, verbose): # get geographical data for ip
    if siteIsUp(freegeoipAPI, verbose):
        if verbose:
            print "--- Getting geographical information from %s" % freegeoipAPI
        ipInfo = freegeoipLookup(ip, verbose)
    elif siteIsUp(telizeAPI, verbose):
        if verbose:
            print "--- Getting geographical information from %s" % telizeAPI
        ipInfo = telizeLookup(ip, verbose) 
    else:
        if verbose:
            print "*** Returning empty values"
        ipInfo = {'longitude': "na", 'latitude': "na", 'countryCode': "na",
              'city': "na", 'country': "na", 'regionCode': "na", 'region': "na",
              'geoSource': "na",'offset': "na", 'timeZone': "na",
              'countryCode3': "na", 'isp': "na",'zipCode': "na",
              'metroCode': "na", 'areaCode': "na"}
        
    return ipInfo

def telizeLookup(ip, verbose):
    geoSource = "freegeoip.net"
    
    try:
        response = urllib2.urlopen("%s%s" % (telizeAPI, ip), timeout = timeOut).read() # get xml from freegeoip
    except urllib2.URLError, e:
        if verbose:
            print "*** There was an error: %r" % e
        
    if response:
        if verbose:
            print "--- Response:\n%s" % response
        data = json.loads(response)
            
        try: # longitude
            longitude = data['longitude']
            if verbose:
                print "--- Longitude: %s" % longitude
        except KeyError:
            longitude = "na"
            if verbose:
                print "*** Longitude not retreived"
        try: # latitude
            latitude = data['latitude']
            if verbose:
                print "--- Latitude: %s" % latitude
        except KeyError:
            latitude = "na"
            if verbose:
                print "*** Latitude not retreived"
        try: # country code
            countryCode = data['country_code']
            if verbose:
                print "--- Country code: %s" % countryCode
        except KeyError:
            countryCode = "na"
            if verbose:
                print "*** Country code not retreived"
        try: # 3-letter country code
            countryCode3 = data['country_code3']
            if verbose:
                print "--- 3-letter country code: %s" % countryCode3
        except KeyError:
            countryCode3 = "na"
            if verbose:
                print "*** 3-letter country code not retreived"
        try: # country
            country = data['country']
            if verbose:
                print "--- Country: %s" % country
        except KeyError:
            country = "na"
            if verbose:
                print "*** Country not retreived"
        try: # ISP
            isp = data['isp']
            if verbose:
                print "--- ISP: %s" % isp
        except KeyError:
            isp = "na"
            if verbose:
                print "*** ISP not retreived"
        try: # continent code
            continentCode = data['continent_code']
            if verbose:
                print "--- Continent code: %s" % continentCode
        except KeyError:
            continentCode = "na"
            if verbose:
                print "*** Continent code not retreived"
        try: # city
            city = data['city']
            if verbose:
                print "--- City: %s" % city
        except KeyError:
            city = "na"
            if verbose:
                print "*** City not retreived"
        try: # time zone
            timeZone = data['timezone']
            if verbose:
                print "--- Time zone: %s" % timeZone
        except KeyError:
            timeZone = "na"
            if verbose:
                print "*** Time zone not retreived"
        try: # region
            region = data['region']
            if verbose:
                print "--- Region: %s" % region
        except KeyError:
            region = "na"
            if verbose:
                print "*** Region not retreived"
        try: # region code
            regionCode = data['region_code']
            if verbose:
                print "--- Region code: %s" % regionCode
        except KeyError:
            regionCode = "na"
            if verbose:
                print "*** Region code not retreived"
        try: # offset
            offset = data['offset']
            if verbose:
                print "--- Offset: %s" % offset
        except KeyError:
            offset = "na"
            if verbose:
                print "*** Offset not retreived"
        try: # area code
            areaCode = data['area_code']
            if verbose:
                print "--- Area code: %s" % areaCode
        except KeyError:
            areaCode = "na"
            if verbose:
                print "*** Area code not retreived"
        try: # postal code
            postalCode = data['postal_code']
            if verbose:
                print "--- postal code: %s" % postalCode
        except KeyError:
            postalCode = "na"
            if verbose:
                print "*** Postal code not retreived"
        try: # postal code
            dmaCode = data['dma_code']
            if verbose:
                print "--- postal code: %s" % dmaCode
        except KeyError:
            dmaCode = "na"
            if verbose:
                print "*** DMA code not retreived"
        try: # asn
            asn = data['asn']
            if verbose:
                print "--- postal code: %s" % asn
        except KeyError:
            asn = "na"
            if verbose:
                print "*** ASN not retreived"
                
    else:
        if verbose:
            print "*** Could not get a response"        

    ipInfo = {'longitude': longitude, 'latitude': latitude, 'countryCode': countryCode,
              'city': city, 'country': country, 'regionCode': regionCode, 'region': region,
              'geoSource': geoSource,'offset': offset, 'timeZone': timeZone,
              'countryCode3': countryCode3, 'isp': isp, 'continentCode': continentCode,
              'areaCode': areaCode, 'postalCode': postalCode, 'dmaCode': dmaCode,
              'asn': asn}
    
    return ipInfo

def freegeoipLookup(ip, verbose):
    response = ""
    countryCode = "na"
    country = "na"
    regionCode = "na"
    region = "na"
    city = "na"
    zipCode = "na"
    latitude = "na"
    longitude = "na"
    metroCode = "na"
    areaCode = "na"
    geoSource = "freegeoip.net"
    
    try:
        response = urllib2.urlopen("%s%s" % (freegeoipAPI, ip), timeout = timeOut).read() # get xml from freegeoip
    except urllib2.URLError, e:
        if verbose:
            print "*** There was an error: %r" % e
        
    if response:
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
                zipCode = xmlChild.text
                if verbose:
                    print "--- Zip code: %s" % zipCode
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
        else:
            if verbose:
                print "Could not get info"
    
    ipInfo = {'longitude': longitude, 'latitude': latitude, 'countryCode': countryCode,
              'city': city, 'country': country, 'regionCode': regionCode, 'region': region,
              'geoSource': geoSource, 'zipCode': zipCode,
              'metroCode': metroCode, 'areaCode': areaCode}
    
    return ipInfo

def logSql(log, ipInfo, verbose): # create sql for the log
    name, protocol, port, ip, event = log
    sql = (
        "INSERT INTO %s"
        " (`name`, `protocol`, `port`, `ip`, `event`, `longitude`, `latitude`,"
        "`countryCode`, `city`, `country`, `regionCode`,"
        "`region`, `geoSource`)"
        " VALUES"
        " ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
        % (tableName, name, protocol, port, ip, event, ipInfo['longitude'], ipInfo['latitude'],
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
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            onError(4, "*** Something is wrong with your user name or password\n    Have you run with argument '--setupdb' yet?")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
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
    if ipInfo.has_key('continentCode'):
        print "--- Continent code: %s" % ipInfo['continentCode']
    if ipInfo.has_key('countryCode'):
        print "--- Country code: %s" % ipInfo['countryCode']
    if ipInfo.has_key('countryCode3'):
        print "--- 3-letter country code: %s" % ipInfo['countryCode3']
    if ipInfo.has_key('country'):
        print "--- Country: %s" % ipInfo['country']
    if ipInfo.has_key('regionCode'):
        print "--- Region code: %s" % ipInfo['regionCode']
    if ipInfo.has_key('region'):
        print "--- Region: %s" % ipInfo['region']
    if ipInfo.has_key('city'):
        print "--- City: %s" % ipInfo['city']
    if ipInfo.has_key('latitude'):
        print "--- Latitude: %s" % ipInfo['latitude']
    if ipInfo.has_key('longitude'):
        print "--- Longitude: %s" % ipInfo['longitude']
    if ipInfo.has_key('isp'):
        print "--- ISP: %s" % ipInfo['isp']
    if ipInfo.has_key('timeZone'):
        print "--- Time Zone: %s" % ipInfo['timeZone']
    if ipInfo.has_key('offset'):
        print "--- Offset: %s" % ipInfo['offset']
    if ipInfo.has_key('zipCode'):
        print "--- Zip code: %s" % ipInfo['zipCode']
    if  ipInfo.has_key('metroCode'):
        print "--- Metro code: %s" % ipInfo['metroCode']
    if ipInfo.has_key('areaCode'):
        print "--- Area code: %s" % ipInfo['areaCode']
    if ipInfo.has_key('postalCode'):
        print "--- Postal code: %s" % ipInfo['postalCode']
    if ipInfo.has_key('dmaCode'):
        print "--- DMA code: %s" % ipInfo['dmaCode']
    if ipInfo.has_key('asn'):
        print "--- ASN: %s" % ipInfo['asn']            
    if ipInfo.has_key('geoSource'):
        print "--- Geo source: %s" % ipInfo['geoSource']