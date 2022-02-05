import argparse
import logging
from pathlib import Path
from utils import config
from jackett.client import JacketClient
from qbittorrent.client import QbittorrentClient
from bots.movies_bot import MoviesBot

DEFAULT_ROOT_PATH = f"{Path.home()}/.tbot"
DEFAULT_CONFIG_PATH = f"{DEFAULT_ROOT_PATH}/config.yaml"

logging.basicConfig(level=logging.DEBUG)

def main():
    logging.debug("Starting Torrent Bot.")

    # Parse arguments and load configurations from a yaml configuration file
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        help="Specify a different config file path.",
        default=DEFAULT_CONFIG_PATH,
    )
    args = parser.parse_args()

    config_path = args.config
    config.load_config(config_path)

    # Initialize clients and bots
    jacket = JacketClient(config.jackett.api_key, config.jackett.api_url)
    qbittorrent = QbittorrentClient(config.qbit.hostname, config.qbit.port)
    movies_bot = MoviesBot(jacket, qbittorrent)
    #tvseries_bot = TvSeriesBot(jacket, qbittorrent)

    # Initialize bot download sequences
    logging.info("Initializing download.")
    movies_bot.start_download(config.movies.directory, config.movies.list) # @TODO change movies to DB
    #tvseries_bot.start_download(config.series.directory, config.series.list) # @TODO change series to DB

    # Initialize bot cleanup sequences
    logging.info(f"Removing torrents older than {config.movies.rentention_period_sec}")
    movies_bot.cleanup(config.movies.rentention_period_sec)
    #tvseries_bot.cleanup(config.movies.rentention)

    # Shutdown bots
    logging.info(f"Shuting down..")
    movies_bot.shutdown()
    #tvseries_bot.shutdown()

if __name__ == '__main__':
    main()