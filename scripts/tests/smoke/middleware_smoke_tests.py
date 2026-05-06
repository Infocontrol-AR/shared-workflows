"""
Middleware Smoke Tests

This script runs smoke tests for the middleware service root endpoint.

Usage:
    python middleware_smoke_tests.py [BASE_URL]

Arguments:
    BASE_URL: Optional base URL for the middleware service (default: http://10.197.0.30:8000)

Environment Variables:
    BASE_URL: Alternative way to specify the base URL

Examples:
    python middleware_smoke_tests.py
    python middleware_smoke_tests.py http://10.197.0.30:8000
    BASE_URL=http://prod.example.com python middleware_smoke_tests.py
"""

import requests
import json
import sys
import os
import random
import time

# Get base URL from command line argument or environment variable or default
if len(sys.argv) > 1:
    base_url = sys.argv[1]
else:
    base_url = os.environ.get("BASE_URL", "http://10.197.0.30:8000")

# Global variables to store batch_id, source_id, document_id, document_name
batch_id = None
source_id = None
document_id = None
document_name = None


def test_root_endpoint():
    """Test the root endpoint that redirects to documentation."""
    url = f"{base_url}/"
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=30)

        # Test status code is 200
        assert response.status_code == 200

        # Validate response body
        json_data = response.json()

        # Assert keys and values as per Postman test
        assert json_data.get("message") == "Achilles Middleware Test API"
        assert json_data.get("docs") == "/docs"
        assert json_data.get("health") == "/health"

        # Validate all required keys exist
        required_keys = ["message", "docs", "health"]
        for key in required_keys:
            assert key in json_data, f"Missing required key: {key}"

        print(f"[PASS] Root endpoint: {json_data['message']}")
        return True

    except AssertionError as e:
        print(f"[FAIL] Root endpoint assertion: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Root endpoint exception: {e}")
        return False


def test_health_endpoint():
    """Test the health endpoint."""
    url = f"{base_url}/health"
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=30)

        # Test status code is 200
        assert response.status_code == 200

        # Validate response body
        json_data = response.json()

        # Assert keys and values as per Postman test
        assert json_data.get("status") == "healthy"
        assert json_data.get("service") == "achilles-middleware-api"
        assert (
            json_data.get("kafka_topic_input") == "DocumentManagement_Batch_Processing"
        )

        # Assert timestamp exists and is positive
        assert "timestamp" in json_data
        assert isinstance(json_data["timestamp"], (int, float))
        assert json_data["timestamp"] > 0

        # Validate all required keys exist
        required_keys = ["status", "service", "kafka_topic_input", "timestamp"]
        for key in required_keys:
            assert key in json_data, f"Missing required key: {key}"

        print(f"[PASS] Health endpoint: {json_data['status']}")
        return True

    except AssertionError as e:
        print(f"[FAIL] Health endpoint assertion: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Health endpoint exception: {e}")
        return False


def validate_json_schema(data, schema, path="root"):
    """Recursively validate JSON data against a schema."""
    if not isinstance(schema, dict):
        return True

    if "type" in schema:
        expected_type = schema["type"]
        if expected_type == "string" and not isinstance(data, str):
            raise AssertionError(f"{path}: Expected string, got {type(data)}")
        elif expected_type == "boolean" and not isinstance(data, bool):
            raise AssertionError(f"{path}: Expected boolean, got {type(data)}")
        elif expected_type == "array" and not isinstance(data, list):
            raise AssertionError(f"{path}: Expected array, got {type(data)}")
        elif expected_type == "object" and not isinstance(data, dict):
            raise AssertionError(f"{path}: Expected object, got {type(data)}")

    if "properties" in schema and isinstance(data, dict):
        for prop_name, prop_schema in schema["properties"].items():
            if prop_name not in data:
                if prop_schema.get("required", False):
                    raise AssertionError(
                        f"{path}: Missing required property '{prop_name}'"
                    )
                continue
            validate_json_schema(data[prop_name], prop_schema, f"{path}.{prop_name}")

    if "items" in schema and isinstance(data, list):
        for i, item in enumerate(data):
            validate_json_schema(item, schema["items"], f"{path}[{i}]")

    if "enum" in schema and data not in schema["enum"]:
        raise AssertionError(
            f"{path}: Value '{data}' not in allowed values {schema['enum']}"
        )

    if "pattern" in schema:
        import re

        if not re.match(schema["pattern"], data):
            raise AssertionError(
                f"{path}: Value '{data}' does not match pattern {schema['pattern']}"
            )

    if (
        "minLength" in schema
        and isinstance(data, str)
        and len(data) < schema["minLength"]
    ):
        raise AssertionError(
            f"{path}: String length {len(data)} < minimum {schema['minLength']}"
        )

    return True


