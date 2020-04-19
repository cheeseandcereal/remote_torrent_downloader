import os
import time
import pathlib

from downloader import deluge
from downloader.state import state
from downloader.state import config


def main() -> None:
    print("Checking for torrents in watch directories")
    for watch_dir in config.get_torrent_watch_dirs():
        final_dir = pathlib.Path(watch_dir["final_download_dir"])
        if not final_dir.is_dir() or not final_dir.is_absolute():
            raise Exception("provided final_download_dir is either not absolute or does not exist")
        temp_dir = pathlib.Path(watch_dir["temp_download_dir"])
        if not temp_dir.is_dir() or not temp_dir.is_absolute():
            raise Exception("provided temp_download_dir is either not absolute or does not exist")
        dir_path = pathlib.Path(watch_dir["directory"])
        if not dir_path.is_dir() or not dir_path.is_absolute():
            raise Exception("provided watch directory is either not absolute or does not exist")

        for f in os.listdir(dir_path):
            file_path = pathlib.Path(dir_path, f)
            if file_path.is_file():
                print(f"Adding {file_path} to deluge")
                # Add torrent file to remote deluge daemon
                infohash = deluge.add_torrent_by_file(str(file_path))
                # Set as watching this torrent with relevant params
                state.add_watching_torrent(infohash, str(temp_dir), str(final_dir))
                # Remove the processed torrent file
                os.remove(file_path)

    # Get currently watching torrents and try to download them if ready
    watching_torrents = state.get_watching_torrents()
    print("Checking deluge for completed torrents that should be downloaded")
    for obj in deluge.get_download_objects_for_watching_torrents(watching_torrents):
        try:
            obj.download()
        except Exception as e:
            print(f"Error: Failure to download {obj.remote_path}", e)

    print("Completed main loop")


if __name__ == "__main__":
    while True:
        try:
            main()
            time.sleep(15)
        except Exception as e:
            print(f"Warning: Uncaught unexpected exception", e)
