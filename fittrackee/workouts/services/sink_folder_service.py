"""
Sink Folder Watcher Service

This service monitors a designated folder for new workout files (FIT, GPX, TCX,
KML, KMZ) and automatically imports them into FitTrackee.

Folder structure:
    UPLOAD_FOLDER/sink/
        └── {username}/           # Subfolder per user
            ├── {sport_id}/       # Optional: subfolder per sport
            │   ├── workout1.fit
            │   └── workout2.gpx
            └── workout3.tcx      # Uses default sport (1 = cycling)

After processing:
    - Successfully processed files are moved to UPLOAD_FOLDER/sink/processed/
    - Failed files are moved to UPLOAD_FOLDER/sink/error/
"""

import os
import shutil
import time
from datetime import datetime, timezone
from io import BytesIO
from logging import Logger, getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from watchdog.observers import Observer

from fittrackee import db
from fittrackee.files import get_absolute_file_path
from fittrackee.users.models import User
from fittrackee.workouts.constants import WORKOUT_ALLOWED_EXTENSIONS
from fittrackee.workouts.models import Sport

if TYPE_CHECKING:
    from flask import Flask

DEFAULT_SPORT_ID = 1  # Cycling
SINK_FOLDER_NAME = "sink"
PROCESSED_FOLDER_NAME = "processed"
ERROR_FOLDER_NAME = "error"

appLog = getLogger("fittrackee_sink_folder")


