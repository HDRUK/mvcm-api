#!/bin/bash

# Start Flask app with uvicorn --workers=2 --threads=4
uvicorn --workers 2 --host 0.0.0.0 --port 80 app:app
