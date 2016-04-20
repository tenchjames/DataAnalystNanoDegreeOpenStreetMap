from pymongo import MongoClient
import pprint


# convenience function. Mongo returns a cursor with find
def pretty_print_cursor(cursor):
    for document in cursor:
        pprint.pprint(document)


def get_db():
    client = MongoClient('localhost:27017')
    db = client.openstreetmap
    return db


def number_of_nodes_by_type(type):
    db = get_db()
    return db.clevelandohio.find({"type": type}).count()

if False:
    print "nodes: {0}".format(number_of_nodes_by_type("node"))
    print "ways: {0}".format(number_of_nodes_by_type("way"))


# my focus was on the types and number of food establishments in the area
def get_food_node_count(db):
    return db.clevelandohio.aggregate(
        [
            {
                "$match": {
                    "$or": [{"cuisine": {"$exists": True}},
                            {"$and": [{"amenity": {"$exists": True}}, {"amenity": "restaurant"}]},
                            {"food": {"$exists": True}}
                            ]
                }
            },
            {"$group": {"_id": "food_total", "count": {"$sum": 1}}}
        ]
    )

if False:
    db = get_db()
    cursor = get_food_node_count(db)
    pretty_print_cursor(cursor)


# what are the most popular restaurants / fast food chains in this area
# after querying data I found characters like the "'" encoded different ways
# causing places with the same name to appear different. I went back and
# cleaned the data and set some expected values for those
# search for tags identified as a food type of location
def get_restaurant_count(db):
    return db.clevelandohio.aggregate(
        [
            {
                "$match": {
                    "$or": [{"cuisine": {"$exists": True}},
                            {"$and": [{"amenity": {"$exists": True}}, {"amenity": "restaurant"}]},
                            {"food": {"$exists": True}}
                            ]
                }
            },
            {
                "$project": {
                    "name": {"$toLower": "$name"}
                }
            },

            {
                "$group": {"_id": "$name", "count": {"$sum": 1}}
            },
            {
                "$sort": {"count": -1}
            }
        ]
    )

if False:
    db = get_db()
    cursor = get_restaurant_count(db)
    pretty_print_cursor(cursor)


# uncovered other node types which led to finding they type key in other nodes that was causing
# problems in data cleaning step.
def get_non_way_node_type(db):
    return db.clevelandohio.find({"$and": [{"type": {"$ne": "way"}}, {"type": {"$ne": "node"}}]})

if False:
    db = get_db()
    cursor = get_non_way_node_type(db)
    pretty_print_cursor(cursor)


# confirm user count matches python analysis
def get_users_with_count(db):
    return db.clevelandohio.aggregate(
        [
            {
                "$group": {"_id": "$created.user", "count": {"$sum": 1}}
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": 10
            }
        ]
    )

if False:
    db = get_db()
    cursor = get_users_with_count(db)
    pretty_print_cursor(cursor)


# query to see what users are contributing and how many nodes they have contributed related to food
def get_user_food_contributions(db):
    return db.clevelandohio.aggregate(
        [
            {
                "$match": {
                    "$or": [{"cuisine": {"$exists": True}},
                            {"$and": [{"amenity": {"$exists": True}}, {"amenity": "restaurant"}]},
                            {"food": {"$exists": True}}
                            ]
                }
            },
            {
                "$group": {"_id": "$created.user", "count": {"$sum": 1}}
            },
            {
                "$sort": {"count" : -1}
            },
            {
                "$limit": 10
            }
        ]
    )

if False:
    db = get_db()
    cursor = get_user_food_contributions(db)
    pretty_print_cursor(cursor)


def get_zip_codes(db):
    return db.clevelandohio.aggregate(
        [
            {
                "$match": {"address.postcode": {"$exists": True}}
            },
            {
                "$group": {"_id": "$address.postcode"}
            }
        ]
    )


if False:
    db = get_db()
    cursor = get_zip_codes(db)
    pretty_print_cursor(cursor)