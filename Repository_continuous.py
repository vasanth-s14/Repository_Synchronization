import os
import paramiko
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def get_remote_file_info(sftp, remote_file):
    """Get the modification time and size of a remote file."""
    try:
        attr = sftp.stat(remote_file)
        return attr.st_mtime, attr.st_size
    except IOError:
        return None, None

def sync_local_to_remote(sftp, local_file, remote_file):
    """Synchronize a local file to the remote server if it is newer."""
    remote_mtime, remote_size = get_remote_file_info(sftp, remote_file)
    local_mtime = os.path.getmtime(local_file)
    local_size = os.path.getsize(local_file)

    if remote_mtime is None or local_mtime > remote_mtime or (local_mtime == remote_mtime and local_size != remote_size):
        sftp.put(local_file, remote_file)
        sftp.utime(remote_file, (local_mtime, local_mtime))
        print(f"Uploaded: {local_file} -> {remote_file}")

def sync_remote_to_local(sftp, local_file, remote_file):
    """Synchronize a remote file to the local machine if it is newer."""
    remote_mtime, remote_size = get_remote_file_info(sftp, remote_file)
    if not os.path.exists(local_file):
        sftp.get(remote_file, local_file)
        os.utime(local_file, (remote_mtime, remote_mtime))
        print(f"Downloaded: {remote_file} -> {local_file}")
    else:
        local_mtime = os.path.getmtime(local_file)
        local_size = os.path.getsize(local_file)

        if remote_mtime > local_mtime or (remote_mtime == local_mtime and remote_size != local_size):
            sftp.get(remote_file, local_file)
            os.utime(local_file, (remote_mtime, remote_mtime))
            print(f"Updated: {remote_file} -> {local_file}")

def sync_directories(sftp, local_dir, remote_dir):
    """Synchronize directories in both directions."""
    # Synchronize local to remote
    for root, dirs, files in os.walk(local_dir):
        relative_path = os.path.relpath(root, local_dir)
        remote_path = os.path.join(remote_dir, relative_path).replace("\\", "/")

        try:
            sftp.chdir(remote_path)  
        except IOError:
            sftp.mkdir(remote_path)
            sftp.chdir(remote_path)

        for file in files:
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_path, file).replace("\\", "/")
            sync_local_to_remote(sftp, local_file, remote_file)

    # Synchronize remote to local
    for remote_root, dirs, files in sftp_walk(sftp, remote_dir):
        relative_path = os.path.relpath(remote_root, remote_dir)
        local_path = os.path.join(local_dir, relative_path)

        if not os.path.exists(local_path):
            os.makedirs(local_path)

        for file in files:
            remote_file = os.path.join(remote_root, file).replace("\\", "/")
            local_file = os.path.join(local_path, file)
            sync_remote_to_local(sftp, local_file, remote_file)

def sftp_walk(sftp, remote_path):
    """Walk through remote directories recursively."""
    file_list = []
    dir_list = []
    try:
        for entry in sftp.listdir_attr(remote_path):
            mode = entry.st_mode
            if paramiko.S_ISDIR(mode):
                dir_list.append(entry.filename)
            else:
                file_list.append(entry.filename)
        yield remote_path, dir_list, file_list

        for directory in dir_list:
            new_path = os.path.join(remote_path, directory).replace("\\", "/")
            for x in sftp_walk(sftp, new_path):
                yield x
    except IOError:
        return

class SyncEventHandler(FileSystemEventHandler):
    """Event handler to sync files on change."""
    def __init__(self, sftp, local_directory, remote_directory):
        self.sftp = sftp
        self.local_directory = local_directory
        self.remote_directory = remote_directory

    def on_modified(self, event):
        """Triggered when a file or directory is modified."""
        print(f"Modified: {event.src_path}")
        sync_directories(self.sftp, self.local_directory, self.remote_directory)

    def on_created(self, event):
        """Triggered when a file or directory is created."""
        print(f"Created: {event.src_path}")
        sync_directories(self.sftp, self.local_directory, self.remote_directory)

    def on_deleted(self, event):
        """Triggered when a file or directory is deleted."""
        print(f"Deleted: {event.src_path}")
        sync_directories(self.sftp, self.local_directory, self.remote_directory)

    def on_moved(self, event):
        """Triggered when a file or directory is moved."""
        print(f"Moved: {event.src_path}")
        sync_directories(self.sftp, self.local_directory, self.remote_directory)

if __name__ == "__main__":
    # SFTP connection details
    hostname = "your.sftp.server"
    port = 22
    username = "your_username"
    password = "your_password"

    local_directory = "path/to/local/directory"
    remote_directory = "/path/to/remote/directory"

    # Establishing the SFTP connection
    transport = paramiko.Transport((hostname, port))
    transport.connect(username=username, password=password)

    sftp = paramiko.SFTPClient.from_transport(transport)

    event_handler = SyncEventHandler(sftp, local_directory, remote_directory)
    observer = Observer()
    observer.schedule(event_handler, path=local_directory, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    sftp.close()
    transport.close()