def test_example_payload_endpoint():
    """Test the example payload endpoint with comprehensive schema validation."""
    url = f"{base_url}/api/v1/test/example-payload"
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=30)

        # Test status code is 200
        assert response.status_code == 200

        # Validate response body
        json_data = response.json()

        # Define comprehensive JSON schema
        schema = {
            "type": "object",
            "properties": {
                "SourceSystem": {"type": "string", "enum": ["MyA"]},
                "SourceId": {"type": "string", "enum": ["00312637"]},
                "B2CToken": {
                    "type": "string",
                    "pattern": r"^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$",
                    "minLength": 20,
                },
                "Questions": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "Identifier": {"type": "string", "enum": ["106/1310"]},
                            "ContextualQuestion": {
                                "type": "string",
                                "pattern": r".*organisation number.*",
                            },
                            "AllowableResponseType": {
                                "type": "string",
                                "enum": ["SingleSelect"],
                            },
                            "RepeaterId": {"type": "string"},
                            "ContextResponseType": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 4,
                            },
                            "SystemResponseCode": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 4,
                            },
                        },
                        "required": [
                            "Identifier",
                            "ContextualQuestion",
                            "AllowableResponseType",
                            "RepeaterId",
                            "ContextResponseType",
                            "SystemResponseCode",
                        ],
                    },
                },
                "Documents": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "DocumentId": {
                                "type": "string",
                                "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                            },
                            "DocumentName": {"type": "string", "minLength": 1},
                            "Identifier": {"type": "string", "enum": ["322/33/60"]},
                            "DocumentLocation": {
                                "type": "string",
                                "pattern": r"^https://.*",
                            },
                        },
                        "required": [
                            "DocumentId",
                            "DocumentName",
                            "Identifier",
                            "DocumentLocation",
                        ],
                    },
                },
                "validation_level": {"type": "string", "enum": ["standard"]},
                "parallel_processing": {"type": "boolean"},
                "enable_cache": {"type": "boolean"},
                "clean_existing": {"type": "boolean"},
            },
            "required": [
                "SourceSystem",
                "SourceId",
                "B2CToken",
                "Questions",
                "Documents",
                "validation_level",
                "parallel_processing",
                "enable_cache",
                "clean_existing",
            ],
        }

        # Validate against schema
        validate_json_schema(json_data, schema)

        # Additional cross-field validations
        questions = json_data["Questions"]
        documents = json_data["Documents"]

        # Ensure ContextResponseType and SystemResponseCode arrays have same length
        for i, question in enumerate(questions):
            if len(question["ContextResponseType"]) != len(
                question["SystemResponseCode"]
            ):
                raise AssertionError(
                    f"Question {i}: ContextResponseType and SystemResponseCode arrays must have same length"
                )

        print(f"[PASS] Example payload endpoint: Schema validation successful")
        return True

    except AssertionError as e:
        print(f"[FAIL] Example payload endpoint schema validation: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Example payload endpoint exception: {e}")
        return False


