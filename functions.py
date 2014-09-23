#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, sys, os, urllib, datetime
import mysql.connector

import xml.etree.ElementTree as ET

from mysql.connector import errorcode

from getpass import getpass
from bsddb.test.test_all import verbose

##### read config file
config = ConfigParser.ConfigParser()
config.read("%s/config.ini" % os.path.dirname(os.path.realpath(__file__))) # read config file

dbHost = config.get('mysql','dbHost')
dbPort = int(config.get('mysql','dbPort'))

dbName = config.get('mysql','dbName')
tableName = config.get('mysql','tableName')

dbUser = config.get('mysql','dbUser')
dbPass = config.get('mysql','dbPass')

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
    elif errorCode in (4, 5, 6, 8):
        print "    %s" % extra
        sys.exit(errorCode)
    elif errorCode == 7:
        print "    %s" % extra
    elif errorCode == 9:
        print "    %s" % extra

##### some help
def usage(exitCode):
    print "\nUsage:"
    print "----------------------------------------"
    print "%s --setupdb [-v]" % sys.argv[0]
    print "      Add required databases, tables and users"
    print "        Options: 'v'erbose output"
    print "    OR"
    print "%s -w -n <name> -q <protocol> -p <port> -i <ip> [-v]" % sys.argv[0]
    print "      Write log to database"
    print "        Arguments: 'n'ame of service"
    print "                 'q' protocol, tcp, udp etc."
    print "                 'p'ort"
    print "                 'i'p number"
    print "                 'e'vent causing this log"
    print "        Options: 'v'erbose output"
    print "    OR"
    print "%s -h" % sys.argv[0]
    print "      Prints this"
    sys.exit(exitCode)
    
def setupDB(verbose): # setup the database with tables and users
    if verbose:
        print "--- Setting up database"
        
    dbUser = raw_input("User with rights to create database: ") # get user
    dbPass = getpass("Password: ") # get user's passsword
    
    if verbose:
        print "Username: %s\nPassword: %s" % (dbUser, dbPass)
        print "--- Connecting to db server %s..." % dbHost
        
    try: # concect to database
        cnx = mysql.connector.connect(user = dbUser, password = dbPass, host = dbHost, port = dbPort)
    except mysql.connector.Error as err: # get errors
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            onError(4, "Something is wrong with your user name or password\n    Have you run with argument '--setupdb' yet?")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            onError(5, "Database does not exists\n    Run again with argument '--setupdb'")
        else:
            onError(6, err)
        
    if verbose:
        print "    OK"
        print "--- Creating database %s..." % dbName
        
    cursor = cnx.cursor() # construct cursor to use
    
    tables = {} # these are the tables that will be created
    tables[tableName] = (
    "CREATE TABLE %s ("
    "  `no` int(11) NOT NULL AUTO_INCREMENT,"
    "  `timeStamp` TIMESTAMP,"
    "  `name` varchar(10),"
    "  `protocol` varchar(3),"
    "  `port` int(5),"
    "  `ip` varchar(15),"
    "  `event` varchar(15),"
    "  `longitude` varchar(10),"
    "  `latitude` varchar(10),"
    "  `countryCode` varchar(2),"
    "  `city` varchar(20),"
    "  `country` varchar(20),"
    "  `regionCode` varchar(3),"
    "  `region` varchar(20),"
    "  PRIMARY KEY (`no`)"
    ") ENGINE=InnoDB" % tableName)
    
    sql = "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(dbName) # the sql for creating tables
    if verbose:
        print "+++ sql = %s" % sql
    try: # execute the sql
        cursor.execute(sql)
    except mysql.connector.Error as err:
        onError(7, "Failed creating database: {}".format(err))
        
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
                print "  already exists."
            else:
                onError(9, err.msg)
        else:
            if verbose:
                print "    OK"
                print "--- Creating user %s..." % dbUser

    dbUser = config.get('mysql','dbUser') # get the normal user
    dbPass = config.get('mysql','dbPass') # get the normal user's password
            
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
    
