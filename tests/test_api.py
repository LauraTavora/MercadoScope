from fastapi.testclient import TestClient

from app.main import app


def test_health_and_mock_job():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["version"] == "1.0.0"

        created = client.post(
            "/api/v1/jobs",
            headers={"X-Tenant-ID": "demo-store"},
            json={"query": "notebook gamer", "max_pages": 1, "sort": "relevance"},
        )
        assert created.status_code == 202
        job_id = created.json()["id"]

        job = client.get(f"/api/v1/jobs/{job_id}", headers={"X-Tenant-ID": "demo-store"})
        assert job.status_code == 200
        assert job.json()["status"] == "completed"
        assert job.json()["item_count"] > 0

        products = client.get(
            f"/api/v1/jobs/{job_id}/products", headers={"X-Tenant-ID": "demo-store"}
        )
        assert products.status_code == 200
        assert len(products.json()) > 0
