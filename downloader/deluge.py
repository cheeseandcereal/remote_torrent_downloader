from typing import List, Dict, Any
import re
import logging
from base64 import b64encode
from pathlib import PurePosixPath, Path

import deluge_client.client

from downloader.model.download_obj import DownloadObject
from downloader.state import config

log = logging.getLogger("deluge")

_torrent_exists_regex = re.compile(r"Torrent already in session \((.*)\)", re.IGNORECASE)

client = deluge_client.client.DelugeRPCClient(**config.get_deluge_rpc_config(), decode_utf8=True, automatic_reconnect=True)


def _connect_if_necessary() -> None:
    if not client.connected:
        log.debug("Connecting to remote deluge daemon")
        client.connect()


def _filter_torrents_status_results(torrent_status_results: Any, watching_torrents: Dict[str, Dict[str, Any]]) -> List[DownloadObject]:
    download_list: List[DownloadObject] = []
    for infohash, torrent_data in torrent_status_results.items():
        completed_time = torrent_data.get("completed_time", 0)
        if completed_time > 0:  # Only completed torrents
            temp_dir = watching_torrents[infohash]["temp_dir"]
            final_dir = watching_torrents[infohash]["final_dir"]
            auto_extract = watching_torrents[infohash].get("auto_extract", False)
            auto_delete_extracted = watching_torrents[infohash].get("auto_delete_extracted", False)
            base_dir = torrent_data["download_location"]
            base_folders = set()
            for file_data in torrent_data["files"]:
                path = PurePosixPath(file_data["path"])
                if len(path.parts) > 1:  # If this file is in a dir in the torrent
                    base_folders.add(path.parts[0])
                elif len(path.parts) == 1:  # This file is at the root of the torrent
                    download_list.append(
                        DownloadObject(
                            infohash,
                            str(PurePosixPath(base_dir, path.parts[0])),
                            completed_time,
                            False,
                            temp_dir,
                            final_dir,
                            auto_extract,
                            auto_delete_extracted,
                        )
                    )
            for folder in base_folders:
                download_list.append(
                    DownloadObject(
                        infohash, str(PurePosixPath(base_dir, folder)), completed_time, True, temp_dir, final_dir, auto_extract, auto_delete_extracted
                    )
                )
    # Sort by timestamp before returning
    download_list.sort(key=lambda x: x.timestamp)
    return download_list


def get_download_objects_for_watching_torrents(watching_torrents: Dict[str, Dict[str, Any]]) -> List[DownloadObject]:
    _connect_if_necessary()
    torrents = client.call("core.get_torrents_status", {"id": list(watching_torrents.keys())}, ["completed_time", "download_location", "files"])
    return _filter_torrents_status_results(torrents, watching_torrents)


def _check_torrent_exists_err(error: deluge_client.client.RemoteException) -> str:
    # Check if the error is that the torrent already exists. If it does, return existing infohash
    match = _torrent_exists_regex.match(str(error))
    if match:
        existing_infohash = match.group(1)
        log.debug(f"Attempt to add existing torrent {existing_infohash}")
        return existing_infohash
    # Unhandled error
    raise error


def add_torrent_by_file(torrent_file_path: str) -> str:
    """Add a torrent from a local file and return its infohash (torrent id)"""
    _connect_if_necessary()
    try:
        path = Path(torrent_file_path)
        if path.suffix == ".magnet":  # Check if file is a magnet link instead of a torrent file (by extension)
            with open(torrent_file_path, "r") as ft:
                return add_torrent_by_uri(ft.read())
        else:
            with open(torrent_file_path, "rb") as fb:
                return client.call("core.add_torrent_file", path.name, b64encode(fb.read()).decode("ascii"), {})
    except deluge_client.client.RemoteException as e:
        return _check_torrent_exists_err(e)


def add_torrent_by_uri(torrent_uri: str) -> str:
    """Add a torrent from a uri and return its infohash (torrent id)"""
    _connect_if_necessary()
    try:
        if torrent_uri.startswith("magnet"):
            return client.call("core.add_torrent_magnet", torrent_uri, {})
        else:
            return client.call("core.add_torrent_url", torrent_uri, {})
    except deluge_client.client.RemoteException as e:
        return _check_torrent_exists_err(e)
