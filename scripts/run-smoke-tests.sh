#!/usr/bin/env bash

# Fail on error, undefined vars, and pipe failures
set -euo pipefail

REPO_NAME="$1"

CORE_BASE_URL="http://${SSH_IP}:${RAG_SERVICE_PORT:-8040}"
RAG_BASE_URL="http://${SSH_IP}:${RAG_SERVICE_PORT:-8040}"
VECTORIZER_BASE_URL="http://${SSH_IP}:${VECTORIZER_PORT:-8020}"

test_rag_service() {
  echo "Testing RAG Service"
  python ./rag_smoke_tests.py --core-base "$CORE_BASE_URL" --rag-base "$RAG_BASE_URL"
}

test_vectorizer() {
  echo "Testing Vectorizer"
  python vectorizer_smoke_tests.py "$VECTORIZER_BASE_URL"
}

test_middleware() {
  echo "Testing Middleware"
  echo "..."
}

case "$REPO_NAME" in
  ai-middleware-v3)
    test_middleware
    test_rag_service
    test_vectorizer
    ;;
  ai-rag-service-v3)
    test_rag_service
    ;;
  ai-vectorizer-v3)
    test_vectorizer
    ;;
  *)
    echo "Not testing anything, because repo name $REPO_NAME is not recognized"
    ;;
esac

echo "Smoke tests completed."
