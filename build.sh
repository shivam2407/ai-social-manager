#!/usr/bin/env bash
set -o errexit

# Build React frontend
cd frontend
npm install
npm run build
cd ..

# Install Python dependencies
cd langgraph-api
pip install .
