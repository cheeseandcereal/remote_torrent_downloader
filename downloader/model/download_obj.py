from typing import List
import re
import os
import sys
import pathlib
import shutil
import subprocess
import logging

from downloader.state import config
from downloader.state import state

log = logging.getLogger("download_obj")


_rar_digit_part_regex = re.compile(r"^\.\d{1,3}$")


def _get_unzip_cmd(zip_path: str, extract_dir: str) -> List[str]:
    return ["unzip", "-o", zip_path, "-d", extract_dir]


def _get_unrar_cmd(rar_path: str, extract_dir: str) -> List[str]:
    return ["unrar", "x", "-o+", "-y", rar_path, extract_dir]


class DownloadObject(object):
    infohash: str
    remote_path: str
    timestamp: int
    directory: bool
    temp_download_dir: str
    final_download_dir: str
    auto_extract: bool

    def __init__(
        self, infohash: str, remote_path: str, timestamp: int, directory: bool, temp_download_dir: str, final_download_dir: str, auto_extract: bool
    ):
        self.infohash = infohash
        self.remote_path = remote_path
        self.timestamp = timestamp
        self.directory = directory
        self.temp_download_dir = temp_download_dir
        self.final_download_dir = final_download_dir
        self.auto_extract = auto_extract

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
        if self.auto_extract:
            self._extract_if_necessary(temp_path)
        # optional chmod stuff
        self._chmod_if_necessary(temp_path)
        # move final data
        shutil.move(str(temp_path), self.final_download_dir)
        # If completed, stop watching this torrent
        state.remove_watching_torrent(self.infohash)

    def _extract_if_necessary(self, temp_path: pathlib.Path) -> None:
        if not self.directory:
            if temp_path.suffix == ".rar" or temp_path.suffix == ".zip":
                # Create directory for extraction if single file
                temp_rename_path = pathlib.Path(str(temp_path) + ".temp")
                temp_path.rename(temp_rename_path)
                temp_path.mkdir()
                temp_rename_path.rename(pathlib.Path(temp_path, temp_path.name))
                self.directory = True
            return

        extract_commands = []
        # Walk through all dirs recursively to look for files to extract
        for dirpath, _, filenames in os.walk(temp_path):
            for fname in filenames:
                curr_file = pathlib.Path(dirpath, fname)
                if curr_file.suffix.lower() == ".zip":
                    extract_commands.append(_get_unzip_cmd(str(curr_file), dirpath))
                elif curr_file.suffix.lower() == ".rar":
                    first_part = True
                    if len(curr_file.suffixes) > 1:
                        # Rar files can be split into parts; If this is a multipart rar, we don't want to extract anything except the first part
                        # https://support.winzip.com/hc/en-us/articles/115011771188-Split-RAR-files-what-they-look-like-and-how-they-work-with-WinZip
                        part_suffix = curr_file.suffixes[-2].lower()
                        if part_suffix.startswith(".part"):
                            if part_suffix != ".part1" and part_suffix != ".part01" and part_suffix != ".part001":
                                first_part = False
                        elif _rar_digit_part_regex.match(part_suffix):
                            if part_suffix != ".1" and part_suffix != ".01" and part_suffix != ".001":
                                first_part = False
                    if first_part:
                        extract_commands.append(_get_unrar_cmd(str(curr_file), dirpath))
        # Run actual extract commands
        if extract_commands:
            log.info(f"Extracting local files from {self.remote_path}")
        for cmd in extract_commands:
            log.debug(f"running extract command: {cmd}")
            subprocess.run(cmd, check=True, stderr=sys.stderr)

    def _chmod_if_necessary(self, temp_path: pathlib.Path) -> None:
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
