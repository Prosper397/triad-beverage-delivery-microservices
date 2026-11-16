import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def _load_service_main(service_dir: str, module_name: str):
    path = ROOT / service_dir / "main.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "service_dir,module_name,service_name",
    [
        ("microservice-client", "service_client_main", "client"),
        ("microservice-manager", "service_manager_main", "manager"),
        ("microservice-agent", "service_agent_main", "agent"),
    ],
)
def test_health(service_dir, module_name, service_name):
    module = _load_service_main(service_dir, module_name)
    client = TestClient(module.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": service_name}


def test_manager_n_expose_pas_auth_register():
    module = _load_service_main("microservice-manager", "service_manager_main_register_check")
    client = TestClient(module.app)
    response = client.post("/auth/register", json={})
    assert response.status_code == 404
