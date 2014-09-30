#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from functions import *

from getpass import getpass

import mysql.connector

def create_database(cursor):
    try:
        cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(dbName))
    except mysql.connector.Error as err:
        onError(7, "Failed creating database: {}".format(err))
    
def setupDB(rootUser, rootPass, verbose): # setup the database with tables and users
    tables = {} # tables that will be created
    tables[tableName] = ("CREATE TABLE %s ("
                         " `no` int(11) NOT NULL AUTO_INCREMENT,"
                         " PRIMARY KEY (`no`)"
                         ") ENGINE=InnoDB" % tableName)
    
    columns = [] # columns that will be added
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
        
        columns.append({'table': tableName, 'column': column,
                        'sql': "ALTER TABLE %s ADD `%s` %s" % (tableName, column, value)})
    
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
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            onError(4, "Something is wrong with your user name or password\n    Have you run with argument '--setupdb' yet?")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            onError(5, "Database does not exists\n    Run again with argument '--setupdb'")
        else:
            onError(6, err)
        
    if verbose:
        print "    OK"
        print "--- Creating database %s with all tables we need..." % dbName
        
    cursor = cnx.cursor() # construct cursor to use
    
    dbExists = False
    sql = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '%s'" % dbName
    if verbose:
        print "--- Checking if database already exists"
        print "+++ sql = %s" % sql
    try: # check if database already exists
        cursor.execute(sql)
    except mysql.connector.Error as err:
        onError(10, "Failed checking if database exists: {}".format(err))
    result = cursor.fetchall()
    for line in result:
        if line[0] == dbName:
            dbExists = True
            if verbose:
                print "--- Database exists"
                
    if not dbExists:
        if verbose:
            print "--- Database does not exist. Creating it..."
        sql = "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(dbName)
        if verbose:
            print "+++ sql = %s" % sql
        try: # create table
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
        if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            cnx.database = dbName
        else:
            onError(8, err)
    
    if verbose:
        print "    OK"
        print "--- Creating tables..."
    
    for newTable, createTableSql in tables.iteritems(): # create the tables one by one
        tableExists = False
        sql = "SHOW TABLES LIKE '%s'" % newTable
        if verbose:
            print "--- Checking if table %s already exists" % newTable
            print "+++ sql = %s" % sql
        try: # check if table already exists
            cursor.execute(sql)
        except mysql.connector.Error as err:
            onError(10, "Failed checking if table exists: {}".format(err))
        result = cursor.fetchall()
        for line in result:
            if line[0] == newTable:
                tableExists = True
                if verbose:
                    print "--- Table exists"
        if not tableExists:
            print "--- Creating %s..." % newTable
            if verbose:
                print "+++ sql = %s" % createTableSql
            try:
                #print("Creating table {}: ".format(newTable), end='')
                cursor.execute(createTableSql)
            except mysql.connector.Error as err:
                if err.errno == mysql.connector.errorcode.ER_TABLE_EXISTS_ERROR:
                    onError(11, "Table %s already exists" % newTable)
                else:
                    onError(9, err.msg)
            else:
                if verbose:
                    print "    OK"
                    print "--- Creating user %s..." % dbUser
         
    userExists = False
    sql = "show grants for '%s'@'localhost'" % dbUser
    if verbose:
        print "--- Checking if user %s already exists" % dbUser
        print "+++ sql = %s" % sql
    try: # check if user already exists
        cursor.execute(sql)
    except mysql.connector.Error as err:
        onError(10, "Failed checking if user exists: {}".format(err))
    result = cursor.fetchall()
    if result[0][0].startswith("GRANT USAGE ON *.*") and result[1][0].startswith("GRANT ALL PRIVILEGES ON `pyfail2sql`"):
        userExists = True
        if verbose:
            print "--- User exists"
    if not userExists:
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
    
    