from typing import NamedTuple
import yaml
import os
from collections import namedtuple

jackett, qbit, movies = None, None, None
_jackett = namedtuple("jackett", ["api_key", "api_url"])
_qbit = namedtuple("qbit", ["hostname", "port"])
_movies = namedtuple("movies", ['directory', 'rentention_period_sec', 'list'])

def load_config(path):
    global jackett, qbit, movies
    if os.path.exists(path):
        with open(path, 'r') as f:
            configuration =  yaml.safe_load(f)
            jackett = _jackett(api_key=configuration['jackett']['api_key'],
                               api_url=configuration['jackett']['api_url'])
            qbit = _qbit(hostname=configuration['qbittorrent']['hostname'],
                               port=configuration['qbittorrent']['port'])
            
            movies = _movies(directory=configuration['movies']['directory'],
                             rentention_period_sec=configuration['movies']['rentention_period_sec'],
                             list=configuration['movies']['list'])
    else:
        print(f"Config file not found. ({path})!")
