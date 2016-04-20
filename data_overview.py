import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import operator

import shared_code

OSMFILE = shared_code.OSMFILE

# audit to see how many tags are in our data
def count_tags(filename):
    tags = {}
    for event, ele in ET.iterparse(filename):
        current_tag = ele.tag
        if current_tag not in tags:
            tags[current_tag] = 1
        else:
            tags[current_tag] += 1
    return tags

if False:
    pprint.pprint(count_tags(OSMFILE))


# data structure to show the unique users and the number of contributions they have made to the map
def unique_users(filename):
    users = {}
    i = 0
    for _, element in ET.iterparse(filename):
        if 'user' in element.attrib:
            current_user = element.attrib['user']
            if current_user in users:
                users[current_user] += 1
            else:
                users[current_user] = 1
    return users

if False:
    user_dict = unique_users(OSMFILE)
    print 'total users: {0}'.format(len(user_dict))
    print '\n\n'
    sorted_desc = sorted(user_dict.items(), key=operator.itemgetter(1), reverse=True)
    for key, value in sorted_desc:
        print u'{0}: {1}'.format(key, value)


problemchars = shared_code.problemchars
lower_colon = shared_code.lower_colon
lower = shared_code.lower


# sets the type of key based on if it is problem, lower case, lower case with a colon
def key_type(element, keys):
    if element.tag == "tag":
        # YOUR CODE HERE
        if 'k' in element.attrib:
            key = element.attrib['k']
            if problemchars.search(key):
                print key
                print element.attrib['v']
                keys['problemchars'] += 1
            elif lower.match(key) is not None:
                keys['lower'] += 1
            elif lower_colon.match(key) is not None:
                keys['lower_colon'] += 1
            else:
                keys['other'] += 1
    return keys


# fills the values for each key type
def audit_keys(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)
    return keys

if False:
    pprint.pprint(audit_keys(OSMFILE))


# inspect the data to see the type of key names on the nodes we are interested in
# found keys like amenity which will be useful to query
def get_unique_keys(filename):
    keys = set()
    for _, element in ET.iterparse(filename):
        if element.tag == "node" or element.tag == "way":
            for tag in element.iter("tag"):
                if 'k' in tag.attrib:
                    keys.add(tag.attrib['k'])
    return keys

if False:
    pprint.pprint(get_unique_keys(OSMFILE))


# zipcode exploration - there are multiple ways to represent zip codes in the OSM data
# including addr:zip, tiger:zip_left, tiger:zip_right and additional tiger:zip_direction_number
# tags as well. In addition, zip codes are not in a consistent format
def get_zip_codes(filename):
    zips = set()
    for _, element in ET.iterparse(filename):
        if element.tag == "node" or element.tag == "way":
            for tag in element.iter("tag"):
                if 'k' in tag.attrib and tag.attrib['k'] == "addr:postcode":
                    zips.add(tag.attrib['v'])
    return zips

if False:
    pprint.pprint(get_zip_codes(OSMFILE))

zip_code_re = shared_code.zip_code_re


# test regex pulls zip code first 5 digits only and ignores bad keys
def get_zip_codes_start_only(filename):
    zips = set()
    for _, element in ET.iterparse(filename):
        if element.tag == "node" or element.tag == "way":
            for tag in element.iter("tag"):
                if 'k' in tag.attrib and tag.attrib['k'] == "addr:postcode":
                    match = zip_code_re.match(tag.attrib['v'])
                    if match:
                        zips.add(match.group(1))
    return zips

if False:
    pprint.pprint(get_zip_codes_start_only(OSMFILE))


tiger_left = shared_code.tiger_left


# are there cases where tiger has a zip code but there is not address zip tag?
def inspect_nodes_with_tiger(filename):
    tiger_zip_tag_no_postal = 0
    for _, element in ET.iterparse(filename):
        if element.tag == "node" or element.tag == "way":
            has_tiger = False
            has_post_code = False
            for tag in element.iter("tag"):
                if 'k' in tag.attrib:
                    matched = tiger_left.search(tag.attrib['k'])
                    if matched:
                        has_tiger = True
                        break
            if has_tiger:
                for tag in element.iter("tag"):
                    if 'k' in tag.attrib and tag.attrib['k'] == "addr:postcode":
                        has_post_code = True
                        break

            if has_tiger and not has_post_code:
                tiger_zip_tag_no_postal += 1
    return tiger_zip_tag_no_postal


if False:
    print "{0} tags with tiger zip code but no address:postcode".format(inspect_nodes_with_tiger(OSMFILE))



