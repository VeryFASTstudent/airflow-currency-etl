# Daily Currency Exchange ETL

Task 3 submission prepared for **VeryFASTstudent**.

GitHub repository: https://github.com/VeryFASTstudent/airflow-currency-etl
The repository contains the pipeline, configuration, automated tests and the PDF report.

## What it does

Every day at **18:00 UTC (23:00 Pakistan time)**, Airflow retrieves the latest published EUR rates for USD, GBP and JPY from the Frankfurter v2 API, validates and transforms each row, then upserts it into MongoDB. The three tasks are:

1. `extract_currency_exchange_rates`: explicit XCom key `raw_exchange_rates`.
2. `transform_exchange_rate_data`: pulls the first named XCom and pushes `transformed_exchange_rates`.
3. `load_data_into_mongodb`: pulls transformed records and writes MongoDB; pushes `load_summary` for inspection.

There are exactly three tasks. Named XComs, rather than implicit TaskFlow return values, transfer the data. XCom carries only the three small records. Network errors fail the task and Airflow retries twice with a two-minute delay. Invalid, missing, duplicate or nonpositive rates fail validation.

The DAG loads the latest *published* rates. It preserves the API's `date` as `rate_date` and adds a timezone-aware UTC extraction timestamp as `retrieved_at`. Holidays/weekends can return an earlier publication date; daily runs do not manufacture new rate dates. `catchup=False` means this is not a historical backfill DAG.

## Requirements

- Docker Desktop with Compose v2, running with enough memory for Airflow.
- Astro CLI (project scaffold initialized using CLI 1.47.0).
- Astro Runtime `3.1-2` / Airflow 3.1.2.
- For Windows: run these shell commands from WSL 2; Docker Desktop must have WSL integration enabled.

## Start with Astro CLI

The project is already initialized; **do not run `astro dev init` over these files**.

```bash
python scripts/configure_env.py
set -a
source .env
set +a
astro config set container.binary docker
astro dev start
astro dev ps
```

`scripts/configure_env.py` creates .env with randomly generated local credentials and refuses to overwrite an existing file. `.env.example` contains no passwords. If changing MongoDB credentials, update both the root settings and `MONGO_URI`; URL-encode special characters in URI passwords. Existing initialized volumes retain their previous MongoDB credentials.

Export `.env` into the shell as shown above before starting or restarting Astro; these exported variables are required for Compose interpolation. Astro CLI merges `docker-compose.override.yml` into its Airflow stack. Both additional services join Astro's project-scoped `airflow` bridge network. MongoDB uses the DNS service name `mongodb` from Airflow and Mongo Express; `localhost` would refer to each individual container. MongoDB is not exposed on a host port. Mongo Express binds only to host loopback port 8081.

Open Airflow using the URL and credentials printed by `astro dev start` (commonly localhost:8080). Open Mongo Express at http://localhost:8081 and use `ME_USERNAME` / `ME_PASSWORD` from `.env`.

## Execute and inspect

In Airflow, enable `currency_exchange_etl` and select **Trigger DAG**. Confirm all three task states show success. Alternatively:

```bash
astro dev run dags test currency_exchange_etl
```

In Airflow, select the extract task and inspect XCom key `raw_exchange_rates`. Inspect `transformed_exchange_rates` under the transform task and `load_summary` under the load task.

In Mongo Express, open database `currency_etl`, collection `exchange_rates`. Confirm the six required fields (MongoDB also adds `_id`). Inspect `unique_currency_date`, a unique compound index on `base_currency`, `target_currency`, `rate_date`.

To inspect records from a container:

```bash
astro dev bash --scheduler "python scripts/verify_mongo.py"
```

Rerunning the pipeline updates matching records instead of inserting duplicate currency/date rows. API rates may be revised during a day, so an upsert deliberately refreshes the rate and retrieval timestamp.

## Networking, image metadata and persistence

`Dockerfile` includes OCI title, author and description labels. Compose defines role, network and storage labels for the database services and named-volume labels. MongoDB has a healthcheck; Mongo Express waits for it to be healthy. `mongodb-data` mounts at `/data/db`; `mongodb-config` mounts at `/data/configdb`. Mongo Express is stateless and needs no data volume.

Use `astro dev stop` and `astro dev start` for a normal restart. Confirm saved documents remain. Do not remove MongoDB volumes when testing persistence; removing volumes destroys their stored data. PostgreSQL in Astro is Airflow's metadata store; MongoDB remains the primary database for the assignment's currency records.

## Tests and captured evidence

```bash
astro dev pytest
```

For tests outside Astro, install the project's requirements plus Airflow 3.1.2 and `dev-requirements.txt` in a virtual environment, then run `pytest -q`. The GitHub Actions workflow runs isolated ETL and Compose tests; the local validation also imports the actual DAG.

See `evidence/validation.json`, `evidence/airflow-final-run.log`, and `evidence/pytest.txt` for recorded validation. Code/output PNGs are rendered captures of the corresponding source files and real terminal results; they are not Airflow or Mongo Express UI screenshots.

**Environment limits:** Docker and Mongo Express could not be started in the build workspace. Live execution was checked using Airflow 3.1.2, the actual Frankfurter API and MongoDB 7.0.16 running directly on Linux. Container startup, Docker-volume restart persistence and Mongo Express UI still require the Docker steps above. The report states these limits explicitly.

## Submission

- Report: `report/Task3_Airflow_ETL_Report.pdf`.
- Source, configuration, tests and captured evidence are included in this repository.
- Repository: https://github.com/VeryFASTstudent/airflow-currency-etl .

## References

- Assignment: Task 3 Building Airflow ETL Pipeline (supplied PDF).
- https://frankfurter.dev/ — v2 response schema, base and quote filters.
- https://www.astronomer.io/docs/cli/v1.44/develop-project — Astro layout.
- https://www.astronomer.io/docs/cli/v1.44/run-airflow-locally — Compose overrides and local execution.
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html — explicit XCom push and pull.
