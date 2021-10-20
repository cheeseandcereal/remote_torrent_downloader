from typing import Dict, Any
import json
import logging

from downloader.state import config

log = logging.getLogger("state")

current_state = {}


def _load_state() -> None:
    global current_state
    try:
        with open(config.get_state_json_path()) as f:
            current_state = json.load(f)
    except FileNotFoundError:
        log.warning("state file not found")


def _save_state() -> None:
    with open(config.get_state_json_path(), "w") as f:
        json.dump(current_state, f, ensure_ascii=False, indent=2)


def get_watching_torrents() -> Dict[str, Dict[str, Any]]:
    """Returns a dictionary where the keys are the infohash of a torrent (torrent id) with the items:
    temp_dir: temporary local download directory
    final_dir: final local download directory (to move too upon download completion)
    auto_extract: bool of whether or not to attempt auto extraction to the download (if necesssary)
    auto_delete_extracted: bool of whether or not to automatically delete archive files after auto extracting (if necessary)
    """
    _load_state()
    return current_state.get("watching_torrents", {})


def remove_watching_torrent(torrent_id: str) -> None:
    _load_state()
    try:
        del current_state["watching_torrents"][torrent_id]
        _save_state()
    except KeyError:
        log.warning(f"tried to delete torrent {torrent_id} which was not being watched")


def add_watching_torrent(
    torrent_id: str, temp_dir: str, final_dir: str, name: str = "", auto_extract: bool = False, auto_delete_extracted: bool = False
) -> None:
    _load_state()
    new_watching = current_state.get("watching_torrents", {})
    new_watching[torrent_id] = {
        "temp_dir": temp_dir,
        "final_dir": final_dir,
        "name": name,
        "auto_extract": auto_extract,
        "auto_delete_extracted": auto_delete_extracted,
    }
    current_state["watching_torrents"] = new_watching
    _save_state()
