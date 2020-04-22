import os
import time
import pathlib
import logging

from downloader import deluge
from downloader.state import state
from downloader.state import config

log = logging.getLogger("main")


def main() -> None:
    log.debug("Checking for torrents in watch directories")
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
                log.info(f"Adding {file_path} to deluge")
                # Add torrent file to remote deluge daemon
                infohash = deluge.add_torrent_by_file(str(file_path))
                # Add torrent to persistent state for watching
                ext = f.rfind(".")
                state.add_watching_torrent(infohash, str(temp_dir), str(final_dir), f[:ext] if ext > 0 else f)
                # Remove the processed torrent file
                os.remove(file_path)

    # Get currently watching torrents and try to download them if ready
    watching_torrents = state.get_watching_torrents()
    log.debug("Checking deluge for completed torrents that should be downloaded")
    for obj in deluge.get_download_objects_for_watching_torrents(watching_torrents):
        try:
            obj.download()
        except Exception:
            log.exception(f"Error: Failure to download {obj.remote_path}")

    log.debug("Completed main loop")


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    while True:
        try:
            main()
            time.sleep(15)
        except Exception:
            log.exception("Unexpected exception in main")
