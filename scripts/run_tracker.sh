#!/bin/bash

# Set environment variables
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="/Users/Mario/Documents/bird_tracker"

# Change to script directory
cd /Users/Mario/Documents/bird_tracker

# Activate virtual environment
source /Users/Mario/Documents/bird_tracker/venv/bin/activate

# Run the script
/Users/Mario/Documents/bird_tracker/venv/bin/python3 /Users/Mario/Documents/bird_tracker/bird_tracker.py

# Log the completion
echo "Bird tracker completed at $(date)" >> /Users/Mario/Documents/bird_tracker/cron.log