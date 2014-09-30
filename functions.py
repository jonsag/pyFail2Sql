#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, sys, os, urllib2
import mysql.connector, json

import xml.etree.ElementTree as ET

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
        