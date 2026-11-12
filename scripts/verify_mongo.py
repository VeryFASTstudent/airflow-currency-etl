"""Inspect records after a run: open astro dev bash --scheduler,
then execute python scripts/verify_mongo.py inside the shell.
"""
import json
import os
from pymongo import MongoClient

with MongoClient(os.environ["MONGO_URI"]) as client:
    target = client[os.getenv("MONGO_DATABASE", "currency_etl")][os.getenv("MONGO_COLLECTION", "exchange_rates")]
    print("Document count:", target.count_documents({}))
    print(json.dumps(list(target.find({}, {"_id": 0}).sort("target_currency", 1)), indent=2))
    print("Indexes:", json.dumps(target.index_information(), default=str, indent=2))
