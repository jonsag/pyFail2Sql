#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from misc import *
from dbcomm import *

from getpass import getpass

import mysql.connector

def create_database(cursor):
    try:
        cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(dbName))
    except mysql.connector.Error as err:
        onError(7, "Failed creating database: {}".format(err))
    
def tablesConfig(verbose):
    tables = {} # tables that will be created
    if verbose:
        print "--- Reading table config..."
        
    tables[tableName] = ("CREATE TABLE %s ("
                         " `no` int(11) NOT NULL AUTO_INCREMENT,"
                         " PRIMARY KEY (`no`)"
                         ") ENGINE=InnoDB" % tableName)
    return tables
    
def columnsConfig(verbose):
    columns = [] # columns that will be added
    
    if verbose:
        print "--- Reading columns config..."
    
    table1 = tableName   
    set1 = [["timeStamp", "timestamp"],
            ["name", "varchar(10)"],
            ["protocol", "varchar(3)"],
            ["port", "int(5)"],
            ["ip", "varchar(15)"],
            ["event", "varchar(15)"],
            ["longitude", "varchar(10)"],
            ["latitude", "varchar(10)"],
            ["countryCode", "varchar(2)"],
            ["city", "varchar(20)"],
            ["region", "varchar(20)"],
            ["country", "varchar(20)"],
            ["regionCode", "varchar(3)"],
            ["geoSource", "varchar(30)"]]
    
    for column, value in set1:
        columns.append({'table': table1, 'column': column, 'type': value})
        
    return columns
        
def connectToDb(rootUser, rootPass, dBase, verbose):
    if not rootUser:
        rootUser = raw_input("User with rights to create database: ") # get user
    if not rootPass:
        rootPass = getpass("Password: ") # get user's passsword
    
    if verbose:
        print "--- Username: %s\n--- Password: %s" % (rootUser, rootPass)

    if not dBase:
        if verbose:
            print "--- Connecting to db server %s as user %s..." % (dbHost, rootUser)
        try: # connect to server, no database
            cnx = mysql.connector.connect(user = rootUser, password = rootPass, host = dbHost, port = dbPort)
            if verbose:
                print "    OK"
        except mysql.connector.Error as err: # get errors
            if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                onError(4, "Something is wrong with your user name or password\n    Have you run with argument '--setupdb' yet?")
            elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                onError(5, "Database does not exists\n    Run again with argument '--setupdb'")
            else:
                onError(6, err)
    elif dBase:
        try: # connect to server, set database
            cnx = mysql.connector.connect(user = rootUser, password = rootPass, host = dbHost, port = dbPort, database=dBase)
            if verbose:
                print "    OK"
        except mysql.connector.Error as err: # get errors
            if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                onError(4, "Something is wrong with your user name or password\n    Have you run with argument '--setupdb' yet?")
            elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                onError(5, "Database does not exists\n    Run again with argument '--setupdb'")
            else:
                onError(6, err)
                
    return cnx, rootUser, rootPass

def createDatabase(cursor, verbose):
    dbExists = False
    if verbose:
        print "--- Creating database %s with all tables we need..." % dbName
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
            if verbose:
                print "    OK"
        except mysql.connector.Error as err:
            onError(7, "Failed creating database: {}".format(err))
            
def useDatabase(cnx, cursor, verbose):
    if verbose:
        print "--- Setting database..."        
    try:
        cnx.database = dbName
        if verbose:
            print "    OK"
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            cnx.database = dbName
        else:
            onError(8, err)
            
    return cnx, cursor

def createTables(cursor, verbose):
    tables = tablesConfig(verbose)
    
    if verbose:
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
                    
def createColumns(cursor, verbose):
    columns = columnsConfig(verbose)
    
    if verbose:
        print "--- Creating columns..."
        
    for column in columns:
        columnExists = False
        typeCorrect = False
        if verbose:
            print "--- Adding column %s to table %s..." % (column['column'], column['table'])
            print "--- Checking if column exists..."
        
        sql = "SHOW COLUMNS FROM `%s` LIKE '%s'" % (column['table'], column['column'])
        if verbose:
            print "+++ sql = %s" % sql
        try: # checking if column exists
            cursor.execute(sql)
            if verbose:
                print "    OK"
        except mysql.connector.Error as err:
            onError(10, "Error: {}".format(err))
        result = cursor
        for answer in result:
            if answer[0] == column['column']:
                columnExists = True
                if answer[1] == column['type']:
                    typeCorrect = True 
                
        if columnExists: # column exists
            if verbose:
                print "--- Column '%s' exists" % column['column']
            if typeCorrect:
                if verbose:
                    print "--- Type '%s' is correct" % column['type']
            else:
                sql = "ALTER TABLE %s MODIFY `%s` %s" % (column['table'], column['column'], column['type'])
                if verbose:
                    print "--- Type should be '%s'" % column['type']
                    print "--- Setting type..."
                    print "+++ sql = %s" % sql
                try:
                    cursor.execute(sql)
                    if verbose:
                        print "    OK"
                except mysql.connector.Error as err:
                    onError(10, "Error: {}".format(err))
        else: # column doews not exist
            sql = "ALTER TABLE %s ADD `%s` %s" % (column['table'], column['column'], column['type'])
            if verbose:
                print "--- Column '%s' does not exist" % column['column']
                print "--- Creating column '%s'..." % column['column']
                print "+++ sql = %s" % sql
            try:
                cursor.execute(sql)
                if verbose:
                    print "    OK"
            except mysql.connector.Error as err:
                onError(10, "Error: {}".format(err))
                    
def createUser(cursor, verbose):
    userExists = False
    if verbose:
        print "--- Creating user %s..." % dbUser
         
    sql = "SHOW GRANTS FOR '%s'@'localhost'" % dbUser
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
    
def setupDB(rootUser, rootPass, verbose): # setup the database with tables and users
    if verbose:
        print "--- Setting up database"

    cnx, rootUser, rootPass = connectToDb(rootUser, rootPass, False, verbose) # get credentials and connect to db server
    cursor = cnx.cursor() # construct cursor to use

    createDatabase(cursor, verbose) # check if database already exists, if not, create it

    createUser(cursor, verbose) # check if user exists, if not, create
    
    cursor.close()
    disconnect(cnx, verbose) # disconnect from server

    #cnx, cursor = useDatabase(cnx, cursor, verbose) # use the new database
    cnx, rootUser, rootPass = connectToDb(rootUser, rootPass, dbName, verbose) # connect to server, set database to use
    cursor = cnx.cursor() # create cursor
    
    createTables(cursor, verbose) # check if tables exists, if not, create them
    
    createColumns(cursor, verbose)

    cursor.close()
    disconnect(cnx, verbose) # disconnect from database
  
    if verbose:
        print "--- Trying to connect to server as normal user..."
    cnx = connect(dbName, verbose) # connect to database as normal user
    if cnx:
        if verbose:
            print "--- Connected as normal user"
    else:
        if verbose:
            print "*** Failed to connect"