from typing import Dict, Any
import json

config_cache: Dict[str, Any] = {}


def _load_config_if_necessary():
    global config_cache
    if not config_cache:
        with open("config.json") as f:
            config_cache = json.loads(f.read())
            # Validate config file
            if not isinstance(config_cache.get("state_json"), str):
                raise Exception("state_json must exist in config.json and be a string")
            if not isinstance(config_cache.get("sftp_host"), str):
                raise Exception("sftp_host must exist in config.json and be a string")
            if not isinstance(config_cache.get("sftp_port"), int):
                raise Exception("sftp_port must exist in config.json and be an integer")
            if not isinstance(config_cache.get("sftp_user"), str):
                raise Exception("sftp_user must exist in config.json and be a string")
            if not isinstance(config_cache.get("sftp_password"), str):
                raise Exception("sftp_password must exist in config.json and be a string")
            if not isinstance(config_cache.get("pget_conn"), int):
                raise Exception("pget_conn must exist in config.json and be an integer")
            if not isinstance(config_cache.get("mirror_parallel"), int):
                raise Exception("mirror_parallel must exist in config.json and be an integer")
            if not isinstance(config_cache.get("mirror_conn"), int):
                raise Exception("mirror_conn must exist in config.json and be an integer")
            if not isinstance(config_cache.get("deluge_rpc_addr"), str):
                raise Exception("deluge_rpc_addr must exist in config.json and be a string")
            if not isinstance(config_cache.get("deluge_rpc_port"), int):
                raise Exception("deluge_rpc_port must exist in config.json and be an integer")
            if not isinstance(config_cache.get("deluge_rpc_user"), str):
                raise Exception("deluge_rpc_user must exist in config.json and be a string")
            if not isinstance(config_cache.get("deluge_rpc_password"), str):
                raise Exception("deluge_rpc_password must exist in config.json and be a string")
            if not isinstance(config_cache.get("torrent_watch_dirs"), list):
                raise Exception("torrent_watch_dirs must exist in config.json and be an array")


def get_download_path() -> str:
    _load_config_if_necessary()
    return config_cache["download_path"]


def get_remote_path() -> str:
    _load_config_if_necessary()
    return config_cache["remote_path"]


def get_state_json_path() -> str:
    _load_config_if_necessary()
    return config_cache["state_json"]


def get_deluge_rpc_config():
    _load_config_if_necessary()
    return {
        "host": config_cache["deluge_rpc_addr"],
        "port": config_cache["deluge_rpc_port"],
        "username": config_cache["deluge_rpc_user"],
        "password": config_cache["deluge_rpc_password"],
    }


def get_sftp_options():
    _load_config_if_necessary()
    return {
        "host": config_cache["sftp_host"],
        "port": config_cache["sftp_port"],
        "username": config_cache["sftp_user"],
        "password": config_cache["sftp_password"],
        "pget_conn": config_cache["pget_conn"],
        "mirror_parallel": config_cache["mirror_parallel"],
        "mirror_conn": config_cache["mirror_conn"],
    }


def get_torrent_watch_dirs():
    _load_config_if_necessary()
    return config_cache["torrent_watch_dirs"]
