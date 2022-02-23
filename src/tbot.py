import logging
import time
import signal
from utils import config
from data import TBDatabase
from tasks import MovieProbe
from visuals import Visuals

logging.basicConfig(level=logging.INFO)

def main():
    logging.info("Loading configurations")
    config.load_config(config.CONFIG_PATH)

    logging.info("Initializing data")
    db = TBDatabase(config.DB_PATH)
    db.create_schema()
    db.close()

    logging.info("Starting Torrent Bot.")
    tbot = TorrentBot()
    tbot.start()


class TorrentBot:
    """Torrent bot"""

    def __init__(self) -> None:
        self.visuals = Visuals(
            config.DB_PATH, config.frontend.secret_key, config.RES_PROFILES
        )
        self.movies_probe = MovieProbe(
            config.jackett.api_key,
            config.jackett.api_url,
            config.qbit.hostname,
            config.qbit.port,
            config.DB_PATH,
            config.movies.directory,
            config.movies.rentention_period_sec,
        )
        self.running = True
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def start(self) -> None:
        """Start torrent bot. 
        The starting procedure includes initializing the frontend and 
        continously probing for new torrents.
        """
        logging.info("Starting visuals")
        self.visuals.start()
        while self.running:
            logging.debug("Probing...")
            self.movies_probe.probe()
            self.movies_probe.update()
            logging.debug(f"Going to sleep...")
            time.sleep(5)

        logging.info(f"Shuting down..")
        self.movies_probe.shutdown()
    
    def exit_gracefully(self, *args) -> None:
        """Changed the bot running flag to False
        """
        self.running = False


if __name__ == "__main__":
    main()
