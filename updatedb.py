#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from dbcomm import *
from geolookup import *

def addData(idNo, ipInfo, cnx, cursor, verbose):
    sql = (
           "UPDATE %s SET countryCode='%s', "
           "city='%s', region='%s', country='%s', "
           "regionCode='%s', geoSource='%s' ",
           "longitude='%s', latitude='%s' "
           "WHERE no='%s'"
           % (tableName, ipInfo['countryCode'],
           ipInfo['city'], ipInfo['region'], ipInfo['country'],
           ipInfo['regionCode'], ipInfo['geoSource'],
           ipInfo['longitude'], ipInfo['latitude'],
           idNo)
           )
        
    cursor = executeSql(cursor, sql, verbose)
    
    cnx.commit() # commit changes
    

def findEmpty(verbose):
    posts = []
    
    cnx = connect(dbName, verbose)
    if cnx:
        cursor = cnx.cursor() # create cursor
    
    sql = (
           "SELECT no, ip, city, region, country FROM %s WHERE "
           "`city` = '%s' OR"
           "`region` = '%s' OR "
           "`country` = '%s' OR "
           "`country` = '%s' OR "
           "`regionCode` = '%s' OR "
           "`longitude` = '%s' OR "
           "`latitude` = '%s'"
             % (tableName, 
                noDataText,
                noDataText,
                noDataText,
                noDataText,
                noDataText,
                noDataText,
                noDataText)
             )
    
    if verbose:
        print "+++ sql = %s" % sql
        
    cursor = executeSql(cursor, sql, verbose)
    
    for idNo, ip, city, region, country in cursor:
        posts.append([idNo, ip, city, region, country])
    
    if posts:
        if verbose:
            print "--- These posts does not have adequate geo data:"
        for idNo, ip, city, region, country in posts:
            if verbose:
                print "id: %s\tIP: %s\t%s, %s, %s" % (idNo, ip, city, region, country)
                print "-" * scores
            ipInfo = lookupIP(ip, verbose)
            if verbose:
                print "--- Updating post..."
            addData(idNo, ipInfo, cnx, cursor, verbose)
    else:
        if verbose:
            print "--- All posts have geo data"
        