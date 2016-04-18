# DataAnalystNanoDegreeOpenStreetMap

**Author**: James Tench
**Project**: Udacity Data Analyst project 3

#### Project Summary
---
This project is the final project associated with the Data Wrangling course. The purpose of the course, and project is to demonstrate the process of converting raw xml to a usable format for data analysis.

The conversion process involved auditing, cleaning, and shaping the  data into a usable schema in json format. Python was used for pre-processing the data

MongoDb or SQL were both options for completing the project. MongoDB was selected for this project.

Data source: [Mapzen](https://mapzen.com/data/metro-extracts/)
Map area: [Cleveland Ohio](https://s3.amazonaws.com/metro-extracts.mapzen.com/cleveland_ohio.osm.bz2)
File Size: 362.4 MB uncompressed

---

### Project Criteria

#### 1. Problems encountered with the map

##### Inconsistent Street names
Inconsistent street names were found throughout the file. Most common cases were abbreviations for Street with St. or Road rd. To correct the names based on the common naming in the area the python code was updated to map and update the values during the shaping process. This was done with a python dictionary.
`street_name_mapping = {
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
`

##### Inconsistent characters
During the data query phase, while running aggregate queries in MongoDB these inconsistencies were found. Specifically the single quote character was represented with the unicode \u2019 and the "'" symbol. This was causing data to group in different ways.

At this point I went back to the data cleaning process and wrote a simple regular expression to change to one consistent character when the unicode character was encountered.
`right_apos = re.compile(ur'\u2019', re.IGNORECASE)`
`matched = right_apos.search(value)`
`if matched:`
`value = re.sub(ur'\u2019', "'", value)`

##### Problem keys in tags
My schema identified an entry by the type based openstreetmap model of nodes, ways and references. To account for this my schema has a field "type" which indicated what type of node. 
After the parsing process was complete I found other values for "type" than what was expected. To investigate the issue I added code to track all of the key names and the number of times they appeared.
I found that there was a key on the "tag" nodes of "type". This key was overwriting the original expected value. Overall there were only 42 occurrences of this issue.
To correct the problem I chose to ignore this tag as I was shaping the data. To control that key value and other keys that I knew were part of my schema I created an ignore list.
`keys_to_ignore = ["type", "id", "visible", "created", "address"]`

##### Additional tags
During the tag counting process I found the following tags:
`{'bounds': 1,`
`'member': 19661,`
`'nd': 1871102,`
`'node': 1610592,`
`'osm': 1,`
`'relation': 2548,`
`'tag': 1069095,`
`'way': 166319}`

I expected now, way, relation, tag and nd. The other tags were not expected. I could not find a need to include any of these tags in the data so the python code ignored those tags.

#### 2. Overview of the data

File size: cleveland_ohio.osm 362.4 MB
Unique user count: 977
 