def test_send_message_to_middleware():
    """Test sending message to middleware with 1 document and 1 question."""
    url = f"{base_url}/api/v1/test/send-message"
    headers = {"Content-Type": "application/json"}

    try:
        # Generate a random integer between 1 and 99999
        random_int = random.randint(1, 99999)

        # Generate a random string of up to 5 letters
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        random_str = "".join(random.choice(letters) for _ in range(5))

        # Combine everything
        global source_id
        source_id = f"molnar_automated_Test_{random_int}_{random_str}"

        # Create payload with 1 document and 1 question
        payload = {
            "B2CToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY3RpdmVPcmdhbmlzYXRpb25JZCI6IjAwMzEyNjM3Iiwic3ViIjoidGVzdC11c2VyIiwibmFtZSI6IlRlc3QgVXNlciIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsImlhdCI6MTcwMDAwMDAwMCwiZXhwIjoxOTAwMDAwMDAwfQ.3rX9YKq8xZv4j5N2mB7pL6wQ8tR1uV0oY3cE4fH6iK8",
            "Documents": [
                {
                    "DocumentId": "e28877ca-3798-4efa-84bc-47718312b448",
                    "DocumentLocation": "https://docprocessor1754468784.blob.core.windows.net/documents/00157761_StartBANK/documents/653824_Company%20certificate_20230001409450-1.pdf",
                    "DocumentName": "Financial Statement HYOSUNG Heavy Industries.pdf",
                    "Identifier": "322/33/60",
                }
            ],
            "Questions": [
                {
                    "AllowableResponseType": "SingleSelect",
                    "ContextResponseType": [
                        "979 850 689",
                        "978 850 689",
                        "979 580 689",
                        "979 850 698",
                    ],
                    "ContextualQuestion": "What is the organisation number of RONNIE KAARBY registered in Brønnøysundregistrene?",
                    "Identifier": "106/1310",
                    "RepeaterId": "This is a reapeater id",
                    "SystemResponseCode": ["A", "B", "C", "D"],
                }
            ],
            "SourceId": source_id,
            "SourceSystem": "MyA",
            "clean_existing": True,
            "enable_cache": True,
            "parallel_processing": True,
            "validation_level": "standard",
        }

        # Simulate parsing the request body to set variables
        if payload.get("Documents") and len(payload["Documents"]) > 0:
            global document_id
            global document_name
            document_id = payload["Documents"][0]["DocumentId"]
            document_name = payload["Documents"][0]["DocumentName"]
        else:
            print("No Documents found in payload.")

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        # Print response body
        try:
            json_data = response.json()
            # print("Response body:", json.dumps(json_data, indent=2))
        except ValueError:
            # print("Response body:", response.text)
            json_data = None

        # Test status code is 202
        assert response.status_code == 202

        # Assert status
        assert json_data.get("status") == "accepted"

        # Assert message
        assert json_data.get("message") == "Message successfully published to Kafka"

        # Assert topic
        assert json_data.get("topic") == "DocumentManagement_Batch_Processing"

        # Store batch_id
        global batch_id
        batch_id = json_data.get("batch_id")
        assert isinstance(batch_id, str) and batch_id

        # Optional: Log for debugging
        print(f"Stored batch_id: {batch_id}")

        # Validate batch_id exists and is not empty
        assert json_data["batch_id"]

        # JSON Schema for MessageResponse
        schema = {
            "$id": "MessageResponse",
            "type": "object",
            "title": "Respuesta al enviar un mensaje",
            "required": ["status", "message", "supplier_id", "batch_id", "topic"],
            "additionalProperties": False,
            "properties": {
                "status": {"type": "string", "minLength": 1},
                "message": {"type": "string", "minLength": 1},
                "supplier_id": {"type": "string", "minLength": 1},
                "batch_id": {"type": "string", "minLength": 1},
                "topic": {"type": "string", "minLength": 1},
            },
        }

        # Validate against schema
        validate_json_schema(json_data, schema)

        # Simple sanity checks
        required_keys = ["status", "message", "supplier_id", "batch_id", "topic"]
        for key in required_keys:
            assert key in json_data, f"Falta el campo: {key}"
            assert isinstance(json_data[key], str), f"El campo {key} debe ser string"
            assert len(json_data[key]) > 0, f"El campo {key} no debe estar vacío"

        print(f"[PASS] Send message to middleware: {json_data['message']}")
        return True

    except AssertionError as e:
        print(f"[FAIL] Send message to middleware assertion: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Send message to middleware exception: {e}")
        return False


