# Torrent Remote Auto Downloader/Fetcher

This is a program to bridge the gap between downloading a torrent file with a remote torrent daemon,
and then automatically fetching the resulting files with [lftp(1)](https://lftp.yar.ru/) once completed.

This was specifically written to work with the `Torrent Blackhole` option in [sonarr](https://sonarr.tv/)
for the usecase of downloading and seeding with torrent daemon on a completely remote machine.

## Configuration

A file called `config.json` must be present in the working directory of the program when running.

An example configuration:

```javascript
{
  "state_json": "state.json",  // path to json file used for storing app state
  "chmod_download": {  // set to false instead of object if you do not want to chmod downloaded files
    "file": 436,  // 436 == 0o664
    "folder": 509  // 509 == 0o775
  },
  "sftp_host": "my.remote.host.or.ip",
  "sftp_port": 22,
  "sftp_user": "user",
  "sftp_password": "leave as empty string if using public key",
  "pget_conn": 25,  // when torrent is a single file, this is how many connections will be used with lftp pget
  "mirror_parallel": 4,  // when torrent is a directory, this is how many files are downloaded simoultaneously
  "mirror_conn": 7,  // when torrent is a directory, this is how many connections each currently downloading file gets
  "torrent_client_type": "deluge", // deluge or transmission
  "torrent_client_options": { // note you only need to specify deluge OR transmission options here, dependent on torrent_client_type above
    "deluge_rpc_addr": "my.remote.host.or.ip",
    "deluge_rpc_port": 58846,
    "deluge_rpc_user": "user",
    "deluge_rpc_password": "someRPCpasswordFromDelugeDaemon",
    "transmission_rpc_addr": "my.remote.host.or.ip",
    "transmission_rpc_port": 9091,
    "transmission_rpc_path": "/transmission/rpc",
    "transmission_rpc_user": "user",
    "transmission_rpc_password": "someRPCpasswordFromTransmissionDaemon",
    "transmission_rpc_verified_tls": true // note that unverified ssl/tls (such as with self-signed cert) is not currently supported
  },
  "torrent_watch_dirs": [  // Specify as many as desired
    {
      "directory": "/home/user/Downloads/torrents",  // Directory to watch for .torrent or .magnet files
      "temp_download_dir": "/tmp",  // Used for temporary storage for in-progress downloads
      "final_download_dir": "/home/user/Downloads"  // Where finished downloads are moved
      "attempt_extract": true  // (Optional) Attempt to extract downloaded files (unix only) (default false)
      "auto_delete_extracted": true // (Optional) When attempt_extract is true, delete the archive files after extracting (default false)
    }
  ]
}
```

## Running

### Requirements

In order to run this, there are different requirements for the local machine running this and the remote machine running the torrent daemon.

- Remote Machine
  - Should be linux (may work on unix?)
  - Running torrent daemon
    - Deluge daemon (only tested with 2.X, but should work with 1.X as well),
      accessible over the network with the specified RPC options in the config.
      See these [deluge docs](https://dev.deluge-torrent.org/wiki/UserGuide/ThinClient) for more info
    - OR
    - Transmission daemon (only version 3.00+) accessible over the network with the specified RPC options in the config.
      See these [transmission docs](https://github.com/transmission/transmission/wiki/Editing-Configuration-Files#rpc) for more info
  - Running sshd with sftp accessible over the network using the specified SFTP options in the config.
    (Only tested with openssh, but should work with other sftp servers)
- Local Machine (with Docker)
  - No additional requirements. See below if you do not wish to use docker.
- Local Machine (without Docker)
  - Python 3.6+ with the packages from `requirements.txt` installed (`python3 -m pip install -r requirements.txt`)
  - lftp must be installed and in the [PATH](<https://en.wikipedia.org/wiki/PATH_(variable)>)
  - This _should_ be able to be ran on windows or any unix system, but only tested on linux. (Note extraction does _NOT_ work on windows.)
    (If there are bugs running this on another OS, please report them)
  - If using extraction, ensure you have `unrar` and `unzip` installed

### Starting

If using docker, simply run the container, mounting your desired config.json into `/usr/src/app/config.json`, and any other necessary directories.

i.e. `docker run -v $(pwd)/config.json:/usr/src/app/config.json -v /home/user/Downloads:/home/user/Downloads cheeseandcereal/remote_torrent_downloader:latest`

If not using docker, download the source code here, ensure the above requirements are met,
create and ensure you have a config.json in your working directory,
then start the program with `python3 -m downloader.main` in a terminal of some sort.
(`python3` may need to be replaced with `python` depening on how it was installed).

#### Systemd Example Service

The following is an example systemd service file if running on linux with systemd and not docker.

```systemd
[Unit]
Description=Remote Torrent Fetcher
After=network-online.target

[Service]
# Set unbuffered so logging works when running under systemd
Environment="PYTHONUNBUFFERED=true"
WorkingDirectory=/directory/of/code/with/configjson/
ExecStart=/usr/bin/python3 -m downloader.main
Restart=always
RestartSec=30

[Install]
WantedBy=default.target
```
