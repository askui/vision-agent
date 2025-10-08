"""Integration tests for event streaming."""

import json

import pytest
from fastapi.testclient import TestClient


def test_event_streaming_with_multiple_readers(
    test_client_with_db: TestClient, test_headers: dict[str, str]
):
    """Test event streaming with multiple readers."""
    # Create a thread first
    thread_data = {"name": "Test Thread"}
    response = test_client_with_db.post(
        "/threads", json=thread_data, headers=test_headers
    )
    assert response.status_code == 201
    thread_id = response.json()["id"]

    # Create an assistant
    assistant_data = {
        "name": "Test Assistant",
        "description": "Test assistant",
        "tools": [],
        "system": "You are a test assistant",
    }
    response = test_client_with_db.post(
        "/assistants", json=assistant_data, headers=test_headers
    )
    assert response.status_code == 201
    assistant_id = response.json()["id"]

    # Create a run
    run_data = {"assistant_id": assistant_id, "instructions": "Test instructions"}
    response = test_client_with_db.post(
        f"/threads/{thread_id}/runs", json=run_data, headers=test_headers
    )
    assert response.status_code == 201
    run_id = response.json()["id"]

    # Start streaming events
    response = test_client_with_db.get(
        f"/threads/{thread_id}/runs/{run_id}/events/stream", headers=test_headers
    )
    assert response.status_code == 200

    # The response should be a streaming response
    assert response.headers["content-type"] == "text/event-stream"

    # Read the stream content
    stream_content = response.content.decode("utf-8")

    # Should contain event data
    assert "data:" in stream_content
    assert "event:" in stream_content


def test_event_streaming_with_cancellation(
    test_client_with_db: TestClient, test_headers: dict[str, str]
):
    """Test event streaming with run cancellation."""
    # Create a thread first
    thread_data = {"name": "Test Thread"}
    response = test_client_with_db.post(
        "/threads", json=thread_data, headers=test_headers
    )
    assert response.status_code == 201
    thread_id = response.json()["id"]

    # Create an assistant
    assistant_data = {
        "name": "Test Assistant",
        "description": "Test assistant",
        "tools": [],
        "system": "You are a test assistant",
    }
    response = test_client_with_db.post(
        "/assistants", json=assistant_data, headers=test_headers
    )
    assert response.status_code == 201
    assistant_id = response.json()["id"]

    # Create a run
    run_data = {"assistant_id": assistant_id, "instructions": "Test instructions"}
    response = test_client_with_db.post(
        f"/threads/{thread_id}/runs", json=run_data, headers=test_headers
    )
    assert response.status_code == 201
    run_id = response.json()["id"]

    # Cancel the run
    response = test_client_with_db.post(
        f"/threads/{thread_id}/runs/{run_id}/cancel", headers=test_headers
    )
    assert response.status_code == 200

    # Start streaming events
    response = test_client_with_db.get(
        f"/threads/{thread_id}/runs/{run_id}/events/stream", headers=test_headers
    )
    assert response.status_code == 200

    # Read the stream content
    stream_content = response.content.decode("utf-8")

    # Should contain cancellation event
    assert "cancelled" in stream_content or "cancel" in stream_content.lower()


def test_event_streaming_with_error_handling(
    test_client_with_db: TestClient, test_headers: dict[str, str]
):
    """Test event streaming with error handling."""
    # Try to stream events for non-existent run
    fake_thread_id = "thread_507f1f77bcf86cd799439011"
    fake_run_id = "run_507f1f77bcf86cd799439012"

    response = test_client_with_db.get(
        f"/threads/{fake_thread_id}/runs/{fake_run_id}/events/stream",
        headers=test_headers,
    )
    assert response.status_code == 404


def test_event_streaming_content_format(
    test_client_with_db: TestClient, test_headers: dict[str, str]
):
    """Test that event streaming returns properly formatted content."""
    # Create a thread first
    thread_data = {"name": "Test Thread"}
    response = test_client_with_db.post(
        "/threads", json=thread_data, headers=test_headers
    )
    assert response.status_code == 201
    thread_id = response.json()["id"]

    # Create an assistant
    assistant_data = {
        "name": "Test Assistant",
        "description": "Test assistant",
        "tools": [],
        "system": "You are a test assistant",
    }
    response = test_client_with_db.post(
        "/assistants", json=assistant_data, headers=test_headers
    )
    assert response.status_code == 201
    assistant_id = response.json()["id"]

    # Create a run
    run_data = {"assistant_id": assistant_id, "instructions": "Test instructions"}
    response = test_client_with_db.post(
        f"/threads/{thread_id}/runs", json=run_data, headers=test_headers
    )
    assert response.status_code == 201
    run_id = response.json()["id"]

    # Start streaming events
    response = test_client_with_db.get(
        f"/threads/{thread_id}/runs/{run_id}/events/stream", headers=test_headers
    )
    assert response.status_code == 200

    # Read the stream content
    stream_content = response.content.decode("utf-8")

    # Should contain properly formatted SSE
    lines = stream_content.strip().split("\n")
    for line in lines:
        if line.startswith("data:"):
            # Should be valid JSON
            data_content = line[5:].strip()
            if data_content:
                try:
                    json.loads(data_content)
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in event stream: {data_content}")