def test_check_batch_id_processed():
    """Test checking that the batch ID was processed and wait for the process."""
    url = f"{base_url}/api/v1/results/list/batch-ids?limit=50&offset=0"
    headers = {"accept": "application/json"}

    try:
        print("Waiting for kafka to respond...")
        time.sleep(40)
        print("40 seconds passed")

        response = requests.get(url, headers=headers, timeout=30)

        # Test status code is 200
        assert response.status_code == 200

        # Validate response body
        json_data = response.json()

        # Assert that the response has the property "batch_ids"
        assert "batch_ids" in json_data

        # Assert that batch_ids is not empty
        assert len(json_data["batch_ids"]) > 0, "batch_ids should not be empty"

        # Assert that batch_ids contains the expected batch_id
        assert (
            batch_id in json_data["batch_ids"]
        ), f"Expected batch_id {batch_id} not found"

        print(
            f"[PASS] Check batch ID processed: Found {len(json_data['batch_ids'])} batch IDs including {batch_id}"
        )
        return True

    except AssertionError as e:
        print(f"[FAIL] Check batch ID processed assertion: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Check batch ID processed exception: {e}")
        return False


def test_check_qdrant_collection():
    """Test checking that the collection was created in the Qdrant database."""
    collection_name = f"supplier_{source_id}_documents"
    url = f"https://76812338-c24f-4eb9-9b37-6a3c99eb379b.us-east-1-0.aws.cloud.qdrant.io:6333/collections/{collection_name}"
    headers = {
        "accept": "*/*",
        "api-key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.8ElM5ohCbfZBjJPLoMSNz8S38YtnocllwiH5R29Fuqo",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)

        # Validate response body
        json_data = response.json()

        # Assert top-level status is "ok"
        assert json_data.get("status") == "ok"

        # Assert result.status is "green"
        assert json_data.get("result", {}).get("status") == "green"

        # Assert optimizer_status is "ok"
        assert json_data.get("result", {}).get("optimizer_status") == "ok"

        # Assert points_count is 5
        assert json_data.get("result", {}).get("points_count") == 5

        # Optional extra checks
        result = json_data.get("result", {})
        if "indexed_vectors_count" in result:
            assert result["indexed_vectors_count"] >= 0
        if "segments_count" in result:
            assert result["segments_count"] >= 1
        if "time" in json_data:
            assert isinstance(json_data["time"], (int, float)) and json_data["time"] > 0

        print(
            f"[PASS] Check Qdrant collection: {collection_name} is ready with {json_data['result']['points_count']} points"
        )
        return True

    except AssertionError as e:
        print(f"[FAIL] Check Qdrant collection assertion: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Check Qdrant collection exception: {e}")
        return False


