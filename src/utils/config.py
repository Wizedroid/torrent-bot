from typing import NamedTuple
from flask import config
import yaml
import os
from pathlib import Path
from collections import namedtuple

ROOT_PATH = f"{Path.home()}/.tbot"
CONFIG_PATH = f"{ROOT_PATH}/config.yaml"
DB_PATH = f"{ROOT_PATH}/tbot.db"
RES_PROFILES = {
    "1080p+bluray",
    "1080p+webrip",
    "1080p+web-dl",
    "720p+bluray",
    "720p+webrip",
    "720p+web-dl",
}

jackett, qbit, movies, frontend = None, None, None, None
_jackett = namedtuple("jackett", ["api_key", "api_url"])
_qbit = namedtuple("qbit", ["hostname", "port"])
_movies = namedtuple("movies", ['directory', 'rentention_period_sec'])
_frontend = namedtuple("frontend", ['secret_key'])

def load_config(path):
    global jackett, qbit, movies, frontend
    if os.path.exists(path):
        with open(path, 'r') as f:
            configuration =  yaml.safe_load(f)
            jackett = _jackett(api_key=configuration['jackett']['api_key'],
                               api_url=configuration['jackett']['api_url'])
            qbit = _qbit(hostname=configuration['qbittorrent']['hostname'],
                               port=configuration['qbittorrent']['port'])
            movies = _movies(directory=configuration['movies']['directory'],
                             rentention_period_sec=configuration['movies']['rentention_period_sec'])
            frontend = _frontend(secret_key=configuration['frontend']['secret_key'])
    else:
        print(f"Config file not found. ({path})!")
