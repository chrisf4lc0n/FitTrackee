#!/bin/bash
set -e

echo "==================================="
echo "FitTrackee Sink Folder Watcher"
echo "==================================="

# Setup sink folder structure
echo "Setting up sink folder structure..."
ftcli workouts sink_setup

# Process existing files if enabled
if [ "${PROCESS_EXISTING:-true}" = "true" ]; then
    echo "Processing existing files in sink folder..."
    ftcli workouts sink_process -v
fi

# Start the watcher
echo ""
echo "Starting sink folder watcher..."
echo "Watching: ${UPLOAD_FOLDER:-/usr/src/app/uploads}/sink/"
echo ""
echo "Folder structure:"
echo "  sink/{username}/           - Drop files here (default sport: cycling)"
echo "  sink/{username}/{sport_id}/ - Drop files here (specific sport)"
echo ""
echo "Press Ctrl+C to stop"
echo "==================================="

exec ftcli workouts sink_watch -v
