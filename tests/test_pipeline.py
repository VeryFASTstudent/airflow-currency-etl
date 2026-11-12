from copy import deepcopy
from unittest.mock import Mock, patch
import pytest
from fx_pipeline import extract_rates, transform_rates, load_rates

@pytest.fixture
def raw():
    return {'rows': [{'date': '2026-11-04', 'base': 'EUR', 'quote': 'USD', 'rate': 1.15}],
            'retrieved_at': '2026-11-05T07:15:00+00:00', 'base': 'EUR', 'quotes': ['USD']}

def test_exact_schema(raw):
    assert transform_rates(raw) == [{'base_currency': 'EUR', 'target_currency': 'USD',
        'exchange_rate': 1.15, 'rate_date': '2026-11-04', 'source': 'Frankfurter API',
        'retrieved_at': raw['retrieved_at']}]

@pytest.mark.parametrize('rate', [0, -1, float('nan'), float('inf'), True, 'bad'])
def test_invalid_rate(raw, rate):
    raw['rows'][0]['rate'] = rate
    with pytest.raises(ValueError): transform_rates(raw)

def test_bad_date(raw):
    raw['rows'][0]['date'] = '2026-02-30'
    with pytest.raises(ValueError): transform_rates(raw)

def test_duplicates(raw):
    raw['rows'].append(deepcopy(raw['rows'][0]))
    with pytest.raises(ValueError, match='Duplicate'): transform_rates(raw)

def test_missing_quote(raw):
    raw['quotes'].append('GBP')
    with pytest.raises(ValueError, match='missing'): transform_rates(raw)

def test_wrong_base(raw):
    raw['rows'][0]['base'] = 'GBP'
    with pytest.raises(ValueError, match='Unexpected'): transform_rates(raw)

def test_naive_timestamp(raw):
    raw['retrieved_at'] = '2026-11-05T07:15:00'
    with pytest.raises(ValueError, match='timezone'): transform_rates(raw)

def test_no_raw_data():
    with pytest.raises(ValueError): transform_rates(None)

@patch('fx_pipeline.requests.get')
def test_http_failure_is_not_swallowed(get):
    get.return_value.raise_for_status.side_effect = RuntimeError('HTTP failure')
    with pytest.raises(RuntimeError): extract_rates()

@patch('fx_pipeline.requests.get')
@pytest.mark.parametrize('body', [[], {}, None])
def test_bad_api_shape(get, body):
    get.return_value.json.return_value = body
    with pytest.raises(ValueError): extract_rates()

@patch('fx_pipeline.requests.get')
def test_extract_metadata_and_timeout(get, raw):
    get.return_value.json.return_value = raw['rows']
    result = extract_rates('EUR', ('USD',))
    assert result['quotes'] == ['USD']
    assert result['retrieved_at'].endswith('+00:00')
    assert get.call_args.kwargs['timeout'] == (10, 30)

def test_empty_load():
    with pytest.raises(ValueError): load_rates([], 'mongodb://unused')
