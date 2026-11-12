"""Daily latest published rates: exactly three tasks, explicit named XComs."""
import logging
import os
from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task, get_current_context
from fx_pipeline import extract_rates, transform_rates, load_rates


@dag(dag_id="currency_exchange_etl", schedule="0 18 * * *",
     start_date=datetime(2026, 1, 1, tzinfo=timezone.utc), catchup=False,
     max_active_runs=1, default_args={"owner": "VeryFASTstudent", "retries": 2,
                                    "retry_delay": timedelta(minutes=2)},
     tags=["assignment", "currency", "mongodb"],
     description="Daily Frankfurter rates to MongoDB using named XComs")
def currency_exchange_etl():
    @task(task_id="extract_currency_exchange_rates", do_xcom_push=False)
    def extract():
        quotes = tuple(q.strip().upper() for q in os.getenv("FX_QUOTES", "USD,GBP,JPY").split(",") if q.strip())
        raw = extract_rates(os.getenv("FX_BASE", "EUR").upper(), quotes)
        get_current_context()["ti"].xcom_push(key="raw_exchange_rates", value=raw)
        logging.info("Extracted %s rates", len(raw["rows"]))

    @task(task_id="transform_exchange_rate_data", do_xcom_push=False)
    def transform():
        ti = get_current_context()["ti"]
        raw = ti.xcom_pull(task_ids="extract_currency_exchange_rates", key="raw_exchange_rates")
        docs = transform_rates(raw)
        ti.xcom_push(key="transformed_exchange_rates", value=docs)
        logging.info("Transformed %s validated documents", len(docs))

    @task(task_id="load_data_into_mongodb", do_xcom_push=False)
    def load():
        ti = get_current_context()["ti"]
        docs = ti.xcom_pull(task_ids="transform_exchange_rate_data", key="transformed_exchange_rates")
        stats = load_rates(docs, os.environ["MONGO_URI"],
                           os.getenv("MONGO_DATABASE", "currency_etl"),
                           os.getenv("MONGO_COLLECTION", "exchange_rates"))
        ti.xcom_push(key="load_summary", value=stats)
        logging.info("MongoDB load summary: %s", stats)

    extract() >> transform() >> load()


currency_exchange_etl()
