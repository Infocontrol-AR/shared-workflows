"""
Vectorizer Smoke Tests

This script runs comprehensive smoke tests for the vectorizer service, including:
- Health check
- API stats
- Document vectorization process
- Qdrant collection creation and validation
- Qdrant points scrolling and content verification
- Qdrant collection cleanup

Usage:
    python vectorizer_smoke_tests.py [BASE_URL]

Arguments:
    BASE_URL: Optional base URL for the vectorizer service (default: http://10.197.0.30:8020)

Environment Variables:
    BASE_URL: Alternative way to specify the base URL

Examples:
    python vectorizer_smoke_tests.py
    python vectorizer_smoke_tests.py http://10.197.0.30:8020
    BASE_URL=http://prod.example.com python vectorizer_smoke_tests.py
"""

import requests
import json
import sys
import os
import random
import string

# Get base URL from command line argument or environment variable or default
if len(sys.argv) > 1:
    base_url = sys.argv[1]
else:
    base_url = os.environ.get("BASE_URL", "http://10.197.0.30:8020")

# Qdrant configuration
qdrant_url = (
    "https://76812338-c24f-4eb9-9b37-6a3c99eb379b.us-east-1-0.aws.cloud.qdrant.io:6333"
)
qdrant_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.8ElM5ohCbfZBjJPLoMSNz8S38YtnocllwiH5R29Fuqo"


def generate_supplier_id():
    """Generate a random supplier ID."""
    random_int = random.randint(1, 99999)
    random_str = "".join(random.choices(string.ascii_letters, k=5))
    return f"molnar_automated_Test_{random_int}_{random_str}"


def test_health_check():
    """Test the health check endpoint."""
    url = f"{base_url}/api/health"
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)

        # Test status code is 200
        assert response.status_code == 200

        # Validate response body
        json_data = response.json()

        assert json_data["status"] == "healthy"
        assert json_data["mode"] == "ULTRA_FAST"
        assert isinstance(json_data["timestamp"], (int, float))

        assert isinstance(json_data["components"], dict)
        assert json_data["components"]["gpu_available"] == False
        assert json_data["components"]["device"] == "cpu"
        assert json_data["components"]["tracking_enabled"] == False

    except AssertionError as e:
        return False
    except Exception as e:
        return False
    return True


def test_api_stats():
    """Test the API stats endpoint."""
    url = f"{base_url}/api/stats"
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)

        # Test status code is 200
        assert response.status_code == 200

        # Validate response body
        json_data = response.json()

        assert json_data["gpu_available"] == False
        assert json_data["device"] == "cpu"
        assert json_data["tracking_enabled"] == False

    except AssertionError as e:
        return False
    except Exception as e:
        return False
    return True


