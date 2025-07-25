#!/bin/bash
set -e

pip install -e /app/TxGNN
exec uvicorn main:app --host 0.0.0.0 --port 8000