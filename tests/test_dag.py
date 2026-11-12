from pathlib import Path
from airflow.models import DagBag

def test_real_dag_import_and_dependencies():
    bag = DagBag(dag_folder=str(Path(__file__).resolve().parents[1] / 'dags'), include_examples=False)
    assert not bag.import_errors, bag.import_errors
    dag = bag.dags['currency_exchange_etl']
    assert len(dag.tasks) == 3
    assert dag.get_task('extract_currency_exchange_rates').downstream_task_ids == {'transform_exchange_rate_data'}
    assert dag.get_task('transform_exchange_rate_data').downstream_task_ids == {'load_data_into_mongodb'}
    assert dag.max_active_runs == 1
    assert dag.catchup is False
