# rag_smoke_tests.py
# -*- coding: utf-8 -*-
"""
RAG Service Smoke Tests (Python)

Author: Radu Catalin Molnar (QA Automation)

This script performs end-to-end smoke checks against the Achilles RAG Service:
 1) Service info (/)
 2) Ollama health (/health-ollama)
  3) Fireworks/Qdrant health (/health-fireworks)
 4) RAG processing (/rag-service/?top_k=12) with dynamically generated SupplierId

Assertions include HTTP 200 and key fields/values as specified.

Run:
python .\rag_smoke_tests.py http://10.197.0.30:8040

Environment overrides (optional):
  EXPECTED_SERVICE, EXPECTED_VERSION, EXPECTED_STATUS_ROOT,
  EXPECTED_OLLAMA_BASE_URL, EXPECTED_OLLAMA_MODEL, EXPECTED_EMBED_DIM,
  FIREWORKS_QDRANT_URL

Dependencies:
  - requests (pip install requests)

Notes & TODOs:
  - If versions or provider configs change, set env variables to override expected values.
  - RAG call may take ~60–120s; timeout is set accordingly.
  - Adjust top_k in the query string if your collection is sparse.
"""

import os
import sys
import time
import json
import random
import string
from typing import Dict, Any

try:
    import requests
except ImportError as e:
    print(
        "[ERROR] Missing dependency 'requests'. Install via: pip install requests",
        file=sys.stderr,
    )
    raise

# -------- Configuration (with sensible defaults; override via ENV/CLI) -------- #
EXPECTED_SERVICE = os.getenv("EXPECTED_SERVICE", "Achilles RAG Service")
EXPECTED_VERSION = os.getenv("EXPECTED_VERSION", "3.0.0")
EXPECTED_STATUS_ROOT = os.getenv("EXPECTED_STATUS_ROOT", "running")

EXPECTED_OLLAMA_BASE_URL = os.getenv(
    "EXPECTED_OLLAMA_BASE_URL", "http://embedding-service-ollama:11434"
)
EXPECTED_OLLAMA_PROVIDER = os.getenv("EXPECTED_OLLAMA_PROVIDER", "ollama")
EXPECTED_OLLAMA_MODEL = os.getenv("EXPECTED_OLLAMA_MODEL", "bge-m3")
EXPECTED_EMBED_DIM = int(os.getenv("EXPECTED_EMBED_DIM", "1024"))

FIREWORKS_QDRANT_URL = os.getenv(
    "FIREWORKS_QDRANT_URL",
    "https://76812338-c24f-4eb9-9b37-6a3c99eb379b.us-east-1-0.aws.cloud.qdrant.io",
)
FIREWORKS_LLM_PROVIDER = os.getenv("FIREWORKS_LLM_PROVIDER", "fireworks")
FIREWORKS_EMBED_PROVIDER = os.getenv("FIREWORKS_EMBED_PROVIDER", "ollama")
FIREWORKS_OLLAMA_BASE = os.getenv("FIREWORKS_OLLAMA_BASE", EXPECTED_OLLAMA_BASE_URL)

# Request timeouts
CORE_TIMEOUT = float(os.getenv("CORE_TIMEOUT", "20"))  # for /, /health-* endpoints
RAG_TIMEOUT = float(os.getenv("RAG_TIMEOUT", "300"))  # rag-service can be slow

HEADERS_JSON = {"accept": "application/json"}

# -------- Utilities -------- #


def generate_supplier_id(prefix: str = "molnar_automated_Test") -> str:
    """Generate SupplierId like molnar_automated_Test_6745_bdjS
    - 4 random digits
    - 4 random letters (mixed case)
    """
    digits = random.randint(1000, 9999)
    letters = "".join(random.choices(string.ascii_letters, k=4))
    return f"{prefix}_{digits}_{letters}"


def get_json(url: str, timeout: float = CORE_TIMEOUT) -> Dict[str, Any]:
    resp = requests.get(url, headers=HEADERS_JSON, timeout=timeout)
    assert (
        resp.status_code == 200
    ), f"GET {url} expected 200, got {resp.status_code}, body={resp.text[:512]}"
    try:
        return resp.json()
    except json.JSONDecodeError:
        raise AssertionError(
            f"GET {url} did not return valid JSON. Raw body: {resp.text[:512]}"
        )


def post_json(
    url: str, payload: Dict[str, Any], timeout: float = RAG_TIMEOUT
) -> Dict[str, Any]:
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    assert (
        resp.status_code == 200
    ), f"POST {url} expected 200, got {resp.status_code}, body={resp.text[:1024]}"
    try:
        return resp.json()
    except json.JSONDecodeError:
        raise AssertionError(
            f"POST {url} did not return valid JSON. Raw body: {resp.text[:1024]}"
        )


# -------- Tests -------- #


