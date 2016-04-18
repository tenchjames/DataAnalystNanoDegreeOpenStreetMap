from pymongo import MongoClient
import pprint

def get_db():
    client = MongoClient('localhost:27017')
    db = client.openstreetmap
    return db


def get_first_node(db):
    return db.clevelandohio.find_one()


def get_amenity(db):
    return db.clevelandohio.find_one({"type": "way", "amenity": "restaurant", "name": "Subway"})


def get_amenity_count(db):
    return db.clevelandohio.aggregate(
        [
            {"$group": {"_id": "$amenity", "count": {"$sum": 1}}}
        ]
    )

# what are the most popular restaurants / fast food chains in this area
# after querying data I found characters like the "'" encoded different ways
# causing places with the same name to appear different. I went back and
# cleaned the data and set some expected values for those
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


def get_non_way_node_type(db):
    return db.clevelandohio.find({"$and": [{"type":{"$ne": "way"}}, {"type":{"$ne": "node"}}]})


def pretty_print_cursor(cursor):
    for document in cursor:
        pprint.pprint(document)


if __name__ == "__main__":
    db = get_db()
    #pprint.pprint(get_first_node(db))
    #pprint.pprint(get_amenity(db))
    # for document in get_amenity_count(db):
    #     pprint.pprint(document)
    #pretty_print_cursor(get_non_way_node_type(db))
    #pretty_print_cursor(get_non_way_node_type(db))
    pretty_print_cursor(get_restaurant_count(db))