def lookupIP(ip, verbose): # get geographical data for ip
    countryCode = ""
    country = ""
    regionCode = ""
    region = ""
    city = ""
    zipCode = ""
    latitude = ""
    longitude = ""
    metroCode = ""
    areaCode = ""
    
    response = urllib.urlopen("http://freegeoip.net/xml/%s" % ip).read() # get xml from freegeoip
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
    
    ipInfo = longitude, latitude, countryCode, city, country, regionCode, region
    return ipInfo

def logSql(log, ipInfo, verbose): # create sql for the log
    name, protocol, port, ip, event = log
    longitude, latitude, countryCode, city, country, regionCode, region = ipInfo
    sql = (
        "INSERT INTO %s"
        " (`name`, `protocol`, `port`, `ip`, `event`, `longitude`, `latitude`, `countryCode`, `city`, `country`, `regionCode`, `region`)"
        " VALUES"
        " ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
        % (tableName, name, protocol, port, ip, event, longitude, latitude, countryCode, city, country, regionCode, region))
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

def showStatistics(verbose):
    cnx =connect(dbName, verbose) # connect to database
    print "Statistics:\n"

    cursor = cnx.cursor() # create cursor
        
    fieldList = (["ip", "IP"], ["country", "Country"], ["name", "Service"])
        
    for field, text in fieldList:
        print "%s:" % text
        sql = "SELECT %s, COUNT(*) FROM %s GROUP BY %s" % (field, tableName, field)            
        cursor = executeSql(cursor, sql, verbose)
        for field, count in cursor:
            if count == 1:
                word = "time"
            else:
                word = "times"
            print "%s\tbanned: %s %s" % (field, count, word)
        print
    
    cursor.close()
    disconnect(cnx, verbose) # disconnect from database

def showIpStats(ip, verbose):
    cnx =connect(dbName, verbose) # connect to database
    print "Statistics on %s:\n" % ip
    
    cursor = cnx.cursor() # create cursor
        
    sql = "SELECT ip, COUNT(*) FROM %s WHERE ip = '%s'" % (tableName, ip)
    cursor = executeSql(cursor, sql, verbose)
    for field, count in cursor:
        if count > 0:
            if count == 1:
                word = "time"
            else:
                word = "times"
            print "banned: %s %s" % (count, word)
            
            sql = "SELECT `timeStamp`, `city`, `country`, `countryCode` FROM %s WHERE ip = '%s'" % (tableName, ip)
            cursor = executeSql(cursor, sql, verbose)
            for timeStamp, city, country, countryCode in cursor:
                print "%s\t%s, %s %s" % (timeStamp, city, country, countryCode)

        else:
            print "IP does not occur in database"

    cursor.close()
    disconnect(cnx, verbose) # disconnect from database
    
def showCountryStats(country, verbose):
    cnx =connect(dbName, verbose) # connect to database
    print "Statistics on %s:\n" % country
    
    cursor = cnx.cursor() # create cursor
    
    sql = "SELECT country, COUNT(*) FROM %s WHERE country = '%s'" % (tableName, country)
    cursor = executeSql(cursor, sql, verbose)
    for field, count in cursor:
        if count > 0:
            if count == 1:
                word = "time"
            else:
                word = "times"
            print "banned: %s %s" % (count, word)
            
            sql = "SELECT `timeStamp`, `ip`, `city`, `countryCode` FROM %s WHERE country = '%s'" % (tableName, country)
            cursor = executeSql(cursor, sql, verbose)
            for timeStamp, ip, city, countryCode in cursor:
                print "%s\t%s, %s, %s" % (timeStamp, ip, city, country)
            
        else:
            print "Country does not occur in database"
            
    cursor.close()
    disconnect(cnx, verbose) # disconnect from database
    