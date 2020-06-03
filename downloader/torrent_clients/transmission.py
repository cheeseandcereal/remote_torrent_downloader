from typing import List, Dict, Any, cast
import logging
from base64 import b64encode
from pathlib import PurePosixPath, Path

from transmission import Transmission

from downloader.model.download_obj import DownloadObject
from downloader.state import config

log = logging.getLogger("transmission")

# Will get created when a method using the client is called
client = cast(Transmission, None)


def _connect_if_necessary() -> None:
    global client
    if not client:
        log.info("Connecting to transmission daemon")
        client = Transmission(**config.get_torrent_client_config())


def _filter_torrents_status_results(torrent_status_results: Any, watching_torrents: Dict[str, Dict[str, Any]]) -> List[DownloadObject]:
    download_list: List[DownloadObject] = []
    for torrent_data in torrent_status_results["torrents"]:
        infohash = torrent_data["hashString"]
        completed_time = int(torrent_data["doneDate"].timestamp())
        temp_dir = watching_torrents[infohash]["temp_dir"]
        final_dir = watching_torrents[infohash]["final_dir"]
        auto_extract = watching_torrents[infohash].get("auto_extract", False)
        auto_delete_extracted = watching_torrents[infohash].get("auto_delete_extracted", False)
        base_dir = torrent_data["downloadDir"]
        base_folders = set()
        for file_data in torrent_data["files"]:
            path = PurePosixPath(file_data["name"])
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
    wanted_ids = []
    # First make a call to get all torrents, to determine which ids we want
    all_torrents = client.call("torrent-get", fields=["hashString", "percentDone", "id"])
    for torrent_data in all_torrents["torrents"]:
        if torrent_data["hashString"] in watching_torrents and torrent_data["percentDone"] == 1:  # Only completed torrents we are watching
            wanted_ids.append(torrent_data["id"])
    # Now get the all the relevant info for our wanted torrent ids
    torrents = client.call("torrent-get", ids=wanted_ids, fields=["hashString", "downloadDir", "doneDate", "files"])
    return _filter_torrents_status_results(torrents, watching_torrents)


def _get_torrent_hash_from_add(torrent_add_response: Dict[str, Any]) -> str:
    # Transmission sends a different payload if the added torrent was a duplicate, so we have to check/parse seperately for this
    if torrent_add_response.get("torrent-added"):
        return torrent_add_response["torrent-added"]["hashString"]
    elif torrent_add_response.get("torrent-duplicate"):
        return torrent_add_response["torrent-duplicate"]["hashString"]
    else:
        raise RuntimeError("Unexpected torrent-add response from transmission")


def add_torrent_by_file(torrent_file_path: str) -> str:
    """Add a torrent from a local file and return its infohash"""
    _connect_if_necessary()
    path = Path(torrent_file_path)
    if path.suffix == ".magnet":  # Check if file is a magnet link instead of a torrent file (by extension)
        with open(torrent_file_path, "r") as ft:
            return add_torrent_by_uri(ft.read())
    else:
        with open(torrent_file_path, "rb") as fb:
            return _get_torrent_hash_from_add(client.call("torrent-add", metainfo=b64encode(fb.read()).decode("ascii")))


def add_torrent_by_uri(torrent_uri: str) -> str:
    """Add a torrent from a uri and return its infohash"""
    _connect_if_necessary()
    return _get_torrent_hash_from_add(client.call("torrent-add", filename=torrent_uri))
