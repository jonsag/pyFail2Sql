#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from dbcomm import *

import xml.etree.ElementTree as ET

import urllib2, json

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
            ipInfo = {'longitude': noDataText, 'latitude': noDataText, 'countryCode': noDataText,
                  'city': noDataText, 'country': noDataText, 'regionCode': noDataText, 'region': noDataText,
                  'geoSource': noDataText,'offset': noDataText, 'timeZone': noDataText,
                  'countryCode3': noDataText, 'isp': noDataText,'postalCode': noDataText,
                  'metroCode': noDataText, 'areaCode': noDataText}
        
    return ipInfo

def telizeLookup(response, verbose):
    longitude = noDataText
    latitude = noDataText
    countryCode = noDataText
    countryCode3 = noDataText
    country = noDataText
    isp = noDataText
    continentCode = noDataText
    city = noDataText
    timeZone = noDataText
    region = noDataText
    regionCode = noDataText
    offset = noDataText
    areaCode = noDataText
    postalCode = noDataText
    dmaCode = noDataText
    asn = noDataText
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
    countryCode = noDataText
    country = noDataText
    regionCode = noDataText
    region = noDataText
    city = noDataText
    postalCode = noDataText
    latitude = noDataText
    longitude = noDataText
    metroCode = noDataText
    areaCode = noDataText
    isp = noDataText
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
              'metroCode': metroCode, 'areaCode': areaCode, 'isp': isp}
    
    return ipInfo
