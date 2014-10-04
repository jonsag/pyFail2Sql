#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from dbcomm import *

import socket

def showStatistics(extendedStats, verbose):
    stat = []
    statCount = 0
    
    cnx =connect(dbName, verbose) # connect to database
    print "Statistics:"
    print "------------------------------------------------------------------"

    cursor = cnx.cursor() # create cursor
        
    fieldList = (["ip", "IP"], ["country", "Country"], ["name", "Service"], ["isp", "ISP"])
        
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
            
            sql = "SELECT `timeStamp`, `ip`, `city`, `region`, `country`, `countryCode`, `isp` FROM %s WHERE %s = '%s'" % (tableName, searchField, searchTerm)
            cursor = executeSql(cursor, sql, verbose)
            for timeStamp, ip, city, region, country, countryCode, isp in cursor:
                print "%s\t%s\t%s, %s, %s\t%s" % (timeStamp, ip, city, region, country, isp)
            print
        else:
            print "%s does not occur in database" % field
            print
            
    cursor.close()
    disconnect(cnx, verbose) # disconnect from database
    