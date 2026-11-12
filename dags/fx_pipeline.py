"""Testable ETL logic; Airflow orchestration lives in currency_exchange_etl.py."""
import math
from datetime import date, datetime, timezone

import requests
from pymongo import ASCENDING, MongoClient, UpdateOne

API_URL = "https://api.frankfurter.dev/v2/rates"


def extract_rates(base="EUR", quotes=("USD", "GBP", "JPY")):
    response = requests.get(API_URL, params={"base": base, "quotes": ",".join(quotes)}, timeout=(10, 30))
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or not payload:
        raise ValueError("API response must be a nonempty list")
    return {"rows": payload, "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "base": base, "quotes": list(quotes)}


def transform_rates(raw):
    if not isinstance(raw, dict) or not raw.get("rows"):
        raise ValueError("Missing extracted rows")
    retrieved = datetime.fromisoformat(raw["retrieved_at"])
    if retrieved.tzinfo is None:
        raise ValueError("retrieved_at must include a timezone")
    documents, seen = [], set()
    for row in raw["rows"]:
        base, quote = row["base"].upper(), row["quote"].upper()
        if base != raw["base"].upper() or quote not in {q.upper() for q in raw["quotes"]}:
            raise ValueError("Unexpected currency in response")
        if isinstance(row["rate"], bool):
            raise ValueError("Boolean exchange rate is invalid")
        rate = float(row["rate"])
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("Exchange rate must be finite and positive")
        rate_date = date.fromisoformat(row["date"]).isoformat()
        key = (base, quote, rate_date)
        if key in seen:
            raise ValueError("Duplicate currency/date in source")
        seen.add(key)
        documents.append({"base_currency": base, "target_currency": quote,
                          "exchange_rate": rate, "rate_date": rate_date,
                          "source": "Frankfurter API", "retrieved_at": raw["retrieved_at"]})
    if {d["target_currency"] for d in documents} != {q.upper() for q in raw["quotes"]}:
        raise ValueError("API response is missing a requested quote currency")
    return documents


def load_rates(documents, uri, database="currency_etl", collection="exchange_rates"):
    if not documents:
        raise ValueError("Refusing to load an empty dataset")
    with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
        client.admin.command("ping")
        target = client[database][collection]
        target.create_index([("base_currency", ASCENDING), ("target_currency", ASCENDING),
                             ("rate_date", ASCENDING)], unique=True, name="unique_currency_date")
        operations = [UpdateOne({k: doc[k] for k in ("base_currency", "target_currency", "rate_date")},
                                {"$set": doc}, upsert=True) for doc in documents]
        result = target.bulk_write(operations, ordered=False)
        return {"processed": len(documents), "inserted": result.upserted_count,
                "matched": result.matched_count, "modified": result.modified_count}