class WorkoutFileHandler(FileSystemEventHandler):
    """Handler for file system events in the sink folder."""

    def __init__(self, app: "Flask", logger: Logger):
        self.app = app
        self.logger = logger
        super().__init__()

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = event.src_path

        # Only process workout files
        extension = Path(file_path).suffix.lower().lstrip(".")
        if extension not in WORKOUT_ALLOWED_EXTENSIONS:
            return

        # Wait a moment for file to be fully written
        time.sleep(0.5)

        with self.app.app_context():
            self._process_file(file_path)

    def _process_file(self, file_path: str) -> None:
        """Process a single workout file from the sink folder."""
        from fittrackee.workouts.services.workouts_from_file_creation_service import (
            WorkoutsFromFileCreationService,
        )

        file_path_obj = Path(file_path)
        filename = file_path_obj.name

        self.logger.info(f"Processing file: {file_path}")

        # Parse the path to get username and sport
        try:
            user, sport_id = self._parse_file_path(file_path)
        except Exception as e:
            self.logger.error(f"Failed to parse file path: {e}")
            self._move_to_error(file_path, str(e))
            return

        if not user:
            self.logger.error(f"Could not determine user for file: {file_path}")
            self._move_to_error(file_path, "Could not determine user")
            return

        # Verify sport exists
        sport = Sport.query.filter_by(id=sport_id).first()
        if not sport:
            self.logger.error(f"Sport ID {sport_id} not found")
            self._move_to_error(file_path, f"Sport ID {sport_id} not found")
            return

        # Check if user is active
        if user.suspended_at:
            self.logger.error(f"User {user.username} is suspended")
            self._move_to_error(file_path, f"User {user.username} is suspended")
            return

        # Read file content
        try:
            with open(file_path, "rb") as f:
                file_content = BytesIO(f.read())
        except Exception as e:
            self.logger.error(f"Failed to read file: {e}")
            self._move_to_error(file_path, str(e))
            return

        # Create a file-like object that mimics werkzeug FileStorage
        class FileStorageMock:
            def __init__(self, stream: BytesIO, filename: str):
                self.stream = stream
                self.filename = filename

            def getvalue(self) -> bytes:
                self.stream.seek(0)
                return self.stream.read()

            def save(self, dst: str) -> None:
                self.stream.seek(0)
                with open(dst, "wb") as f:
                    f.write(self.stream.read())

        file_storage = FileStorageMock(file_content, filename)

        # Prepare workout data
        workouts_data = {
            "sport_id": sport_id,
            "title": None,
            "description": None,
            "notes": f"Imported from sink folder",
            "equipment_ids": None,
        }

        # Process the workout
        try:
            service = WorkoutsFromFileCreationService(
                auth_user=user,
                workouts_data=workouts_data,
                file=file_storage,  # type: ignore
            )
            workouts, processing_output = service.process()

            if workouts:
                workout = workouts[0]
                self.logger.info(
                    f"Successfully imported workout for user {user.username}: "
                    f"{workout.short_id} ({workout.sport.label})"
                )
                self._move_to_processed(file_path, user.username)
            else:
                error_msg = processing_output.get("errored_workouts", {})
                self.logger.error(f"Failed to create workout: {error_msg}")
                self._move_to_error(file_path, str(error_msg))

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error processing workout: {e}")
            self._move_to_error(file_path, str(e))

    def _parse_file_path(self, file_path: str) -> tuple[Optional[User], int]:
        """
        Parse the file path to extract username and sport ID.

        Expected structure:
            .../sink/{username}/file.fit -> default sport
            .../sink/{username}/{sport_id}/file.fit -> specific sport
        """
        file_path_obj = Path(file_path)
        parts = file_path_obj.parts

        # Find the 'sink' folder in the path
        try:
            sink_index = parts.index(SINK_FOLDER_NAME)
        except ValueError:
            raise ValueError(f"'{SINK_FOLDER_NAME}' not found in path")

        remaining_parts = parts[sink_index + 1:]

        if len(remaining_parts) < 2:
            raise ValueError(
                f"Invalid path structure. Expected: sink/username/file or "
                f"sink/username/sport_id/file"
            )

        # First part after sink is always username
        username = remaining_parts[0]

        # Check if there's a sport_id subfolder
        if len(remaining_parts) == 2:
            # sink/username/file.fit
            sport_id = DEFAULT_SPORT_ID
        elif len(remaining_parts) == 3:
            # sink/username/sport_id/file.fit
            try:
                sport_id = int(remaining_parts[1])
            except ValueError:
                # Not a number, treat as part of filename structure
                sport_id = DEFAULT_SPORT_ID
        else:
            sport_id = DEFAULT_SPORT_ID

        # Get user from database
        user = User.query.filter_by(username=username).first()

        return user, sport_id

    def _get_sink_folder(self) -> str:
        """Get the base sink folder path."""
        upload_folder = self.app.config["UPLOAD_FOLDER"]
        return os.path.join(upload_folder, SINK_FOLDER_NAME)

    def _move_to_processed(self, file_path: str, username: str) -> None:
        """Move successfully processed file to the processed folder."""
        self._move_file(
            file_path,
            PROCESSED_FOLDER_NAME,
            username
        )

    def _move_to_error(self, file_path: str, error_msg: str) -> None:
        """Move failed file to the error folder."""
        # Extract username from path if possible
        try:
            parts = Path(file_path).parts
            sink_index = parts.index(SINK_FOLDER_NAME)
            username = parts[sink_index + 1] if len(parts) > sink_index + 1 else "unknown"
        except (ValueError, IndexError):
            username = "unknown"

        self._move_file(file_path, ERROR_FOLDER_NAME, username)

        # Write error message to a companion file
        error_file = file_path + ".error"
        try:
            timestamp = datetime.now(tz=timezone.utc).isoformat()
            error_content = f"Timestamp: {timestamp}\nError: {error_msg}\n"

            # Get destination error file path
            sink_folder = self._get_sink_folder()
            dest_folder = os.path.join(sink_folder, ERROR_FOLDER_NAME, username)
            os.makedirs(dest_folder, exist_ok=True)

            filename = Path(file_path).name
            error_dest = os.path.join(dest_folder, filename + ".error")

            with open(error_dest, "w") as f:
                f.write(error_content)
        except Exception as e:
            self.logger.warning(f"Failed to write error file: {e}")

    def _move_file(self, file_path: str, dest_type: str, username: str) -> None:
        """Move a file to the specified destination folder."""
        sink_folder = self._get_sink_folder()
        dest_folder = os.path.join(sink_folder, dest_type, username)

        # Create destination folder if it doesn't exist
        os.makedirs(dest_folder, exist_ok=True)

        # Generate unique filename if file already exists
        filename = Path(file_path).name
        dest_path = os.path.join(dest_folder, filename)

        if os.path.exists(dest_path):
            # Add timestamp to filename
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(dest_folder, filename)

        try:
            shutil.move(file_path, dest_path)
            self.logger.debug(f"Moved {file_path} to {dest_path}")
        except Exception as e:
            self.logger.error(f"Failed to move file {file_path}: {e}")


