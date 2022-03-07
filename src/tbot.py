import logging
import time
import signal
from utils import config
from data import TBDatabase
from probes import MovieProbe
from visuals import Visuals
from probes import TVShowProbe


logging.basicConfig(level=logging.INFO)


def main():
    """
    Main function for torrent bot.
    Used to load the initial configuration, create the database and start the torrent bot.
    """
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
        continously probing for new torrents.
        """
        logging.info("Starting visuals")
        self.visuals.start()
        sleepcount = 5
        while self.running:
            if sleepcount == 5:
                logging.debug("Probing...")
                self.movies_probe.start()
                self.series_probe.start()
                logging.debug(f"Going to sleep...")
                sleepcount = 0
            else:
                time.sleep(1)
                sleepcount += 1

        logging.info(f"Shuting down..")
        self.movies_probe.shutdown()

    def exit_gracefully(self, *args) -> None:
        """Change the bot running flag to False
        """
        self.running = False


if __name__ == "__main__":
    main()
