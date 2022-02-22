import logging
import time
from pathlib import Path
from utils import config
from tools import JackettClient
from tools import QbittorrentClient
from data import TBDatabase
from tasks import MovieProbe
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
        self.movies_probe = MovieProbe(
            config.jackett.api_key,
            config.jackett.api_url,
            config.qbit.hostname,
            config.qbit.port,
            DB_PATH,
            config.movies.directory,
            config.movies.rentention_period_sec,
        )
        # tvseries_bot = TvSeriesBot(jacket, qbittorrent)
        self.running = True

    def run(self) -> None:
        while self.running:
            # Start tasks
            logging.info("Starting tasks..")
            self.movies_probe.probe()
            self.movies_probe.update()

            logging.info("Finished tasks..")
            logging.info(f"Going to sleep...")
            time.sleep(5)

        # Shutdown bots
        logging.info(f"Shuting down..")
        self.movies_probe.shutdown()
        # tvseries_bot.shutdown()


if __name__ == "__main__":
    main()
