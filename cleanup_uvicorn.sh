#!/bin/bash

# Find the PID of the uvicorn process using port 8000 and kill it
pm2 restart fastapi
pid=$(lsof -t -i:8000 -sTCP:LISTEN)
if [ -n "$pid" ]; then
    echo "Killing process with PID $pid on port 8000..."
    kill -9 $pid
else
    echo "No process found on port 8000."
fi

# Reload the FastAPI app using PM2
echo "Reloading FastAPI app using PM2"
