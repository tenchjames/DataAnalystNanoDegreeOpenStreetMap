import xml.etree.cElementTree as ET
from collections import defaultdict
from operator import itemgetter
import re
import codecs
import json
import pprint

OSMFILE = 'cleveland_ohio.osm'
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# street types we expect to see
# added additional after initial parse like Way
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Way", "Circle"]

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


# pprint.pprint(dict(audit(OSMFILE)))

# this method this method to update names to expected value
def update_name(name, mapping):
    better_name = name
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type in mapping:
            better_name = re.sub(street_type, mapping[street_type], name)
    return better_name




# test key to see how many have problem characters
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
right_apos = re.compile(ur'\u2019', re.IGNORECASE)

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



def audit_keys(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys

#pprint.pprint(audit_keys(OSMFILE))
# only one key found with problems addr.source:street
# I choose to ignore this key


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

#pprint.pprint(get_unique_keys(OSMFILE))


# shape the data set into a python dictionary to prepare for import to mongodb
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def is_street_tag(keyArray):
    if len(keyArray) > 1 and keyArray[0] == 'addr' and keyArray[1] == 'street':
        return True
    return False


# assumes the tag is a street tag with only one : that split it
def is_street_tag_only(street_tag):
    return len(street_tag) == 2

keys_to_ignore = ["type", "id", "visible", "created", "address"]
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
                    if tag.attrib['k'] in tag_keys:
                        tag_keys[tag.attrib['k']] += 1
                    else:
                        tag_keys[tag.attrib['k']] = 1

                    if is_street_tag(key_array):
                        if 'address' not in node:
                            node['address'] = {}
                        # only add the tag if it is just the street, no extra : delimiter
                        if is_street_tag_only(key_array):
                            node['address']['street'] = update_name(value, street_name_mapping)
                    elif 'k' in tag.attrib and tag.attrib['k'] not in keys_to_ignore:
                        node[tag.attrib['k']] = value

            for tag in element.iter("nd"):
                if 'node_refs' not in node:
                    node['node_refs'] = []
                if 'ref' in tag.attrib:
                    node['node_refs'].append(tag.attrib['ref'])

        return node
    return None


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
pprint.pprint(sorted(tag_keys.items(), key=itemgetter(1)))


# take a look at the data
# with open('cleveland_ohio.osm.json') as fp:
#     json_data = json.loads(fp.readline())
#
# print json_data