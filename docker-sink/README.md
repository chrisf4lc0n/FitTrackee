# FitTrackee Sink Folder Auto-Import

Automatically import workout files (FIT, GPX, TCX, KML, KMZ) into FitTrackee by simply dropping them into a folder.

## Features

- **Continuous file watching** - Automatically detects new files
- **User-based organization** - Separate folders per user
- **Sport selection** - Use subfolders for different sport types
- **Automatic cleanup** - Processed files moved to `processed/`, failed to `error/`
- **Docker ready** - Easy deployment with docker-compose

## Quick Start

### 1. Clone and configure

```bash
cd docker-sink
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start the stack

```bash
docker compose up -d
```

### 3. Create a user in FitTrackee

Access FitTrackee at http://localhost:5000 and create a user account.

### 4. Set up sink folders

```bash
# Create folder for your user (replace 'admin' with your username)
mkdir -p ./data/uploads/sink/admin

# Optional: Create sport-specific folders
mkdir -p ./data/uploads/sink/admin/5  # For running
```

### 5. Drop workout files

```bash
# Copy a cycling workout (uses default sport)
cp morning_ride.fit ./data/uploads/sink/admin/

# Copy a running workout (sport_id=5)
cp evening_run.gpx ./data/uploads/sink/admin/5/
```

Files are automatically imported and moved to `./data/uploads/sink/processed/admin/`

## Folder Structure

```
./data/uploads/sink/
├── {username}/              # Create one folder per user
│   ├── workout1.fit         # Default sport (cycling)
│   ├── workout2.gpx
│   └── {sport_id}/          # Optional: specific sport
│       ├── run.fit
│       └── run2.tcx
├── processed/               # Successfully imported files
│   └── {username}/
└── error/                   # Failed files with .error details
    └── {username}/
```

## Sport IDs

Common sport IDs (check your database for the complete list):

| ID | Sport |
|----|-------|
| 1 | Cycling (Sport) |
| 2 | Cycling (Transport) |
| 3 | Hiking |
| 4 | Mountain Biking |
| 5 | Running |
| 6 | Walking |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROCESS_EXISTING` | Process existing files on startup | `true` |
| `UPLOAD_FOLDER` | Base upload folder path | `/usr/src/app/uploads` |
| `APP_SECRET_KEY` | Application secret key | (required) |
| `DATABASE_URL` | PostgreSQL connection URL | (required) |

See `.env.example` for all available options.

## Adding to Existing FitTrackee

If you already have FitTrackee running, add this service to your existing `docker-compose.yml`:

```yaml
  fittrackee-sink:
    container_name: fittrackee-sink
    env_file:
      - .env
    image: fittrackee/fittrackee:v1.0.3
    volumes:
      - ${HOST_UPLOAD_DIR:-./data/uploads}:/usr/src/app/uploads
      - ${HOST_LOG_DIR:-./data/logs}:/usr/src/app/logs
      - ${HOST_STATICMAP_CACHE_DIR:-./data/staticmap_cache}:/usr/src/app/.staticmap_cache
    post_start:
      - command: chown -R fittrackee:fittrackee /usr/src/app/uploads /usr/src/app/logs /usr/src/app/.staticmap_cache
        user: root
    command: "ftcli workouts sink_watch --process-existing -v"
    depends_on:
      fittrackee:
        condition: service_healthy
    networks:
      - internal_network
    restart: unless-stopped
```

## CLI Commands

The sink folder feature provides these CLI commands:

```bash
# Start continuous watcher
ftcli workouts sink_watch --process-existing -v

# One-time batch processing
ftcli workouts sink_process -v

# Setup folder structure only
ftcli workouts sink_setup
```

## Logs

View sink watcher logs:

```bash
docker compose logs -f fittrackee-sink
```

## Troubleshooting

### Files not being processed

1. Check that the username folder matches an existing FitTrackee user
2. Verify the user is not suspended
3. Check logs: `docker compose logs fittrackee-sink`

### Files moved to error folder

Check the `.error` file next to the failed file for details:

```bash
cat ./data/uploads/sink/error/admin/workout.fit.error
```

### Permission issues

Ensure the upload folder is writable:

```bash
chmod -R 777 ./data/uploads
```

## Building Locally

To build the sink folder image locally:

```bash
# From the FitTrackee root directory
docker build -t fittrackee-sink -f docker-sink/Dockerfile .
```

## License

AGPL-3.0 - Same as FitTrackee
