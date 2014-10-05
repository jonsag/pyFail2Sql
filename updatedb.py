#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from dbcomm import *
from geolookup import *
from setupdb import columnExists

def addData(idNo, ipInfo, cnx, cursor, verbose):
    
    sql = (
           "UPDATE %s SET countryCode='%s', "
           "city='%s', region='%s', country='%s', "
           "regionCode='%s', geoSource='%s', "
           "longitude='%s', latitude='%s', "
           "isp='%s' "
           "WHERE no='%s'"
           % (tableName, ipInfo['countryCode'],
           ipInfo['city'], ipInfo['region'], ipInfo['country'],
           ipInfo['regionCode'], ipInfo['geoSource'],
           ipInfo['longitude'], ipInfo['latitude'],
           ipInfo['isp'],
           idNo)
           )
        
    cursor = executeSql(cursor, sql, verbose)
    
    cnx.commit() # commit changes
    
def fillColumn(column, cnx, cursor, verbose):
    posts = []
    
    if verbose:
        print "--- Checking if column '%s' exists..." % column
    
    columnAlreadyExists, typeCorrect = columnExists(tableName, column, "na", cursor, verbose)
    
    if columnAlreadyExists:
        if verbose:
            print "--- Column exists"
            
    else:
        if verbose:
            print "*** Column does not exist"
            
    sql = (
           "SELECT no, ip, city, region, country, isp FROM %s WHERE "
           "`%s` = '%s' OR `%s` IS NULL"
           % (tableName,
              column, noDataText, column)
            )
    
    cursor = executeSql(cursor, sql, verbose)
    
    for idNo, ip, city, region, country, isp in cursor:
            posts.append([idNo, ip, city, region, country, isp])
        
    if posts:
        if verbose:
            print "--- These posts does not have adequate ISP data:"
        for idNo, ip, city, region, country, isp in posts:
            if verbose:
                print "id: %s\tIP: %s\t%s, %s, %s\t%s" % (idNo, ip, city, region, country, isp)
                print "-" * scores
            ipInfo = lookupIP(ip, verbose)
            if verbose:
                print "--- Updating post..."
            addData(idNo, ipInfo, cnx, cursor, verbose)
    else:
        if verbose:
            print "--- All posts have data"
            
            
def findEmpty(column, verbose):
    posts = []
    
    cnx = connect(dbName, verbose)
    cursor = cnx.cursor() # create cursor
    
    if not column: # search all columns   
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
    else: # search only given column
        fillColumn(column, cnx, cursor, verbose)
        
    cursor.close()
    disconnect(cnx, verbose)
        