import logging
import yaml
import os
from pathlib import Path
from collections import namedtuple
import secrets

ROOT_PATH = f"{Path.home()}/.tbot"
CONFIG_PATH = f"{ROOT_PATH}/config.yaml"
DB_PATH = f"{ROOT_PATH}/tbot.db"
RES_PROFILES = {
    "1080p+bluray",
    "1080p+webrip,1080p+web-dl,1080p+hdrip,1080p+brrip",
    "1080p",
    "720p+bluray",
    "720p+webrip,720p+web-dl,720p+hdrip,720p+brrip",
    "720p",
    "any"
}
ASCII_ART = '''
  _______                        _     ____        _   
 |__   __|                      | |   |  _ \      | |  
    | | ___  _ __ _ __ ___ _ __ | |_  | |_) | ___ | |_ 
    | |/ _ \| '__| '__/ _ \ '_ \| __| |  _ < / _ \| __|
    | | (_) | |  | | |  __/ | | | |_  | |_) | (_) | |_ 
    |_|\___/|_|  |_|  \___|_| |_|\__| |____/ \___/ \__|
'''

jackett, qbit, movies, shows, frontend = None, None, None, None, None
_jackett = namedtuple("jackett", ["api_key", "api_url"])
_qbit = namedtuple("qbit", ["hostname", "port"])
_movies = namedtuple("movies", ['directory', 'rentention_period_sec'])
_shows = namedtuple("shows", ['directory', 'rentention_period_sec'])
_frontend = namedtuple("frontend", ['secret_key', 'hostname', 'port'])


def load_config():
    global jackett, qbit, movies, shows, frontend
    with open(CONFIG_PATH, 'r') as f:
        configuration = yaml.safe_load(f)
        jackett = _jackett(api_key=configuration['jackett']['api_key'],
                           api_url=configuration['jackett']['api_url'])
        qbit = _qbit(hostname=configuration['qbittorrent']['hostname'],
                     port=configuration['qbittorrent']['port'])
        movies = _movies(directory=configuration['movies']['directory'],
                         rentention_period_sec=configuration['movies']['retention_period_days'] * 30 * 60 * 60)
        shows = _shows(directory=configuration['shows']['directory'],
                       rentention_period_sec=configuration['shows']['retention_period_days'] * 30 * 60 * 60)
        frontend = _frontend(secret_key=configuration['frontend'].get('secret_key', secrets.token_hex()),
                             hostname=configuration['frontend'].get('hostname', 'localhost'),
                             port=configuration['frontend'].get('port', 5000))


def create_config():
    if not os.path.exists(ROOT_PATH):
        print(f"Torrent-Bot root path ({ROOT_PATH}) not found!")

        print("\n====================================\n"
              "CREATING NEW CONFIGURATIONS\n"
              "====================================\n")

        jackett_api_key = input("Insert Jackett api key:")
        movies_directory = input("Insert Movies storage directory:")
        shows_directory = input("Insert Tv Shows storage directory:")
        logging.info(f"Creating root path...")
        os.mkdir(ROOT_PATH)
        yaml_dict = {
            'jackett': {
                'api_key': jackett_api_key,
                'api_url': 'http://127.0.0.1:9117/api/v2.0'
            },
            'qbittorrent': {
                'hostname': '127.0.0.1',
                'port': 8080
            },
            'movies': {
                'directory': movies_directory,
                'retention_period_days': 30
            },
            'shows': {
                'directory': shows_directory,
                'retention_period_days': 30
            },
            'frontend': {
                'hostname': '127.0.0.1',
                'port': 5000
            }
        }
        with open(CONFIG_PATH, 'w') as file:
            yaml.dump(yaml_dict, file)
