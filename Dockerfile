FROM astrocrpublic.azurecr.io/runtime:3.1-2
LABEL org.opencontainers.image.title="Daily Currency Exchange ETL" \
      org.opencontainers.image.authors="VeryFASTstudent" \
      org.opencontainers.image.description="Frankfurter API to MongoDB using Airflow named XComs"
COPY --chown=astro:0 scripts /usr/local/airflow/scripts
