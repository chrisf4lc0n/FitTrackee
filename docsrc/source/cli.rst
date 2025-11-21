Command line interface
######################

A command line interface (CLI) is available to manage database, OAuth2 tokens, users and workouts archive uploads.

.. code-block:: bash

    $ ftcli
    Usage: ftcli [OPTIONS] COMMAND [ARGS]...

      FitTrackee Command Line Interface

    Options:
      --help  Show this message and exit.

    Commands:
      db        Manage database.
      oauth2    Manage OAuth2 tokens.
      users     Manage users.
      workouts  Manage workouts.


Database
~~~~~~~~

``ftcli db drop``
"""""""""""""""""
.. versionadded:: 0.6.5

Empty database and delete uploaded files, only on development environments.


``ftcli db upgrade``
""""""""""""""""""""
.. versionadded:: 0.6.5

Apply migrations.


OAuth2
~~~~~~

``ftcli oauth2 clean``
""""""""""""""""""""""
.. versionadded:: 0.7.0

Remove tokens expired for more than provided number of days

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Options
     - Description
   * - ``--days INTEGER``
     - Number of days.



Users
~~~~~

``ftcli users clean_archives``
""""""""""""""""""""""""""""""
.. versionadded:: 0.7.13

Delete export requests and related archives created more than provided number of days.

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Options
     - Description
   * - ``--days INTEGER``
     - Number of days.


``ftcli users clean_tokens``
""""""""""""""""""""""""""""
.. versionadded:: 0.7.0

Remove blacklisted tokens expired for more than provided number of days.

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Options
     - Description
   * - ``--days INTEGER``
     - Number of days.


``ftcli users create``
""""""""""""""""""""""
.. versionadded:: 0.7.15
.. versionchanged:: 0.8.4  User preference for interface language is added.
.. versionchanged:: 0.9.0  Add option for user role.
.. versionchanged:: 0.9.4  User preference for timezone is added.

Create a user account.

.. note::
  - the newly created account is already active.
  - the CLI allows to create users when registration is disabled.


.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Arguments/options
     - Description
   * - ``USERNAME TEXT``
     - Username.
   * - ``--email TEXT``
     - User email (mandatory).
   * - ``--password TEXT``
     - User password (if not provided, a random password is generated).
   * - ``--lang TEXT``
     - User preference for interface language (two-letter code, ISO 639-1). If not provided or not supported, it falls back to English ('en').
   * - ``--tz TEXT``
     - User preference for timezone. If not provided or not supported, it falls back to 'Europe/Paris'.
   * - ``--role [owner|admin|moderator|user]``
     - User role (default: 'user').


``ftcli users export_archive``
"""""""""""""""""""""""""""""""
.. versionadded:: 0.10.0

Process a given queued user data export.

Can be used if redis is not set (no dramatiq workers running).

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Options
     - Description
   * - ``--id TEXT``
     - Id of task to process.


``ftcli users export_archives``
"""""""""""""""""""""""""""""""
.. versionadded:: 0.7.13

Process incomplete user export requests.

Can be used if redis is not set (no dramatiq workers running).

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Options
     - Description
   * - ``--max INTEGER``
     - Maximum number of export requests to process.


``ftcli users update``
""""""""""""""""""""""
.. versionadded:: 0.6.5
.. versionchanged:: 0.9.0  Add ``--set-role`` option. ``--set-admin`` is now deprecated.
.. versionchanged:: 1.0.0  Remove ``--set-admin`` option.

Modify a user account (role, active status, email and password).

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Arguments/options
     - Description
   * - ``USERNAME``
     - Username.
   * - ``--set-role [owner|admin|moderator|user]``
     - Set user role (when setting 'moderator', 'admin' and 'owner' role, it also activates user account if not active).
   * - ``--activate``
     - Activate user account.
   * - ``--reset-password``
     - Reset user password (a new password will be displayed).
   * - ``--update-email TEXT``
     - New user email.


Workouts
~~~~~~~~

``ftcli workouts archive_upload``
"""""""""""""""""""""""""""""""""
.. versionadded:: 0.10.0

Process a given queued workouts archive upload.

Can be used if redis is not set (no dramatiq workers running).

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Options
     - Description
   * - ``--id TEXT``
     - Id of task to process.


