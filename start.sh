#!/bin/bash
# Navigate to your project directory

# Activate virtual environment
source venv/bin/activate

# Start Uvicorn server
exec uvicorn main:app --reload --host 0.0.0.0 --port 8787

exec uvicorn main:app --reload --host 0.0.0.0 --port 8111


cd /Users/yuguan/Desktop/Code/MY/python-payroll-services && source venv/bin/activate && exec uvicorn main:app --reload --host 0.0.0.0 --port 8111