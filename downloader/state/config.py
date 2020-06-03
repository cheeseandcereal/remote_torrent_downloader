from typing import List, Dict, Any
import json

config_cache: Dict[str, Any] = {}


def _load_config_if_necessary() -> None:
    global config_cache
    if not config_cache:
        with open("config.json") as f:
            config_cache = json.load(f)
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
            # Torrent client option checking
            if config_cache.get("torrent_client_type") != "deluge" and config_cache.get("torrent_client_type") != "transmission":
                raise Exception("torrent_client_type must be either 'deluge' or 'transmission'")
            torrent_client_opts = config_cache.get("torrent_client_options")
            if not isinstance(torrent_client_opts, dict):
                raise Exception("torrent_client_options must exist in config.json and be an object")
            if config_cache.get("torrent_client_type") == "deluge":
                if not isinstance(torrent_client_opts.get("deluge_rpc_addr"), str):
                    raise Exception("deluge_rpc_addr must exist in config.json and be a string")
                if not isinstance(torrent_client_opts.get("deluge_rpc_port"), int):
                    raise Exception("deluge_rpc_port must exist in config.json and be an integer")
                if not isinstance(torrent_client_opts.get("deluge_rpc_user"), str):
                    raise Exception("deluge_rpc_user must exist in config.json and be a string")
                if not isinstance(torrent_client_opts.get("deluge_rpc_password"), str):
                    raise Exception("deluge_rpc_password must exist in config.json and be a string")
            elif config_cache.get("torrent_client_type") == "transmission":
                if not isinstance(torrent_client_opts.get("transmission_rpc_addr"), str):
                    raise Exception("transmission_rpc_addr must exist in config.json and be a string")
                if not isinstance(torrent_client_opts.get("transmission_rpc_port"), int):
                    raise Exception("transmission_rpc_port must exist in config.json and be an integer")
                if not isinstance(torrent_client_opts.get("transmission_rpc_path"), str):
                    raise Exception("transmission_rpc_path must exist in config.json and be a string")
                if not isinstance(torrent_client_opts.get("transmission_rpc_user"), str):
                    raise Exception("transmission_rpc_user must exist in config.json and be a string")
                if not isinstance(torrent_client_opts.get("transmission_rpc_password"), str):
                    raise Exception("transmission_rpc_password must exist in config.json and be a string")
                if not isinstance(torrent_client_opts.get("transmission_rpc_verified_tls"), bool):
                    raise Exception("transmission_rpc_verified_tls must exist in config.json and be a boolean")

            if not isinstance(config_cache.get("torrent_watch_dirs"), list):
                raise Exception("torrent_watch_dirs must exist in config.json and be an array")
            # TODO torrent_watch_dirs content verification


def get_state_json_path() -> str:
    _load_config_if_necessary()
    return config_cache["state_json"]


def get_torrent_client_type() -> str:
    _load_config_if_necessary()
    return config_cache["torrent_client_type"]


def get_torrent_client_config() -> Dict[str, str]:
    _load_config_if_necessary()
    options = config_cache["torrent_client_options"]
    if config_cache["torrent_client_type"] == "deluge":
        return {
            "host": options["deluge_rpc_addr"],
            "port": options["deluge_rpc_port"],
            "username": options["deluge_rpc_user"],
            "password": options["deluge_rpc_password"],
        }
    elif config_cache["torrent_client_type"] == "transmission":
        return {
            "host": options["transmission_rpc_addr"],
            "port": options["transmission_rpc_port"],
            "path": options["transmission_rpc_path"],
            "username": options["transmission_rpc_user"],
            "password": options["transmission_rpc_password"],
            "ssl": options["transmission_rpc_verified_tls"],
        }
    else:
        raise NotImplementedError(f"torrent client type {config_cache['torrent_client_type']} not implemented")


def get_sftp_options() -> Dict[str, str]:
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


def get_torrent_watch_dirs() -> List[Dict[str, Any]]:
    _load_config_if_necessary()
    return config_cache["torrent_watch_dirs"]


def get_chmod_config() -> Dict[str, int]:
    _load_config_if_necessary()
    return config_cache.get("chmod_download", False)
