#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# -------------------------------------------------------------------------------- #
# Description                                                                      #
# -------------------------------------------------------------------------------- #
#                                                                                  #
# -------------------------------------------------------------------------------- #
# Example Usage:                                                                   #
#     ./list-region-information.py                                                 #
# -------------------------------------------------------------------------------- #


from __future__ import print_function

import json
import os
import re
import requests
import sys
from bs4 import BeautifulSoup
from prettytable import PrettyTable

# -------------------------------------------------------------------------------- #
# Information URLs                                                                 #
# -------------------------------------------------------------------------------- #
# The urls we use to gather the information.                                       #
# -------------------------------------------------------------------------------- #

region_mapping_url = "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.partial.html"
az_numbers_url = "https://aws.amazon.com/about-aws/global-infrastructure/regions_az/"


# -------------------------------------------------------------------------------- #
# Default Values                                                                   #
# -------------------------------------------------------------------------------- #
# A set of default values to be used but allow them to be              #
# -------------------------------------------------------------------------------- #

region_map_filename = 'region-map.json'
request_timeout = 5


# -------------------------------------------------------------------------------- #
# Main()                                                                           #
# -------------------------------------------------------------------------------- #
# This is the actual 'script' and the functions/sub routines are called in order.  #
# -------------------------------------------------------------------------------- #

def main(cmdline=None):
    contents = get_page_contents(region_mapping_url)
    region_map = process_region_map(contents)

    contents = get_page_contents(az_numbers_url)
    region_map = add_additional_information(region_map, contents)
    display_results(region_map)


# -------------------------------------------------------------------------------- #
# Get Page Content                                                                 #
# -------------------------------------------------------------------------------- #
# Pull the information from the Amazon regional table web page.                    #
# -------------------------------------------------------------------------------- #

def get_page_contents(url):
    r = requests.get(url, timeout=request_timeout)
    return r.content


# -------------------------------------------------------------------------------- #
# Process Region Map                                                               #
# -------------------------------------------------------------------------------- #
# Process the HTML pulled from th first page and process it to create the initial  #
# region map.                                                                      #
# -------------------------------------------------------------------------------- #

def process_region_map(contents):
    region_map = []

    soup = BeautifulSoup(contents, 'lxml')
    tables = soup.find_all('table')
    for table in tables:
        table_rows = table.find_all('tr')
        for tr in table_rows:
            table_cells = tr.find_all('td')
            if len(table_cells) > 0:
                az = table_cells[0].get_text().strip()
                fullname = table_cells[1].get_text().strip()
                fullname = fullname.replace('N.', 'North')
                fullname = fullname.replace('S.', 'South')
                fullname = fullname.replace('-Local', '')
                try:
                    country = re.search(r'\((.*?)\)', fullname).group(1)
                except AttributeError:
                    country = 'unknown'

                row = {'region': az, 'fullname': fullname, 'country': country}

                region_map.append(row)

    sorted_region_map = sorted(region_map, key=lambda k: k['region'])

    return sorted_region_map


# -------------------------------------------------------------------------------- #
# Add Additional Information                                                       #
# -------------------------------------------------------------------------------- #
# Process the HTML pulled from the second source and extract the additional info.  #
# -------------------------------------------------------------------------------- #

def add_additional_information(region_map, contents):
    soup = BeautifulSoup(contents, 'lxml')

    paragraphs = soup.find_all(lambda tag: tag.name == "p" and "Availability Zones" in tag.text)
    for p in paragraphs:
        fullname = None
        azs = 0
        launched = None

        text = p.get_text().strip()
        m = re.search(r'(.*? \(.*?\)) .*?Availability Zones: (.+?).*?Launched (.+)', text)
        if m is not None:
            fullname = m.group(1)
            azs = m.group(2)
            launched = m.group(3).partition(' ')[0]
        if fullname is not None:
            fullname = fullname.replace('Northern', 'North')
            try:
                country = re.search(r'\((.*?)\)', fullname).group(1)
            except AttributeError:
                country = 'unknown'
            index = next((index for (index, d) in enumerate(region_map) if d["country"].lower() == country.lower()), None)
            if index is not None:
                region_map[index].update({'azs': azs, 'launched': launched})

    return region_map


# -------------------------------------------------------------------------------- #
# Display Results                                                                  #
# -------------------------------------------------------------------------------- #
# Display the results of the lookup.                                               #
# -------------------------------------------------------------------------------- #

def display_results(results):
    table = PrettyTable()
    table.hrules = True
    table.field_names = ('Region', 'Fullname', 'Country', 'Availability Zones', 'Launched')

    #
    # Process each results
    #

    for region in results:
        row = (region['region'], region['fullname'], region['country'], region['azs'], region['launched'])
        table.add_row(row)

    print(table)


# -------------------------------------------------------------------------------- #
# Main() really this time                                                          #
# -------------------------------------------------------------------------------- #
# This runs when the application is run from the command it grabs sys.argv[1:]     #
# which is everything after the program name and passes it to main the return      #
# value from main is then used as the argument to sys.exit, which you can test for #
# in the shell. program exit codes are usually 0 for ok, and non-zero for          #
# something going wrong.                                                           #
# -------------------------------------------------------------------------------- #

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


# -------------------------------------------------------------------------------- #
# End of Script                                                                    #
# -------------------------------------------------------------------------------- #
# This is the end - nothing more to see here.                                      #
# -------------------------------------------------------------------------------- #