def test_process_vectorize(supplier_id):
    """Test the vectorize process endpoint."""
    url = f"{base_url}/api/process"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    payload = {
        "SupplierId": supplier_id,
        "Network": [""],
        "Documents": [
            {
                "DocumentId": "3825588D-1879-4EAD-82F2-19B11F2FF08A",
                "DocumentName": "Calor Gas Registration Certificate.pdf",
                "Identifier": "322/33/60",
                "DocumentUrl": "https://docprocessor1754468784.blob.core.windows.net/documents/00018325_UVDB_GlobalEnergy/documents/Calor%20Gas%20Registration%20Certificate.pdf",
            }
        ],
        "validation_level": "standard",
        "parallel_processing": True,
        "enable_cache": True,
        "clean_existing": False,
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["status"] == "completed"
        assert json_data["supplier_id"]
        assert json_data["documents_count"] == 1
        assert json_data["mode"] == "ULTRA_FAST_SYNC"
        assert json_data["result"]["processed_documents"] == 1
        assert (
            json_data["result"]["performance_metrics"]["mode"]
            == "BEAST_MODE_ULTRA_FAST"
        )
        assert "Processing completed successfully" in json_data["message"]
        assert json_data["result"]["failed_documents"] == 0
        assert json_data["result"]["total_vectors_created"] == 2
        assert json_data["processing_time"] > 0

        return json_data["supplier_id"]

    except AssertionError as e:
        return None
    except Exception as e:
        return None


def test_qdrant_collection(supplier_id):
    """Test Qdrant database collection creation check ."""
    url = f"{qdrant_url}/collections/{supplier_id}"
    headers = {"accept": "*/*", "api-key": qdrant_api_key}

    try:
        response = requests.get(url, headers=headers)
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["status"] == "ok"
        assert json_data["result"]["status"] == "green"
        assert json_data["result"]["optimizer_status"] == "ok"
        assert json_data["result"]["points_count"] == 2
        assert json_data["result"]["indexed_vectors_count"] >= 0
        assert json_data["result"]["segments_count"] >= 1
        assert json_data["time"] > 0

        return True

    except AssertionError as e:
        return False
    except Exception as e:
        return False


def test_qdrant_scroll(
    supplier_id, supplier_id_input, expected_document_id, expected_document_name
):
    """Test Qdrant database points / data from the vectorized file"""
    url = f"{qdrant_url}/collections/{supplier_id}/points/scroll"
    headers = {
        "accept": "application/json",
        "api-key": qdrant_api_key,
        "content-type": "application/json",
    }
    payload = {"limit": 2, "offset": None, "with_payload": True, "with_vector": False}

    try:
        response = requests.post(url, headers=headers, json=payload)
        assert response.status_code == 200

        json_data = response.json()
        points = json_data["result"]["points"]
        assert len(points) == 2

        # Validate each payload
        for i, point in enumerate(points):
            payload_data = point["payload"]

            # Document ID matches
            if payload_data["document_id"] != expected_document_id:
                raise AssertionError(f"Document ID mismatch for chunk {i}")

            # Batch processed is true
            if payload_data["batch_processed"] != True:
                raise AssertionError(f"Batch processed is not true for chunk {i}")

            # Chunk index is within valid range
            if not (0 <= payload_data["chunk_index"] < len(points)):
                raise AssertionError(f"Chunk index invalid for chunk {i}")

            # Page number is valid (> 0)
            if payload_data["page_number"] <= 0:
                raise AssertionError(f"Page number not positive for chunk {i}")

            # Collection name contains supplier_id
            if supplier_id_input not in payload_data["collection_name"]:
                raise AssertionError(
                    f"Collection name does not contain supplier_id for chunk {i}"
                )

            # Supplier ID matches (normalize trailing underscores)
            actual_supplier_id = payload_data["supplier_id"].rstrip("_")
            if actual_supplier_id != supplier_id_input:
                raise AssertionError(f"Supplier ID mismatch for chunk {i}")

            # Document name is valid
            if expected_document_name not in payload_data["document_name"]:
                raise AssertionError(f"Document name invalid for chunk {i}")

        # Summary checks
        all_doc_id = all(
            p["payload"]["document_id"] == expected_document_id for p in points
        )
        if not all_doc_id:
            raise AssertionError("Not all chunks share the same Document ID")

        all_supplier = all(
            p["payload"]["supplier_id"].rstrip("_") == supplier_id_input for p in points
        )
        if not all_supplier:
            raise AssertionError(
                "Not all chunks share the same Supplier ID (normalized)"
            )

        return True

    except AssertionError as e:
        print(f"Assertion failed in Qdrant Scroll: {e}")
        return False
    except Exception as e:
        print(f"Exception in Qdrant Scroll: {e}")
        return False


def test_qdrant_delete(supplier_id):
    """Test Qdrant collection deletion."""
    url = f"{qdrant_url}/collections/{supplier_id}"
    headers = {"accept": "*/*", "api-key": qdrant_api_key}

    try:
        response = requests.delete(url, headers=headers)
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["result"] == True
        assert json_data["status"] == "ok"

        return True

    except AssertionError as e:
        return False
    except Exception as e:
        return False


if __name__ == "__main__":
    health_passed = test_health_check()
    if health_passed:
        print("[PASS] / Health Check")
    else:
        print("[FAIL] / Health Check")

    stats_passed = test_api_stats()
    if stats_passed:
        print("[PASS] / API Stats")
    else:
        print("[FAIL] / API Stats")

    # Generate supplier ID and run vectorize process
    supplier_id_input = generate_supplier_id()
    print(f"Generated Supplier ID: {supplier_id_input}")
    supplier_id_response = test_process_vectorize(supplier_id_input)
    if supplier_id_response:
        print("[PASS] / Vectorize Process")
        supplier_id = supplier_id_response
        print(f"Response Supplier ID: {supplier_id}")
    else:
        print("[FAIL] / Vectorize Process")
        sys.exit(1)

    # Test Qdrant collection
    collection_passed = test_qdrant_collection(supplier_id)
    if collection_passed:
        print("[PASS] / Qdrant Collection Check")
    else:
        print("[FAIL] / Qdrant Collection Check")
        sys.exit(1)

    # Test Qdrant scroll points
    expected_document_id = "3825588D-1879-4EAD-82F2-19B11F2FF08A"
    expected_document_name = "Calor Gas Registration Certificate.pdf"
    scroll_passed = test_qdrant_scroll(
        supplier_id, supplier_id_input, expected_document_id, expected_document_name
    )
    if scroll_passed:
        print("[PASS] / Qdrant Points Scroll")
    else:
        print("[FAIL] / Qdrant Points Scroll")

    # Delete Qdrant collection
    delete_passed = test_qdrant_delete(supplier_id)
    if delete_passed:
        print("[PASS] / Qdrant Collection Delete")
    else:
        print("[FAIL] / Qdrant Collection Delete")

    if (
        health_passed
        and stats_passed
        and supplier_id_response
        and collection_passed
        and scroll_passed
        and delete_passed
    ):
        sys.exit(0)
    else:
        sys.exit(1)
