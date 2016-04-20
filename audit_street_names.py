import xml.etree.cElementTree as ET
from collections import defaultdict
from operator import itemgetter
import re
import codecs
import json
import pprint

import shared_code

OSMFILE = shared_code.OSMFILE
street_type_re = shared_code.street_type_re

expected = shared_code.expected

# after auditing street names these new mappings were created to map variations to expected
street_name_mapping = {
    'St': 'Street',
    'Ave': 'Avenue',
    'Ave.': 'Avenue',
    'Blvd': 'Boulevard',
    'Blvd.': 'Boulevard',
    'Dr': 'Drive',
    'Dr.': 'Drive',
    'Ln': 'Lane',
    'Pkwy': 'Parkway',
    'Rd': 'Road',
    'Rd.': 'Road',
    'St': 'Street',
    'St.': 'Street',
    'Street.': 'Street',
    'ave': 'Avenue'
}


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


# is this element in the format of expected street key
def is_street_name(elem):
    return elem.attrib['k'] == "addr:street"


# audit method to extract the street types
def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

if False:
    pprint.pprint(dict(audit(OSMFILE)))


# this method this method to update names to expected value
def update_name(name, mapping):
    better_name = name
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type in mapping:
            better_name = re.sub(street_type, mapping[street_type], name)
    return better_name


# regular expressions to test keys
lower = shared_code.lower
lower_colon = shared_code.lower_colon
problemchars = shared_code.problemchars
# this regular expression is to adjust right apostrophe unicode character in the data
right_apos = re.compile(ur'\u2019', re.IGNORECASE)


zip_code_re = shared_code.zip_code_re


# according to http://www.structnet.com/instructions/zip_min_max_by_state.html and local knowledge
# the valid ohio zip codes should fall in the range of 43001 and 45999
def update_zip_code(zip):
    matched = zip_code_re.match(zip)
    if matched:
        zip_code = int(matched.group(1))
        if zip_code >= 43001 and zip_code <= 45999:
            return zip_code
    return None

# shape the data set into a python dictionary to prepare for import to mongodb
CREATED = ["version", "changeset", "timestamp", "user", "uid"]


# helper function to see if array is a street
def is_street_tag(key_array):
    if len(key_array) > 1 and key_array[0] == 'addr' and key_array[1] == 'street':
        return True
    return False


# assumes the tag is a street tag with only one : that split it
def is_street_tag_only(street_tag):
    return len(street_tag) == 2


def is_postal_tag(key_array):
    if len(key_array) > 1 and key_array[1] == 'postcode':
        return True
    return False

tiger_left = re.compile(r'^tiger:zip_left$')
tiger_right = re.compile(r'^tiger:zip_right$')


# for auditing tiger zips used
zips_from_tiger = set()

# search an element for tiger zip tags to add to our nodes
# if it has a postal code, use that...else check tiger tags
# if it has either a left or right only return that cleaned zip code
# if it has a left and right, check they are equal and return
# if not equal, or not a valid zip or does not contain tag, return none
def get_best_matched_zip(element):
    left_zip = None
    right_zip = None
    postal_zip = None
    for tag in element.iter("tag"):
        if 'k' in tag.attrib:
            key_array = tag.attrib['k'].split(":")
            if is_postal_tag(key_array):
                postal_zip = update_zip_code(tag.attrib['v'])
                break
            matched = tiger_left.search(tag.attrib['k'])
            if matched:
                left_zip = update_zip_code(tag.attrib['v'])
                continue
            matched = tiger_right.search(tag.attrib['k'])
            if matched:
                right_zip = update_zip_code(tag.attrib['v'])
                continue
    if postal_zip:
        return postal_zip
    if left_zip and right_zip and left_zip == right_zip:
        zips_from_tiger.add(left_zip)
        return left_zip
    if left_zip:
        zips_from_tiger.add(left_zip)
        return left_zip
    if right_zip:
        zips_from_tiger.add(right_zip)
        return right_zip
    return None

# filter list so we do not overwrite our primary schema keys
keys_to_ignore = ["type", "id", "visible", "created", "address", "addr:postcode"]
tiger_tag = shared_code.tiger_tag
tag_keys = defaultdict()


# in the data i found other tag tags had "type" as a key and it was changing
# my node / way type so I created an ignore list
def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way":
        if element.tag == "node":
            node['type'] = "node"
        else:
            node['type'] = "way"

        node['id'] = element.attrib['id']

        if 'visible' in element.attrib:
            node['visible'] = element.attrib['visible']

        if 'lat' in element.attrib and 'lon' in element.attrib:
            node['pos'] = []
            node['pos'].append(float(element.attrib['lat']))
            node['pos'].append(float(element.attrib['lon']))

        for c in CREATED:
            if c in element.attrib:
                if 'created' not in node:
                    node['created'] = {}
                node['created'][c] = element.attrib[c]

        if element.tag == "way":
            zip_code = get_best_matched_zip(element)
            # added postal codes to the address when present
            # clean zip and ignore non standard zips before attempting to add
            if zip_code:
                if 'address' not in node:
                    node['address'] = {}
                node['address']['postcode'] = zip_code

            for tag in element.iter("tag"):
                matched = problemchars.search(tag.attrib['k'])
                if matched is None:
                    key_array = tag.attrib['k'].split(':')
                    value = tag.attrib['v']
                    matched = right_apos.search(value)
                    # added to make apostrophe characters consistent
                    if matched:
                        value = re.sub(ur'\u2019', "'", value)

                    # this is to audit the list of available tags and find problems
                    # if tag.attrib['k'] in tag_keys:
                    #     tag_keys[tag.attrib['k']] += 1
                    # else:
                    #     tag_keys[tag.attrib['k']] = 1

                    if is_street_tag(key_array):
                        if 'address' not in node:
                            node['address'] = {}
                        # only add the tag if it is just the street, no extra : delimiter
                        if is_street_tag_only(key_array):
                            node['address']['street'] = update_name(value, street_name_mapping)

                    # # added postal codes to the address when present
                    # # clean zip and ignore non standard zips before attempting to add
                    # if zip_code:
                    #     if 'address' not in node:
                    #         node['address'] = {}
                    #     node['address']['postcode'] = zip_code

                    # if is_postal_tag(key_array):
                    #     if 'address' not in node:
                    #         node['address'] = {}
                    #     zipcode = update_zip_code(value)
                    #     if zipcode:
                    #         node['address']['postcode'] = zipcode

                    if 'k' in tag.attrib and tag.attrib['k'] not in keys_to_ignore:
                        matched = tiger_tag.search(tag.attrib['k'])
                        if not matched:
                            tag_keys[tag.attrib['k']] = 1
                            node[tag.attrib['k']] = value

            for tag in element.iter("nd"):
                if 'node_refs' not in node:
                    node['node_refs'] = []
                if 'ref' in tag.attrib:
                    node['node_refs'].append(tag.attrib['ref'])

        return node
    return None


# runs main code and creates our json file
def process_map(file_in, pretty = False):
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data


data = process_map(OSMFILE)
#pprint.pprint(sorted(tag_keys.items(), key=itemgetter(1)))
#pprint.pprint(zips_from_tiger)

# take a look at the data
# with open('cleveland_ohio.osm.json') as fp:
#     json_data = json.loads(fp.readline())
#
# print json_data