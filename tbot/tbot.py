import argparse
from pathlib import Path
from utils import config
from jackett import JacketClient
from qbittorrent import QbittorrentClient

DEFAULT_CONFIG_PATH=f"{Path.home()}/config.yaml"

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="Specify a different config file path.", default=DEFAULT_CONFIG_PATH)
args = parser.parse_args()

config_path = args.config
cfg = config.load_config(config_path)
print(cfg)


# Initialization
jacket_api_key = cfg['jacket']['api_key']
jacket = JacketClient(jacket_api_key)

qbittorrent_url = cfg['qbittorrent']['url']
qbittorrent = QbittorrentClient(cfg['qbittorrent']['qbittorrent_url'])

# Movies Download
movies = cfg['movies']

for movie in movies:
    name = movie.get('name')
    max_size = movie.get("max_size", None)
    year = movie.get("year", None)
    res = movie.get("max_size", ['720p', '1080p'])
    lang = movie.get("lang", None)
    destination_dir = movie.get("dir")
    link = jacket.find_movie(name, max_size, year, res, lang)
    qbittorrent.download(link, destination_dir)


# Series Download
# @TODO

# Others
# @TODO

# Clear Seeding
# @TODO

# Remove movies not in the list