def test_service_info(core_base: str) -> None:
    url = core_base.rstrip("/") + "/"
    data = get_json(url, timeout=CORE_TIMEOUT)

    # Basic field presence
    for key in ["service", "version", "status", "docs", "redoc", "endpoints"]:
        assert key in data, f"Missing key '{key}' in service info response"

    # Required assertions
    assert (
        data["service"] == EXPECTED_SERVICE
    ), f"Service name mismatch: expected '{EXPECTED_SERVICE}', got '{data['service']}'"
    assert (
        data["version"] == EXPECTED_VERSION
    ), f"Service version mismatch: expected '{EXPECTED_VERSION}', got '{data['version']}'"
    assert (
        data["status"] == EXPECTED_STATUS_ROOT
    ), f"Service status mismatch: expected '{EXPECTED_STATUS_ROOT}', got '{data['status']}'"

    # Endpoint presence sanity
    endpoints = data.get("endpoints", {})
    for ep in ["rag", "debug", "health_general", "health_ollama"]:
        assert ep in endpoints, f"Missing '{ep}' in endpoints"

    print("[PASS] / service info")


def test_health_ollama(core_base: str) -> None:
    url = core_base.rstrip("/") + "/health-ollama"
    data = get_json(url, timeout=CORE_TIMEOUT)

    # Required assertions
    assert (
        data.get("status") == "healthy"
    ), f"Ollama status expected 'healthy', got '{data.get('status')}'"
    assert (
        data.get("base_url") == EXPECTED_OLLAMA_BASE_URL
    ), f"base_url mismatch: expected '{EXPECTED_OLLAMA_BASE_URL}', got '{data.get('base_url')}'"
    assert (
        data.get("provider") == EXPECTED_OLLAMA_PROVIDER
    ), f"provider mismatch: expected '{EXPECTED_OLLAMA_PROVIDER}', got '{data.get('provider')}'"
    assert (
        data.get("embedding_model") == EXPECTED_OLLAMA_MODEL
    ), f"embedding_model mismatch: expected '{EXPECTED_OLLAMA_MODEL}', got '{data.get('embedding_model')}'"

    # Dimensions & latency checks
    emb_dim = data.get("embedding_dim")
    assert (
        emb_dim == EXPECTED_EMBED_DIM
    ), f"embedding_dim mismatch: expected {EXPECTED_EMBED_DIM}, got {emb_dim}"
    latency = data.get("latency_ms")
    assert (
        isinstance(latency, (int, float)) and latency >= 0
    ), f"latency_ms invalid: {latency}"

    # Details
    details = data.get("details", {})
    assert (
        details.get("http_status") == 200
    ), f"details.http_status expected 200, got {details.get('http_status')}"
    assert (
        details.get("embedding_sample_len") == emb_dim
    ), f"embedding_sample_len ({details.get('embedding_sample_len')}) != embedding_dim ({emb_dim})"

    print("[PASS] /health-ollama")


def test_health_fireworks(core_base: str) -> None:
    url = core_base.rstrip("/") + "/health-fireworks"
    data = get_json(url, timeout=CORE_TIMEOUT)

    assert (
        data.get("status") == "healthy"
    ), f"Fireworks health status expected 'healthy', got '{data.get('status')}'"
    assert (
        data.get("qdrant_url") == FIREWORKS_QDRANT_URL
    ), f"qdrant_url mismatch: expected '{FIREWORKS_QDRANT_URL}', got '{data.get('qdrant_url')}'"
    assert (
        data.get("llm_provider") == FIREWORKS_LLM_PROVIDER
    ), f"llm_provider mismatch: expected '{FIREWORKS_LLM_PROVIDER}', got '{data.get('llm_provider')}'"
    assert (
        data.get("embed_provider") == FIREWORKS_EMBED_PROVIDER
    ), f"embed_provider mismatch: expected '{FIREWORKS_EMBED_PROVIDER}', got '{data.get('embed_provider')}'"
    assert (
        data.get("ollama_base") == FIREWORKS_OLLAMA_BASE
    ), f"ollama_base mismatch: expected '{FIREWORKS_OLLAMA_BASE}', got '{data.get('ollama_base')}'"

    details = data.get("details", {})
    env_quiet = details.get("env_quiet")
    assert env_quiet is True, f"details.env_quiet expected True, got {env_quiet}"
    qdrant_points = details.get("qdrant_total_points")
    assert (
        isinstance(qdrant_points, int) and qdrant_points >= 0
    ), f"details.qdrant_total_points invalid: {qdrant_points}"

    print("[PASS] /health-fireworks")


