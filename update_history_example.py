import pymongo
from bson import ObjectId

import os

def write_to_mongo(time_period, grouping, score):
    client = pymongo.MongoClient(os.environ.get("DATABASE_URL"))

    db = client["peers"]
    collection = db["example"]
    
    data_from_mongo = list(collection.find())
    
    for data in data_from_mongo:
        if data["navbar_title"] == "DSG Peer Group Generator":
            navbar_title = "DSG Peer Group Generator_"
        else:
            navbar_title = "DSG Peer Group Generator"
            
    record = {
    "navbar_title":  navbar_title
    }

    collection.replace_one({"_id": ObjectId("630278b467f0249948f20bfd")},  {"navbar_title": navbar_title})
    print("replace document in mongo - example")
    # print(testing)
    return

def main():
    write_to_mongo()
    
    

if __name__ == "__main__":
    main()