# Deluge Remote Auto Downloader/Fetcher

This is a program to bridge the gap between downloading a torrent file with a remote deluge daemon,
and then automatically fetching the resulting files with [lftp(1)](https://lftp.yar.ru/) once completed.

This was specifically written to work with the `Torrent Blackhole` option in [sonarr](https://sonarr.tv/)
for the usecase of downloading with deluge on a completely remote machine (and no deluge web-ui requirement).

## Configuration

A file called `config.json` must be present in the working directory of the program when running.

An example configuration:

```json
{
  "state_json": "state.json",
  "sftp_host": "my.remote.host",
  "sftp_port": 22,
  "sftp_user": "user",
  "sftp_password": "leave as empty string if using public key",
  "pget_conn": 25,
  "mirror_parallel": 4,
  "mirror_conn": 7,
  "deluge_rpc_addr": "my.remote.host",
  "deluge_rpc_port": 54321,
  "deluge_rpc_user": "user",
  "deluge_rpc_password": "someRPCpasswordFromDelugeDaemon",
  "torrent_watch_dirs": [
    {
      "directory": "/home/user/Downloads/torrents",
      "temp_download_dir": "/tmp",
      "final_download_dir": "/home/user/Downloads"
    }
  ]
}
```

## Running

### Requirements

In order to run this, there are different requirements for the local machine running this and the remote machine running deluge.

- Remote Machine
  - Should be linux (may work on unix?)
  - Running deluge daemon (only tested with 2.X, but should work with 1.X as well),
    accessible over the network with the specified RPC options in the config.
    See these [deluge docs](https://dev.deluge-torrent.org/wiki/UserGuide/ThinClient) for more information
  - Running sshd with sftp accessible over the network using the specified SFTP options in the config.
    (Only tested with openssh, but may work with other sftp servers)
- Local Machine (with Docker)
  - No additional requirements. See below if you do not wish to use docker.
- Local Machine (without Docker)
  - Python 3.6+ with the packages from `requirements.txt` installed (`python3 -m pip install -r requirements.txt`)
  - lftp must be installed and in the [PATH](<https://en.wikipedia.org/wiki/PATH_(variable)>)
  - This _should_ be able to be ran on windows or any unix system, but only tested on linux.
    (If there are bugs running this on another OS, please report them)

### Starting

If using docker, simply run the container, mounting your desired config.json into `/usr/src/app/config.json`, and any other necessary directories.

i.e. `docker run -v $(pwd)/config.json:/usr/src/app/config.json -v /home/user/Downloads:/home/user/Downloads cheeseandcereal/remote_deluge_downloader:latest`

If not using docker, download the source code here, ensure the above requirements are met,
create and ensure you have a config.json in your working directory,
then start the program with `python3 -m downloader.main` in a terminal of some sort.
(`python3` may need to be replaced with `python` depening on how it was installed).