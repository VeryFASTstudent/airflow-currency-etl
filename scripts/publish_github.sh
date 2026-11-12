#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
account=$(gh api user --jq .login)
if [ "$account" != "VeryFASTstudent" ]; then
  echo "Authenticate gh as VeryFASTstudent before publishing. Current account: $account" >&2
  exit 1
fi
if [ ! -d .git ]; then
  git init -b main
  git add .
  git -c user.name=VeryFASTstudent -c user.email=VeryFASTstudent@users.noreply.github.com commit -m "Build daily Airflow currency ETL with MongoDB and report"
fi
gh repo create VeryFASTstudent/airflow-currency-etl --public --source=. --remote=origin --push
