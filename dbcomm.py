#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from misc import *

import mysql.connector

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
        print "--- Connecting to db server %s as user %s, using database %s..." % (dbHost, dbUser, dbName)
        
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
        
        if verbose:
            print "--- Committing changes..."    
        cnx.commit() # commit changes
        if verbose:
            print "    OK"
        cursor.close() 
    disconnect(cnx, verbose) # disconnect from database
    return result

def executeSql(cursor, sql, verbose):
    if verbose:
        print "--- Querying database..."
        print "+++ sql = %s" % sql
    try: # get answer
        cursor.execute(sql)
    except mysql.connector.Error as err:
        onError(9, err.msg)
    else:
        if verbose:
            print "    OK"
    return cursor

        