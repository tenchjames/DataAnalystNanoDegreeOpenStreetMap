import re


OSMFILE = 'cleveland_ohio.osm'
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# street types we expect to see
# added additional after initial parse like Way
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Way", "Circle"]

# regular expressions to test keys
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

tiger = re.compile(r'^tiger:zip*')

zip_code_re = re.compile(r'(\d{5})')