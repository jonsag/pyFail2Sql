#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from dbcomm import *

import socket

def showStatistics(extendedStats, verbose):
    stat = []
    statCount = 0
    
    cnx = connect(dbName, verbose)  # connect to database
    print "Statistics:\n"

    cursor = cnx.cursor()  # create cursor
        
    fieldList = (["ip", "IP"], ["country", "Country"], ["name", "Service"], ["isp", "ISP"])
        
    for field, text in fieldList:
        temp = []
        timesBannedText = "times banned"
        sql = (
               "SELECT %s, COUNT(*) AS `times` FROM %s GROUP BY %s ORDER BY `times` DESC"
               % (field, logTableName, field)
               )            
        cursor = executeSql(cursor, sql, verbose)
        result = cursor.fetchall()
        
        maxText = len(text)  # find how we will print this
        maxCount = 0
        for field, count in result:
            maxText = max(maxText, len(field))
            maxCount = max(maxCount, len(str(count)))
        maxText = maxText + spacing
        maxCount = maxCount + spacing
        
        print "%-*s %*s" % (maxText, text, maxCount, timesBannedText)
        print "-" * scores
 
        for field, count in result:
            if count == 1:
                word = "time"
            else:
                word = "times"
            print "%-*s %s %s" % (maxText, field, count, word)
            temp.append(field)
        print
        stat.append(temp)
        
    if extendedStats:
        print "Extended statistics:\n"
        for searchField, text in fieldList:
            for searchTerm in stat[statCount]:
                showExtendedStats(searchField, text, searchTerm, verbose)
            statCount += 1
        
    cursor.close()
    disconnect(cnx, verbose)  # disconnect from database
    
def showExtendedStats(searchField, text, searchTerm, verbose):
    timeText = "Time"
    ipText = "IP"
    cityText = "City"
    regionText = "Region"
    countryText = "Country"
    ispText = "ISP"
    
    cnx = connect(dbName, verbose)  # connect to database
    print "Statistics on %s %s:" % (text, searchTerm)
    print "-" * scores
    
    cursor = cnx.cursor()  # create cursor
    
    sql = (
           "SELECT %s, COUNT(*) FROM %s WHERE %s = '%s'"
           % (searchField, logTableName, searchField, searchTerm)
           )
    
    cursor = executeSql(cursor, sql, verbose)
    result = cursor.fetchall()
    
    for field, count in result:
        if count > 0:
            if count == 1:
                word = "time"
            else:
                word = "times"
            print "Banned %s %s:" % (count, word)
            # print "-" * (scores / 2)
            
            sql = "SELECT `timeStamp`, `ip`, `city`, `region`, `country`, `countryCode`, `isp` FROM %s WHERE %s = '%s'" % (logTableName, searchField, searchTerm)
            cursor = executeSql(cursor, sql, verbose)
            result = cursor.fetchall()
            
            maxTimeStamp = len(timeText)
            maxIp = len(ipText)
            maxCity = len(cityText)
            maxRegion = len(regionText)
            maxCountry = len(countryText)
            maxIsp = len(ispText)
            for timeStamp, ip, city, region, country, countryCode, isp in result:
                maxTimeStamp = max(maxTimeStamp, len(str(timeStamp)))
                maxIp = max(maxIp, len(ip))
                maxCity = max(maxCity, len(city))
                maxRegion = max(maxRegion, len(region))
                maxCountry = max(maxCountry, len(country))
                maxIsp = max(maxIsp, len(isp))
            maxTimeStamp = maxTimeStamp + spacing
            maxIp = maxIp + spacing
            maxCity = maxCity + spacing
            maxRegion = maxRegion + spacing
            maxCountry = maxCountry + spacing
            maxIsp = maxIsp + spacing
                
            print (
                   "%-*s"
                   "%-*s"
                   "%-*s"
                   "%-*s"
                   "%-*s"
                   "%-*s"
                   % (maxTimeStamp, timeText,
                      maxIp, ipText,
                      maxCity, cityText,
                      maxRegion, regionText,
                      maxCountry, countryText,
                      maxIsp, ispText)
                   )
            
            for timeStamp, ip, city, region, country, countryCode, isp in result:
                print ("%-*s"
                       "%-*s"
                       "%-*s"
                       "%-*s"
                       "%-*s"
                       "%-*s"
                       % (maxTimeStamp, timeStamp,
                          maxIp, ip,
                          maxCity, city,
                          maxRegion, region,
                          maxCountry, country,
                          maxIsp, isp)
                          )
            print
        else:
            print "%s does not occur in database" % field
            print
            
    cursor.close()
    disconnect(cnx, verbose)  # disconnect from database
    
