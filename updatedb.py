#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from dbcomm import *
from geolookup import *

def findEmpty(verbose):
    posts = []
    
    cnx = connect(dbName, verbose)
    if cnx:
        cursor = cnx.cursor() # create cursor
    
    sql = "SELECT no, ip, city, region, country FROM %s WHERE `city` = '%s'" % (tableName, noDataText)
    if verbose:
        print "+++ sql = %s" % sql
        
    cursor = executeSql(cursor, sql, verbose)
    
    for idNo, ip, city, region, country in cursor:
        posts.append([idNo, ip, city, region, country])
    
    if posts:
        if verbose:
            print "--- These posts does not have adequate geo data:"
        for idNo, ip, city, region, country in posts:
            print "id: %s\tIP: %s\t%s, %s, %s" % (idNo, ip, city, region, country)
            ipInfo = lookupIP(ip, verbose)
    else:
       print "--- All posts have geo data"
        