def _build_rag_payload(supplier_id: str) -> Dict[str, Any]:
    return {
        "SupplierId": supplier_id,
        "Network": ["StartBANK"],
        "Tier": ["Registered"],
        "ContextualQuestions": [
            {
                "Identifier": "106/1310",
                "ContextualQuestion": "What is the organisation number of RONNIE KAARBY registered in Brønnøysundregistrene?",
                "AllowableResponseType": "SingleSelect",
                "RepeaterId": "RepeatId",
                "ContextResponseType": [
                    "979 850 689",
                    "978 850 689",
                    "979 580 689",
                    "979 850 698",
                ],
                "SystemResponseCode": ["A", "B", "C", "D"],
            }
        ],
        "Documents": [
            {
                "DocumentId": "1902341f-595b-425b-b4d1-1f353d44f30e",
                "DocumentName": "653824_Company certificate_20230001409450-1.pdf",
                "Identifier": "322/33/60",
                "DocumentUrl": "https://docprocessor1754468784.blob.core.windows.net/documents/00157761_StartBANK/documents/653824_Company%20certificate_20230001409450-1.pdf",
            }
        ],
        "validation_level": "standard",
        "parallel_processing": True,
        "enable_cache": True,
        "clean_existing": True,
    }


def test_rag_service(rag_base: str, supplier_id: str) -> None:
    url = rag_base.rstrip("/") + "/rag-service/?top_k=12"
    payload = _build_rag_payload(supplier_id)
    data = post_json(url, payload, timeout=RAG_TIMEOUT)

    # Top-level assertions
    assert (
        data.get("SupplierId") == supplier_id
    ), f"SupplierId mismatch: expected '{supplier_id}', got '{data.get('SupplierId')}'"
    assert data.get("status") in {
        "complete",
        "completed",
    }, f"RAG status expected 'complete', got '{data.get('status')}'"

    # Find the response for Identifier "106/1310"
    responses = data.get("SupplierResponses", [])
    assert (
        isinstance(responses, list) and len(responses) > 0
    ), "SupplierResponses is empty"

    target = None
    for r in responses:
        if r.get("Identifier") == "106/1310":
            target = r
            break
    assert target, "No SupplierResponses entry found for Identifier '106/1310'"

    # Field assertions per spec
    assert (
        target.get("Identifier") == "106/1310"
    ), "Identifier mismatch in SupplierResponses"
    # Accept both 'SingleSelect' from request and lowercase 'singleselect' in response
    allowable = target.get("AllowableResponseType")
    if allowable is not None:
        assert (
            str(allowable).lower() == "singleselect"
        ), f"AllowableResponseType expected 'singleselect', got '{allowable}'"
    expected_question = "What is the organisation number of RONNIE KAARBY registered in Brønnøysundregistrene?"
    question_text = target.get("QuestionText")
    if question_text is not None:
        assert question_text == expected_question, "QuestionText mismatch"
    repeater_id = target.get("RepeaterId")
    if repeater_id is not None:
        assert repeater_id == "RepeatId", "RepeaterId mismatch"
    ai_response = target.get("AiResponse")
    if ai_response is not None and ai_response != "Error":
        assert (
            ai_response == "979 850 689"
        ), f"AiResponse expected '979 850 689', got '{ai_response}'"

    decision = target.get("Decision", {})
    decision_label = decision.get("label")
    if decision_label is not None:
        assert (
            decision_label == "979 850 689"
        ), f"Decision.label expected '979 850 689', got '{decision_label}'"
    decision_code = decision.get("code")
    if decision_code is not None:
        assert (
            decision_code == "A"
        ), f"Decision.code expected 'A', got '{decision_code}'"

    # Optional sanity checks (do not fail test if absent)
    if "retrieved_k" in target:
        rk = target.get("retrieved_k")
        assert rk == 12, f"retrieved_k expected 12, got {rk}"

    timings = target.get("Timings", {})
    t_total_ms = timings.get("t_total_ms")
    if t_total_ms is not None:
        assert (
            isinstance(t_total_ms, (int, float)) and t_total_ms >= 0
        ), f"Timings.t_total_ms invalid: {t_total_ms}"

    usage = target.get("usage", {})
    total_tokens = usage.get("total_tokens")
    if total_tokens is not None:
        assert (
            isinstance(total_tokens, int) and total_tokens >= 0
        ), f"usage.total_tokens invalid: {total_tokens}"

    print("[PASS] /rag-service processing")


# -------- Runner -------- #


def run_all(core_base: str, rag_base: str, supplier_id: str) -> None:
    print(f"Running RAG smoke tests against {core_base}")
    start = time.time()

    test_service_info(core_base)
    test_health_ollama(core_base)
    test_health_fireworks(core_base)
    test_rag_service(rag_base, supplier_id)

    elapsed = time.time() - start
    print(f"\nALL TESTS PASSED in {elapsed:.2f}s")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Achilles RAG Service smoke tests")
    parser.add_argument(
        "base_url",
        help="Base URL for the service",
    )
    parser.add_argument(
        "--supplier-id",
        help="Fixed SupplierId to use instead of generating random",
    )
    args = parser.parse_args()

    supplier_id = (
        args.supplier_id if args.supplier_id else "molnar_automated_Test_6745_bdjS"
    )

    try:
        run_all(
            core_base=args.base_url, rag_base=args.base_url, supplier_id=supplier_id
        )
    except AssertionError as ae:
        print(f"\n[FAIL] {ae}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as re:
        print(f"\n[FAIL] Network/Request error: {re}", file=sys.stderr)
        sys.exit(2)
