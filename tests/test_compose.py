from pathlib import Path
import yaml

def test_services_network_and_persistence():
    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / 'docker-compose.override.yml').read_text())
    assert set(config['services']) == {'mongodb', 'mongo-express'}
    assert config['services']['mongodb']['volumes'] == ['mongodb-data:/data/db', 'mongodb-config:/data/configdb']
    assert config['services']['mongo-express']['depends_on']['mongodb']['condition'] == 'service_healthy'
    assert config['services']['mongo-express']['ports'] == ['127.0.0.1:8081:8081']
    assert all(service['networks'] == ['airflow'] for service in config['services'].values())
