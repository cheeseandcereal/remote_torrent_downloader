import os
import sys
import pathlib
import shutil
import subprocess
import logging

from downloader.state import config
from downloader.state import state

log = logging.getLogger("download_obj")


class DownloadObject(object):
    infohash: str
    remote_path: str
    timestamp: int
    directory: bool
    temp_download_dir: str
    final_download_dir: str

    def __init__(self, infohash: str, remote_path: str, timestamp: int, directory: bool, temp_download_dir: str, final_download_dir: str):
        self.infohash = infohash
        self.remote_path = remote_path
        self.timestamp = timestamp
        self.directory = directory
        self.temp_download_dir = temp_download_dir
        self.final_download_dir = final_download_dir

    def download(self) -> None:
        log.info(f"Starting download for {self.remote_path}")
        sftp_opts = config.get_sftp_options()
        open_cmd = f"open -p {sftp_opts['port']} sftp://{sftp_opts['username']}:{sftp_opts['password']}@{sftp_opts['host']}"
        fetch_cmd = ""
        escaped_remote = self.remote_path.replace('"', '\\"')
        temp_path = pathlib.Path(self.temp_download_dir, pathlib.PurePosixPath(self.remote_path).name)
        escaped_temp = str(temp_path).replace('"', '\\"')
        if self.directory:
            temp_path.mkdir(parents=True, exist_ok=True)
            fetch_cmd = (
                f'mirror -c --parallel={sftp_opts["mirror_parallel"]} --use-pget-n={sftp_opts["mirror_conn"]} "{escaped_remote}" "{escaped_temp}"'
            )
        else:
            fetch_cmd = f'pget -c -n {sftp_opts["pget_conn"]} "{escaped_remote}" -o "{escaped_temp}"'
        # Run the lftp command, linking up its stdout/stderr with host's stdout and stderr
        subprocess.run(["lftp", "-c", f"{open_cmd} && {fetch_cmd}"], check=True, stdout=sys.stdout, stderr=sys.stderr)
        log.info(f"Finished downloading {self.remote_path}")
        # optional chmod stuff
        chmod_config = config.get_chmod_config()
        if chmod_config:
            file_mode = chmod_config["file"]
            folder_mode = chmod_config["folder"]
            log.debug(f"Performing post-download chmod. File mode: {file_mode} | Folder mode: {folder_mode}")
            if not self.directory:
                os.chmod(temp_path, file_mode)
            else:
                os.chmod(temp_path, folder_mode)
                for dirpath, dirnames, filenames in os.walk(temp_path):
                    for dname in dirnames:
                        os.chmod(os.path.join(dirpath, dname), folder_mode)
                    for fname in filenames:
                        os.chmod(os.path.join(dirpath, fname), file_mode)
        # move final data
        shutil.move(str(temp_path), self.final_download_dir)
        # If completed, stop watching this torrent
        state.remove_watching_torrent(self.infohash)