``ftcli workouts archive_uploads``
""""""""""""""""""""""""""""""""""
.. versionadded:: 0.10.0

Process workouts archive uploads if queued tasks exist (progress = 0 and not aborted/errored).

Can be used if redis is not set (no dramatiq workers running).

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Options
     - Description
   * - ``--max INTEGER``
     - Maximum number of workouts archive to process.


``ftcli workouts refresh``
""""""""""""""""""""""""""
.. versionadded:: 0.12.0
.. versionchanged:: 1.0.0  Add ``--add-missing-geometry`` option.

Refresh workouts by recalculating data and fetching weather data if provider is set and workout does not have weather data.

Before executing the command, it is recommended to back up of all data (database and upload directory) in case a large number of workouts are refreshed.

.. warning::
   If a weather data provider is defined and the ``--with-weather`` option is provided, the rate limit may be reached, resulting in API rate limit errors when a large number of workouts is refreshed.

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Options
     - Description
   * - ``--sport-id INTEGER``
     - sport id
   * - ``--from TEXT``
     - start date (format: ``%Y-%m-%d``)
   * - ``--to TEXT``
     - end date (format: ``%Y-%m-%d``)
   * - ``--per-page INTEGER``
     - number of workouts per page (default: 10)
   * - ``--page INTEGER``
     - page number (default: 1)
   * - ``--order TEXT``
     - workout date order: 'asc' or 'desc' (default: 'asc')
   * - ``--user TEXT``
     - username of workouts owner
   * - ``--extension TEXT``
     - workout file extension (valid values are: tcx, kmz, gpx, kml, fit)
   * - ``--with-weather``
     - enable weather data collection if weather provider is set and workout has no weather data. WARNING: depending on subscription, the rate limit can be reached, leading to errors and preventing weather data being collected during next uploads until the limit is reset (default: disabled)
   * - ``--add-missing-geometry``
     - if provided, it refreshes only workouts without geometry in database to add geometry and points. This option is provided to update workouts created before v1.x and will be removed in a future version when all workouts must have geometry.
   * - ``-v, --verbose``
     - Enable verbose output log (default: disabled)


``ftcli workouts sink_setup``
"""""""""""""""""""""""""""""
.. versionadded:: 1.1.0

Create the sink folder structure for automatic workout file import.

This creates the necessary folders:

- ``UPLOAD_FOLDER/sink/`` - Base folder for incoming workout files
- ``UPLOAD_FOLDER/sink/processed/`` - Successfully imported files
- ``UPLOAD_FOLDER/sink/error/`` - Failed files with error details


``ftcli workouts sink_watch``
"""""""""""""""""""""""""""""
.. versionadded:: 1.1.0

Watch the sink folder for new workout files and automatically import them.

The sink folder structure is:

- ``UPLOAD_FOLDER/sink/{username}/file.fit`` - uses default sport (cycling)
- ``UPLOAD_FOLDER/sink/{username}/{sport_id}/file.fit`` - uses specific sport

Processed files are moved to ``sink/processed/{username}/``.
Failed files are moved to ``sink/error/{username}/`` with a ``.error`` file containing details.

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Options
     - Description
   * - ``--process-existing``
     - Process existing files in the sink folder before starting the watcher.
   * - ``-v, --verbose``
     - Enable verbose output log (default: disabled)


``ftcli workouts sink_process``
"""""""""""""""""""""""""""""""
.. versionadded:: 1.1.0

Process existing files in the sink folder (one-time batch processing).

This command processes all workout files currently in the sink folder and then exits.
Use this for batch processing without running the continuous watcher.

.. cssclass:: table-bordered
.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Options
     - Description
   * - ``-v, --verbose``
     - Enable verbose output log (default: disabled)


Sink Folder Usage
"""""""""""""""""

The sink folder feature allows automatic import of workout files by simply dropping them into a designated folder.

**Setup:**

1. Create the folder structure:

   .. code-block:: bash

      $ ftcli workouts sink_setup

2. Create a folder for each user (username must match an existing FitTrackee user):

   .. code-block:: bash

      $ mkdir -p /path/to/uploads/sink/admin
      $ mkdir -p /path/to/uploads/sink/admin/5  # Optional: for running (sport_id=5)

3. Start the watcher:

   .. code-block:: bash

      $ ftcli workouts sink_watch --process-existing -v

4. Drop workout files into the appropriate folder:

   .. code-block:: bash

      # Cycling workout (default sport)
      $ cp morning_ride.fit /path/to/uploads/sink/admin/

      # Running workout
      $ cp evening_run.gpx /path/to/uploads/sink/admin/5/

**Docker Deployment:**

To run the sink folder watcher in Docker, uncomment the ``fittrackee-sink`` service in ``docker-compose.yml``.

**Sport IDs:**

Common sport IDs (check your database for the complete list):

- 1 = Cycling (Sport)
- 2 = Cycling (Transport)
- 3 = Hiking
- 4 = Mountain Biking
- 5 = Running
- 6 = Walking