def test_check_batch_details():
    """Test checking the batch details."""
    url = f"{base_url}/api/v1/results/{batch_id}?debug=true"
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=30)

        # Test status code is 200
        assert response.status_code == 200

        # Validate response body
        json_data = response.json()

        # Validate response fields for SourceSystem, SourceId, BatchId, BatchStatus
        assert json_data.get("SourceSystem") == "MyA"
        assert json_data.get("SourceId") == source_id
        assert json_data.get("BatchId") == batch_id
        assert json_data.get("BatchStatus") == "AIE"

        # Validate RepeatorGroupGuid schema (optional)
        target_identifier = "106/1310"
        question = None
        for q in json_data.get("Questions", []):
            if q.get("Identifier") == target_identifier:
                question = q
                break
        assert question is not None, f"Question '{target_identifier}' should exist"

        repeator_guid = (
            question.get("RepeatorGroupGuid")
            or question.get("RepeaterGroupGuid")
            or (question.get("Metadata") or {}).get("RepeatorGroupGuid")
        )

        # If present, validate GUID format; if absent, allow absence
        import re

        guid_regex = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )
        if repeator_guid is not None and repeator_guid != "":
            assert re.match(
                guid_regex, repeator_guid, re.IGNORECASE
            ), "RepeatorGroupGuid should be a valid GUID"
        # Otherwise, it's optional

        # Validate Sources (ContextUsed) from RAG path
        sources = (
            json_data.get("_internal", {})
            .get("rag_response", {})
            .get("chunks", [{}])[0]
            .get("SupplierResponses", [{}])[0]
            .get("ContextUsed", [])
        )

        assert isinstance(sources, list), "ContextUsed should be an array"

        guid_regex_payload = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )

        for i, src in enumerate(sources):
            assert isinstance(src, dict), f"ContextUsed[{i}] should be an object"

            # payload_id
            assert "payload_id" in src, f"ContextUsed[{i}] should have payload_id"
            assert (
                isinstance(src["payload_id"], str) and src["payload_id"]
            ), f"ContextUsed[{i}].payload_id should be a non-empty string"
            # Optional GUID check
            # assert re.match(guid_regex_payload, src["payload_id"], re.IGNORECASE), f"ContextUsed[{i}].payload_id should be GUID"

            # retrieval_score
            assert (
                "retrieval_score" in src
            ), f"ContextUsed[{i}] should have retrieval_score"
            assert isinstance(
                src["retrieval_score"], (int, float)
            ), f"ContextUsed[{i}].retrieval_score should be a number"
            assert (
                0 <= src["retrieval_score"] <= 1
            ), f"ContextUsed[{i}].retrieval_score should be between 0 and 1"

            # document_id
            assert "document_id" in src, f"ContextUsed[{i}] should have document_id"
            assert (
                isinstance(src["document_id"], str) and src["document_id"]
            ), f"ContextUsed[{i}].document_id should be a non-empty string"
            assert (
                src["document_id"] == document_id
            ), f"ContextUsed[{i}].document_id should equal expected"

            # document_name
            assert "document_name" in src, f"ContextUsed[{i}] should have document_name"
            assert (
                isinstance(src["document_name"], str) and src["document_name"]
            ), f"ContextUsed[{i}].document_name should be a non-empty string"
            assert (
                src["document_name"] == document_name
            ), f"ContextUsed[{i}].document_name should equal expected"

            # chunk_index
            assert "chunk_index" in src, f"ContextUsed[{i}] should have chunk_index"
            assert isinstance(
                src["chunk_index"], (int, float)
            ), f"ContextUsed[{i}].chunk_index should be a number"
            assert (
                src["chunk_index"] >= 0
            ), f"ContextUsed[{i}].chunk_index should be >= 0"

            # page_number
            assert "page_number" in src, f"ContextUsed[{i}] should have page_number"
            assert isinstance(
                src["page_number"], (int, float)
            ), f"ContextUsed[{i}].page_number should be a number"
            assert (
                src["page_number"] >= 1
            ), f"ContextUsed[{i}].page_number should be >= 1"

            # section
            assert "section" in src, f"ContextUsed[{i}] should have section"
            assert isinstance(
                src["section"], str
            ), f"ContextUsed[{i}].section should be a string"
            assert (
                src["section"] == "REGISTERUTSKRIFT FRA ENHETSREGISTERET"
            ), f"ContextUsed[{i}].section should match expected"

            # document_used_type
            assert (
                "document_used_type" in src
            ), f"ContextUsed[{i}] should have document_used_type"
            assert isinstance(
                src["document_used_type"], str
            ), f"ContextUsed[{i}].document_used_type should be a string"
            assert (
                src["document_used_type"] == "REGISTERUTSKRIFT"
            ), f"ContextUsed[{i}].document_used_type should match expected"

            # text
            assert "text" in src, f"ContextUsed[{i}] should have text"
            assert (
                isinstance(src["text"], str) and src["text"]
            ), f"ContextUsed[{i}].text should be a non-empty string"

        # Debug output
        if sources:
            print(f"DEBUG ContextUsed (first item): {sources[0]}")

        print(f"[PASS] Check batch details: Batch {batch_id} processed successfully")
        return True

    except AssertionError as e:
        print(f"[FAIL] Check batch details assertion: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Check batch details exception: {e}")
        return False