class SinkFolderWatcher:
    """
    Service to watch the sink folder for new workout files.
    """

    def __init__(self, app: "Flask", logger: Optional[Logger] = None):
        self.app = app
        self.logger = logger or appLog
        self.observer: Optional[Observer] = None

    def get_sink_folder_path(self) -> str:
        """Get the path to the sink folder."""
        upload_folder = self.app.config["UPLOAD_FOLDER"]
        return os.path.join(upload_folder, SINK_FOLDER_NAME)

    def setup_folders(self) -> None:
        """Create the sink folder structure if it doesn't exist."""
        sink_folder = self.get_sink_folder_path()

        # Create main sink folder
        os.makedirs(sink_folder, exist_ok=True)

        # Create processed and error folders
        os.makedirs(os.path.join(sink_folder, PROCESSED_FOLDER_NAME), exist_ok=True)
        os.makedirs(os.path.join(sink_folder, ERROR_FOLDER_NAME), exist_ok=True)

        self.logger.info(f"Sink folder initialized at: {sink_folder}")
        self.logger.info(
            f"Structure:\n"
            f"  {sink_folder}/\n"
            f"    ├── {{username}}/           # Place files here per user\n"
            f"    │   └── {{sport_id}}/       # Optional: subfolder for sport\n"
            f"    ├── {PROCESSED_FOLDER_NAME}/            # Successfully processed files\n"
            f"    └── {ERROR_FOLDER_NAME}/                 # Failed files"
        )

    def start(self, recursive: bool = True) -> None:
        """Start watching the sink folder."""
        sink_folder = self.get_sink_folder_path()

        # Ensure folders exist
        self.setup_folders()

        # Create the event handler and observer
        event_handler = WorkoutFileHandler(self.app, self.logger)
        self.observer = Observer()
        self.observer.schedule(event_handler, sink_folder, recursive=recursive)

        self.logger.info(f"Starting sink folder watcher on: {sink_folder}")
        self.observer.start()

    def stop(self) -> None:
        """Stop watching the sink folder."""
        if self.observer:
            self.logger.info("Stopping sink folder watcher...")
            self.observer.stop()
            self.observer.join()
            self.observer = None

    def run_forever(self) -> None:
        """Run the watcher until interrupted."""
        try:
            self.start()
            self.logger.info("Sink folder watcher is running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            self.stop()

    def process_existing_files(self) -> int:
        """
        Process any existing files in the sink folder.

        This is useful for processing files that were added while the
        watcher was not running.

        Returns the number of files processed.
        """
        sink_folder = self.get_sink_folder_path()
        handler = WorkoutFileHandler(self.app, self.logger)
        count = 0

        with self.app.app_context():
            for root, dirs, files in os.walk(sink_folder):
                # Skip processed and error folders
                dirs[:] = [
                    d for d in dirs
                    if d not in [PROCESSED_FOLDER_NAME, ERROR_FOLDER_NAME]
                ]

                for filename in files:
                    extension = Path(filename).suffix.lower().lstrip(".")
                    if extension in WORKOUT_ALLOWED_EXTENSIONS:
                        file_path = os.path.join(root, filename)
                        self.logger.info(f"Processing existing file: {file_path}")
                        handler._process_file(file_path)
                        count += 1

        return count
