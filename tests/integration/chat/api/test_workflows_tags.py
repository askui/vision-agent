"""Integration tests for workflow tag filtering."""

from fastapi.testclient import TestClient


def test_list_workflows_filter_by_single_tag(
    test_client_with_db: TestClient, test_headers: dict[str, str]
):
    """Test filtering workflows by a single tag."""
    # Create workflows with different tags
    workflow1_data = {
        "name": "Workflow 1",
        "description": "First workflow",
        "tags": ["automation", "testing"],
    }
    workflow2_data = {
        "name": "Workflow 2",
        "description": "Second workflow",
        "tags": ["testing", "deployment"],
    }
    workflow3_data = {
        "name": "Workflow 3",
        "description": "Third workflow",
        "tags": ["automation", "deployment"],
    }

    # Create workflows
    response1 = test_client_with_db.post(
        "/workflows", json=workflow1_data, headers=test_headers
    )
    assert response1.status_code == 201

    response2 = test_client_with_db.post(
        "/workflows", json=workflow2_data, headers=test_headers
    )
    assert response2.status_code == 201

    response3 = test_client_with_db.post(
        "/workflows", json=workflow3_data, headers=test_headers
    )
    assert response3.status_code == 201

    # Filter by "automation" tag
    response = test_client_with_db.get(
        "/workflows?tags=automation", headers=test_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) == 2
    workflow_names = [w["name"] for w in data["data"]]
    assert "Workflow 1" in workflow_names
    assert "Workflow 3" in workflow_names
    assert "Workflow 2" not in workflow_names


def test_list_workflows_filter_by_multiple_tags(
    test_client_with_db: TestClient, test_headers: dict[str, str]
):
    """Test filtering workflows by multiple tags (OR logic)."""
    # Create workflows with different tags
    workflow1_data = {
        "name": "Workflow 1",
        "description": "First workflow",
        "tags": ["automation", "testing"],
    }
    workflow2_data = {
        "name": "Workflow 2",
        "description": "Second workflow",
        "tags": ["testing", "deployment"],
    }
    workflow3_data = {
        "name": "Workflow 3",
        "description": "Third workflow",
        "tags": ["automation", "deployment"],
    }

    # Create workflows
    test_client_with_db.post("/workflows", json=workflow1_data, headers=test_headers)
    test_client_with_db.post("/workflows", json=workflow2_data, headers=test_headers)
    test_client_with_db.post("/workflows", json=workflow3_data, headers=test_headers)

    # Filter by "automation" OR "deployment" tags
    response = test_client_with_db.get(
        "/workflows?tags=automation&tags=deployment", headers=test_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) == 3  # All workflows should match
    workflow_names = [w["name"] for w in data["data"]]
    assert "Workflow 1" in workflow_names
    assert "Workflow 2" in workflow_names
    assert "Workflow 3" in workflow_names


def test_list_workflows_tag_filtering_with_pagination(
    test_client_with_db: TestClient, test_headers: dict[str, str]
):
    """Test combining tag filtering with pagination."""
    # Create multiple workflows with automation tag
    for i in range(5):
        workflow_data = {
            "name": f"Automation Workflow {i}",
            "description": f"Workflow {i}",
            "tags": ["automation"],
        }
        test_client_with_db.post("/workflows", json=workflow_data, headers=test_headers)

    # Create workflows with different tags
    for i in range(3):
        workflow_data = {
            "name": f"Testing Workflow {i}",
            "description": f"Workflow {i}",
            "tags": ["testing"],
        }
        test_client_with_db.post("/workflows", json=workflow_data, headers=test_headers)

    # Filter by automation tag with limit
    response = test_client_with_db.get(
        "/workflows?tags=automation&limit=3", headers=test_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) == 3
    assert data["has_more"] is True

    # Verify all returned workflows have automation tag
    for workflow in data["data"]:
        assert "automation" in workflow["tags"]


def test_modify_workflow_update_tags(
    test_client_with_db: TestClient, test_headers: dict[str, str]
):
    """Test modifying workflow to change tags."""
    # Create workflow with initial tags
    workflow_data = {
        "name": "Test Workflow",
        "description": "Test workflow",
        "tags": ["automation", "testing"],
    }

    response = test_client_with_db.post(
        "/workflows", json=workflow_data, headers=test_headers
    )
    assert response.status_code == 201
    workflow_id = response.json()["id"]

    # Modify workflow to change tags
    modify_data = {
        "name": "Updated Workflow",
        "description": "Updated description",
        "tags": ["deployment", "production"],
    }

    response = test_client_with_db.post(
        f"/workflows/{workflow_id}", json=modify_data, headers=test_headers
    )
    assert response.status_code == 200

    updated_workflow = response.json()
    assert updated_workflow["name"] == "Updated Workflow"
    assert updated_workflow["description"] == "Updated description"
    assert set(updated_workflow["tags"]) == {"deployment", "production"}

    # Verify old tags are no longer associated
    response = test_client_with_db.get(
        "/workflows?tags=automation", headers=test_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 0

    # Verify new tags are associated
    response = test_client_with_db.get(
        "/workflows?tags=deployment", headers=test_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == workflow_id
