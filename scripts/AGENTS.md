# Server scripts

This directory contains the local Docker workflow scripts:

- `start.sh` and `stop.sh` are used on macOS and Linux.
- `start.ps1` and `stop.ps1` are used on Windows PowerShell.

The start scripts build the Docker image and start the Compose service in the background. The stop scripts stop and remove the container while preserving the named SQLite volume.

Run them from any directory. They resolve the project root relative to the script location.