def test_delete_batch_result():
    """Test deleting batch result from cache."""
    url = f"{base_url}/api/v1/results/{batch_id}"
    headers = {"accept": "application/json"}

    try:
        response = requests.delete(url, headers=headers, timeout=30)

        # Test status code is 200
        assert response.status_code == 200

        # Validate response body
        json_data = response.json()

        # Extract batch_id (though it's in URL, response might have it)
        response_batch_id = json_data.get("batch_id")

        # Assert message matches the expected format
        expected_message = f"Result for {batch_id} has been removed from cache"
        assert json_data.get("message") == expected_message

        # Optional: Validate status
        assert json_data.get("status") == "deleted"

        print(f"[PASS] Delete batch result: {json_data['message']}")
        return True

    except AssertionError as e:
        print(f"[FAIL] Delete batch result assertion: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Delete batch result exception: {e}")
        return False


def test_delete_qdrant_collection():
    """Test deleting the Qdrant collection."""
    collection_name = f"supplier_{source_id}_documents"
    url = f"https://76812338-c24f-4eb9-9b37-6a3c99eb379b.us-east-1-0.aws.cloud.qdrant.io:6333/collections/{collection_name}"
    headers = {
        "accept": "*/*",
        "api-key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.8ElM5ohCbfZBjJPLoMSNz8S38YtnocllwiH5R29Fuqo",
    }

    try:
        response = requests.delete(url, headers=headers, timeout=30)

        # Test status code is 200
        assert response.status_code == 200

        # Validate response body
        json_data = response.json()

        # Validate result and status
        assert json_data.get("result") is True
        assert json_data.get("status") == "ok"

        print(
            f"[PASS] Delete Qdrant collection: {collection_name} deleted successfully"
        )
        return True

    except AssertionError as e:
        print(f"[FAIL] Delete Qdrant collection assertion: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Delete Qdrant collection exception: {e}")
        return False


def test_clear_cache():
    """Test clearing the results cache."""
    url = f"{base_url}/api/v1/results/cache/clear"
    headers = {"accept": "application/json"}

    try:
        response = requests.delete(url, headers=headers, timeout=30)

        # Test status code is 200
        assert response.status_code == 200

        # Validate response body
        json_data = response.json()

        # Assert that 'results_removed' is >= 0
        assert json_data.get("results_removed", 0) >= 0

        # Optional: Validate status and message
        assert json_data.get("status") == "cleared"
        assert json_data.get("message") == "Cache cleared successfully"

        print(
            f"[PASS] Clear cache: {json_data['message']}, removed {json_data['results_removed']} results"
        )
        return True

    except AssertionError as e:
        print(f"[FAIL] Clear cache assertion: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Clear cache exception: {e}")
        return False


if __name__ == "__main__":
    print(f"Running middleware smoke tests against {base_url}")

    root_passed = test_root_endpoint()
    health_passed = test_health_endpoint()
    payload_passed = test_example_payload_endpoint()
    send_passed = test_send_message_to_middleware()
    list_passed = test_check_batch_id_processed()
    qdrant_passed = test_check_qdrant_collection()
    batch_details_passed = test_check_batch_details()
    delete_batch_passed = test_delete_batch_result()
    delete_qdrant_passed = test_delete_qdrant_collection()
    clear_cache_passed = test_clear_cache()

    print("\nResults:")
    if (
        root_passed
        and health_passed
        and payload_passed
        and send_passed
        and list_passed
        and qdrant_passed
        and batch_details_passed
        and delete_batch_passed
        and delete_qdrant_passed
        and clear_cache_passed
    ):
        print("✅ All middleware smoke tests passed!")
        sys.exit(0)
    else:
        print("❌ Some middleware smoke tests failed!")
        sys.exit(1)
