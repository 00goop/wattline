"""Frozen read-only API contract, independent of pipeline regeneration."""
import json
import pytest
from fastapi.testclient import TestClient
from api import main

client = TestClient(main.app)

@pytest.mark.parametrize("hour", range(25))
def test_every_hour_matches_prefetched_series(hour):
    response = client.get('/api/exposure', params={'hour': hour})
    assert response.status_code == 200
    assert response.json() == client.get('/api/exposure/all').json()[str(hour)]
    assert response.json()['hour'] == hour

@pytest.mark.parametrize('hour', [-1, 25, 'bad', '1.5'])
def test_invalid_hour(hour):
    assert client.get('/api/exposure', params={'hour':hour}).status_code == 422

@pytest.mark.parametrize('path', ['/api/npus','/api/sites','/api/stats','/api/exposure/all'])
def test_data_endpoints_are_read_only(path):
    assert client.get(path).status_code == 200
    assert client.post(path,json={}).status_code == 405

@pytest.mark.parametrize('processed', [None, '{broken', '[]', '{"sites":[]}'])
def test_source_precedence_and_bad_data_fallback(tmp_path,monkeypatch,processed):
    monkeypatch.setattr(main,'ROOT',tmp_path)
    monkeypatch.setattr(main,'SOURCES',{})
    for directory in ['data/processed','mocks']:(tmp_path/directory).mkdir(parents=True)
    mock={'sites':[{'site_id':'fixture'}]}
    (tmp_path/'mocks/sites.json').write_text(json.dumps(mock))
    if processed is not None:(tmp_path/'data/processed/sites.json').write_text(processed)
    expected={'sites':[]} if processed=='{"sites":[]}' else mock
    assert main.load('sites') == expected
    assert main.SOURCES['sites'] == ('processed' if expected!=mock else 'mocks')

def test_missing_sources_fail_explicitly(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'ROOT',tmp_path)
    with pytest.raises(RuntimeError,match='no data source'):main.load('sites')

def test_missing_hour_is_not_fabricated(monkeypatch):
    monkeypatch.setattr(main,'EXPOSURE',{})
    assert client.get('/api/exposure?hour=4').status_code==404

def test_health_reports_loaded_sources():
    data=client.get('/api/health').json()
    assert data['status']=='ok'
    assert data['exposure_hours']==25
    assert set(data['sources'])=={'npus','exposure','sites','stats'}
