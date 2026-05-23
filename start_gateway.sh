#!/bin/bash
# Start LLM Gateway V3

cd "$(dirname "$0")/llm_gatewayV3" || exit 1

echo "Starting LLM Gateway V3 on port 8101..."
echo "Press Ctrl+C to stop"
echo ""

./run.sh
