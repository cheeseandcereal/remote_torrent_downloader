from typing import Dict
import json

from downloader.state import config

current_state = {}


def _load_state():
    global current_state
    try:
        with open(config.get_state_json_path()) as f:
            current_state = json.loads(f.read())
    except FileNotFoundError:
        print("Warning: state file not found")


def _save_state():
    with open(config.get_state_json_path(), "w") as f:
        f.write(json.dumps(current_state, indent=2))


def get_watching_torrents() -> Dict[str, Dict[str, str]]:
    """Returns a dictionary where the keys are the infohash of a torrent (torrent id) with the items:
       temp_dir: temporary local download directory
       final_dir: final local download directory (to move too upon download completion)
    """
    _load_state()
    return current_state.get("watching_torrents", {})


def remove_watching_torrent(torrent_id: str):
    _load_state()
    try:
        del current_state["watching_torrents"][torrent_id]
        _save_state()
    except KeyError:
        print(f"Warning: tried to delete torrent {torrent_id} which was not being watched")


def add_watching_torrent(torrent_id: str, temp_dir: str, final_dir: str):
    _load_state()
    new_watching = current_state.get("watching_torrents", {})
    new_watching[torrent_id] = {"temp_dir": temp_dir, "final_dir": final_dir}
    current_state["watching_torrents"] = new_watching
    _save_state()