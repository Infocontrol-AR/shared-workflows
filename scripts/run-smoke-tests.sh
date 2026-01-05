#!/usr/bin/env bash

# Fail on error, undefined vars, and pipe failures
set -euo pipefail

REPO_NAME="$1"
CORE_BASE_URL="http://${SSH_IP}:${RAG_SERVICE_PORT:-8040}"
RAG_BASE_URL="http://${SSH_IP}:${RAG_SERVICE_PORT:-8040}"
VECTORIZER_BASE_URL="http://${SSH_IP}:${VECTORIZER_PORT:-8020}"

case "$REPO_NAME" in
  ai-middleware-v3)
    echo "Testing Middleware"
    ;;
  ai-rag-service-v3)
    echo "Testing RAG Service"
    python ./rag_smoke_tests.py --core-base "$CORE_BASE_URL" --rag-base "$RAG_BASE_URL"
    ;;
  ai-vectorizer-v3)  
    echo "Testing Vectorizer"
    python vectorizer_smoke_tests.py "$VECTORIZER_BASE_URL"
    ;;
  *)
    echo "Not testing anything, because repo name $REPO_NAME not recognized"
    ;;
esac
echo "Smoke tests completed."