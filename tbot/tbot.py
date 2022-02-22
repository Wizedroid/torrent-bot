import logging
import time
from pathlib import Path
from utils import config
from tools import JackettClient
from tools import QbittorrentClient
from data import TBDatabase
from tasks import MovieFinder
from visuals import Visuals

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

logging.basicConfig(level=logging.INFO)


def main():
    # Load configs
    config.load_config(CONFIG_PATH)
    # Initialize the TBot
    logging.info("Starting Torrent Bot.")
    tbot = TBot()
    tbot.run()
    
class TBot:

    def __init__(self) -> None:
        # Initialize the database
        logging.info("Initializing data")
        db = TBDatabase(DB_PATH)
        db.create_schema()
        # Initialize the frontend
        logging.info("Initializing visuals")
        visuals = Visuals(DB_PATH, config.frontend.secret_key, RES_PROFILES)
        visuals.start()
        # Initialize tasks @TODO (naming)
        logging.info("Initializing tasks")
        jacket = JackettClient(config.jackett.api_key, config.jackett.api_url)
        qbittorrent = QbittorrentClient(config.qbit.hostname, config.qbit.port)
        self.movies_bot = MovieFinder(jacket, qbittorrent, TBDatabase(DB_PATH))
        # tvseries_bot = TvSeriesBot(jacket, qbittorrent)
        self.running = True


    def run(self) -> None:
        while self.running:
            # Initialize bot download sequences
            logging.info("Started download task..")
            self.movies_bot.start_download(
                config.movies.directory
            )  # @TODO change movies to DB
            # tvseries_bot.start_download(config.series.directory, config.series.list) # @TODO change series to DB

            # Initialize bot cleanup sequences
            logging.info(f"Removing torrents older than {config.movies.rentention_period_sec}")
            self.movies_bot.cleanup(config.movies.rentention_period_sec)
            # tvseries_bot.cleanup(config.movies.rentention)

            logging.info(f"Going to sleep...")
            time.sleep(60)

        # Shutdown bots
        logging.info(f"Shuting down..")
        self.movies_bot.shutdown()
        # tvseries_bot.shutdown()


if __name__ == "__main__":
    main()
