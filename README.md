
# SFTP Directory Synchronization Tool

This Python script synchronizes a local directory with a remote directory over SFTP. It automatically uploads or downloads files based on their modification times and sizes, and it monitors the local directory for changes.

## Features

- Synchronizes files from a local directory to a remote SFTP server.
- Downloads files from a remote directory to a local directory if they are newer.
- Monitors the local directory for file changes, creations, deletions, and moves.
- Uses `paramiko` for SFTP connections and `watchdog` for file system event handling.

## Prerequisites

Before running the script, make sure you have the following installed:

- Python 3.x
- Required libraries:
  ```bash
  pip install paramiko watchdog
  ```

## Configuration

You need to configure the following parameters in the script before running it:

- **SFTP Connection Details**
  - `hostname`: The address of your SFTP server.
  - `port`: The port for the SFTP connection (default is `22`).
  - `username`: Your SFTP username.
  - `password`: Your SFTP password.

- **Directories**
  - `local_directory`: Path to the local directory you want to sync.
  - `remote_directory`: Path to the remote directory on the SFTP server.

### Example

```python
hostname = "your.sftp.server"
port = 22
username = "your_username"
password = "your_password"

local_directory = "path/to/local/directory"
remote_directory = "/path/to/remote/directory"
```

## Usage

1. Ensure you have the necessary permissions for the directories you want to sync.
2. Run the script:

   ```bash
   python sync_script.py
   ```

3. The script will monitor the local directory for any changes. When files are modified, created, deleted, or moved, it will automatically sync those changes with the remote directory.

## Important Notes

- Ensure that your local directory path and remote directory path are correct.
- This script will create any necessary remote directories that do not exist.
- The script will continuously run until interrupted (e.g., with Ctrl+C).

