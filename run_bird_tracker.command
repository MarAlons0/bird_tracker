#!/bin/bash
cd /Users/Mario/Documents/bird_tracker
source venv/bin/activate
echo "Running bird tracker..."
python3 bird_tracker.py
if [ $? -ne 0 ]; then
    echo "Error running program"
    echo "Press Enter to close this window"
    read
else
    echo "Program completed successfully"
    echo "Press Enter to close this window"
    read
fi