"""End-to-end API workflow tests under DEMO_MODE."""

from __future__ import annotations

import io


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True


def test_demo_sample(client):
    resp = client.get("/api/v1/demo/sample")
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] == "SAMPLE"
    assert "requirements" in body
    assert "architecture" in body


def test_full_workflow(client, sample_requirements_dict, sample_drawio_xml):
    # Create project
    r = client.post("/api/v1/projects", json={"name": "E2E Web App"})
    assert r.status_code == 201
    project = r.json()
    pid = project["id"]

    # List
    r = client.get("/api/v1/projects")
    assert r.status_code == 200
    assert any(p["id"] == pid for p in r.json())

    # Requirements
    r = client.put(f"/api/v1/projects/{pid}/requirements", json=sample_requirements_dict)
    assert r.status_code == 200
    assert r.json()["requirements"]["purpose"]

    # Clarify
    r = client.post(f"/api/v1/projects/{pid}/clarify", json={})
    assert r.status_code == 200
    assert "questions" in r.json()

    # Generate
    r = client.post(f"/api/v1/projects/{pid}/generate", json={"regenerate": True})
    assert r.status_code == 200
    assert r.json()["architecture"]["nodes"]

    # Confirm
    arch = r.json()["architecture"]
    r = client.post(
        f"/api/v1/projects/{pid}/confirm-architecture",
        json={"architecture": arch, "confirmed": True},
    )
    assert r.status_code == 200
    assert r.json()["architecture"]["confirmed"] is True

    # Evaluate
    r = client.post(f"/api/v1/projects/{pid}/evaluate")
    assert r.status_code == 200
    evaluation = r.json()
    assert "findings" in evaluation
    assert "scores" in evaluation
    assert 0 <= evaluation["scores"]["overall"] <= 100

    # Optimize
    r = client.post(f"/api/v1/projects/{pid}/optimize")
    assert r.status_code == 200
    assert r.json()["optimized"]["nodes"]

    # Compare
    r = client.get(f"/api/v1/projects/{pid}/compare")
    assert r.status_code == 200
    assert r.json()["original"] is not None
    assert r.json()["optimized"] is not None

    # Report
    r = client.get(f"/api/v1/projects/{pid}/report")
    assert r.status_code == 200
    assert "executive_summary" in r.json()

    # Exports
    r = client.get(f"/api/v1/projects/{pid}/export/drawio")
    assert r.status_code == 200
    assert b"mxfile" in r.content

    r = client.get(f"/api/v1/projects/{pid}/export/png")
    assert r.status_code == 200
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"

    r = client.get(f"/api/v1/projects/{pid}/export/excel")
    assert r.status_code == 200
    assert len(r.content) > 100

    # Upload drawio to a fresh project
    r = client.post("/api/v1/projects", json={"name": "Upload Project"})
    pid2 = r.json()["id"]
    r = client.post(
        f"/api/v1/projects/{pid2}/upload",
        files={"file": ("sample.drawio", sample_drawio_xml.encode("utf-8"), "application/xml")},
    )
    assert r.status_code == 200
    assert r.json()["architecture"]["nodes"]

    # Get / delete
    r = client.get(f"/api/v1/projects/{pid}")
    assert r.status_code == 200
    r = client.delete(f"/api/v1/projects/{pid}")
    assert r.status_code == 204
    r = client.get(f"/api/v1/projects/{pid}")
    assert r.status_code == 404


def test_upload_malformed_drawio(client, malformed_drawio_xml):
    r = client.post("/api/v1/projects", json={"name": "Bad Upload"})
    pid = r.json()["id"]
    r = client.post(
        f"/api/v1/projects/{pid}/upload",
        files={
            "file": (
                "bad.drawio",
                malformed_drawio_xml.encode("utf-8"),
                "application/xml",
            )
        },
    )
    assert r.status_code == 400


def test_generate_without_requirements_uses_prompt(client):
    """Agent assist may generate without a full requirements form."""
    r = client.post("/api/v1/projects", json={"name": "No Req"})
    pid = r.json()["id"]
    r = client.post(
        f"/api/v1/projects/{pid}/generate",
        json={"prompt": "Simple serverless API with DynamoDB"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("architecture") is not None
    assert len(body["architecture"]["nodes"]) >= 1


def test_put_architecture_hand_drawn(client):
    r = client.post("/api/v1/projects", json={"name": "Hand Draw"})
    pid = r.json()["id"]
    arch = {
        "id": "arch-hand",
        "name": "Hand",
        "nodes": [
            {
                "id": "n1",
                "service_id": "lambda",
                "label": "API Fn",
                "props": {},
                "x": 100,
                "y": 80,
            },
            {
                "id": "n2",
                "service_id": "dynamodb",
                "label": "Table",
                "props": {},
                "x": 320,
                "y": 80,
            },
        ],
        "edges": [{"id": "e1", "from": "n1", "to": "n2", "label": "read/write"}],
        "confirmed": True,
        "source": "hand",
        "metadata": {},
    }
    r = client.put(f"/api/v1/projects/{pid}/architecture", json=arch)
    assert r.status_code == 200
    assert r.json()["architecture"]["source"] == "hand"
    assert len(r.json()["architecture"]["nodes"]) == 2
