import xml.etree.cElementTree as ET
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

if True:
    pprint.pprint(audit_keys(OSMFILE))