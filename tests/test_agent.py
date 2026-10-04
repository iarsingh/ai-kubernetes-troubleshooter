from fastapi.testclient import TestClient
from k8strouble.main import app

client = TestClient(app)


def test_runs_and_refuses_a_write():
    payload = client.post("/agent/run", json={"goal": 'why is the pod failing', **{'payload': {'events': ['BackOff restarting failed container']}}}).json()
    assert payload["refused"] is False
    assert payload["applied"] is False
    assert payload["hypothesis"] == "crashloop"
    refused = client.post("/agent/run", json={"goal": 'kubectl delete pod api-0'}).json()
    assert refused["refused"] is True
