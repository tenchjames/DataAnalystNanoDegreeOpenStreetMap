import xml.etree.cElementTree as ET
import pprint
import operator

OSMFILE = 'cleveland_ohio.osm'

# audit to see how many tags are in our data
def count_tags(filename):
    tags = {}
    for event, ele in ET.iterparse(filename):
        current_tag = ele.tag
        if not current_tag in tags:
            tags[current_tag] = 1
        else:
            tags[current_tag] += 1
    return tags

if False:
    pprint.pprint(count_tags(OSMFILE))


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

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Way", "Circle"]