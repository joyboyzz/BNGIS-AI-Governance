#!/bin/bash
# BNGIS — run script
# Installs deps if needed, then starts the server on port 8000
cd "$(dirname "$0")"
pip3 install -q -r requirements.txt
echo "Starting BNGIS on http://0.0.0.0:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000
