import logging
import time
import signal
import sys
from utils import config
from data import TBDatabase
from probes import MovieProbe
from visuals import Visuals
from probes import TVShowProbe
import logging.handlers as handlers

file_handler = handlers.RotatingFileHandler(f"{config.ROOT_PATH}/tbot.log", maxBytes=1048576, backupCount=5)
stdout_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=[file_handler, stdout_handler]
)


def main():
    """
    Main function for torrent bot.
    Used to load the initial configuration, create the database and start the torrent bot.
    """
    config.create_config()
    logging.info(config.ASCII_ART)

    logging.info("Loading configurations")
    config.load_config()

    logging.info("Initializing data")
    db = TBDatabase(config.DB_PATH)
    db.create_schema()
    db.close()

    logging.info("Starting Torrent Bot.")
    tbot = TorrentBot()
    tbot.start()


class TorrentBot:
    """Torrent bot.
    The bot has probes that are periodically called for searching movies and tv series which were previously added to a database. 
    These probes are also responsible for updating the database so that it reflects the latest findings, downloads, uploads or deleted torrents.

    In addition to the probes, the torrent bot also initializes a frontend (called visuals), which will be listening on the configured
    host and port for the frontend.
    """

    def __init__(self) -> None:
        self.visuals = Visuals.new(config)
        self.movies_probe = MovieProbe.new(config)
        self.series_probe = TVShowProbe.new(config)
        self.running = True
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def start(self) -> None:
        """Start torrent bot. 
        The starting procedure includes initializing the frontend and 
        continuously probing for new torrents.
        """
        logging.info("Starting visuals")
        self.visuals.start()
        while self.running:
            logging.debug("Probing...")
            self.movies_probe.start()
            self.series_probe.start()
            logging.debug(f"Going to sleep...")
            time.sleep(5)

        logging.info(f"Shutting down..")
        self.movies_probe.shutdown()
        self.series_probe.shutdown()

    def exit_gracefully(self, *args) -> None:
        """Change the bot running flag to False
        """
        logging.info(f"Received terminating signal..")
        self.running = False


if __name__ == "__main__":
    main()
