#!/bin/bash

# Find the PID of the uvicorn process using port 8001 and kill it
pm2 stop fastapi
sleep 2
pid=$(lsof -t -i:8001 -sTCP:LISTEN)
if [ -n "$pid" ]; then
    echo "Killing process with PID $pid on port 8001..."
    kill -9 $pid
    sleep 3
else
    echo "No process found on port 8001."
fi

pm2 restart fastapi

# Reload the FastAPI app using PM2
echo "Reloading FastAPI app using PM2"
