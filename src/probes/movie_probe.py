from os import stat
import time
import logging
from tools import JackettClient
from tools import QbittorrentClient
from data import TBDatabase
from utils import config

class MovieProbe:
    """
    Movie probe.

    Attributes
    ----------
    jackett_api_key : str
        the jacket api str
    jackett_api_url: QbittorrentClient
        the jackett api url
    qbit_hostname: str
        the qbittorrent hostname
    qbit_port: str
        the qbittorrent port
    data_path: int
        the database file path
    movies_storage_dir: str
        the path were the movies will be stored
    retention_preiod_sec:int
        the maximum seeding period after which the torrents get removed
    """

    def __init__(
        self,
        jackett_api_key: str,
        jackett_api_url: str,
        qbit_hostname: str,
        qbit_port: int,
        data_path: str,
        movies_storage_dir: str,
        retention_preiod_sec: int,
    ) -> None:
        self.jackett = JackettClient(jackett_api_key, jackett_api_url)
        self.qbit = QbittorrentClient(qbit_hostname, qbit_port)
        self.db = TBDatabase(data_path)
        self.movies_storage_dir = movies_storage_dir
        self.retention_preiod_sec = retention_preiod_sec
    

    @staticmethod
    def new(config: config):
        """Create a new movies probe directly from the config

        Args:
            config (config): the configuration parameters for the application

        Returns:
            MovieProbe: The movie probe
        """
        return MovieProbe(
            config.jackett.api_key,
            config.jackett.api_url,
            config.qbit.hostname,
            config.qbit.port,
            config.DB_PATH,
            config.movies.directory,
            config.movies.rentention_period_sec,
        )

    def start(self) -> None:
        """Starts the probe which initiates the search, download and update
        of movies
        """
        self.probe()
        self.update()

    def probe(self) -> None:
        """Search and download movies added to the databse (state=SEARCHING)
        """
        for movie_row in self.db.get_movies_with_state(state=self.db.states.SEARCHING):
            jackett_result = self.jackett.search_movies(
                name=movie_row.get("name"),
                resolution_profile=set(movie_row.get("resolution_profile").split(',')),
                max_size_bytes=self.mb_to_bytes(movie_row.get("max_size_mb")),
                min_number_seeds=2,
            )
            if jackett_result:
                movie = jackett_result[0]  # Highest number of seeds
                magnetUri = movie["MagnetUri"]
                self.qbit.download(magnetUri, self.movies_storage_dir)
                self.db.update_movie(
                    id=movie_row["id"],
                    state=self.db.states.DOWNLOADING,
                    hash=movie["InfoHash"],
                )
            else:
                logging.info(f"Movie {movie_row.get('name')} not found!")

    def update(self) -> None:
        """Updates the database state to reflect the current downloads
        """
        movies = self.db.get_all_movies()
        for movie in movies:
            id = movie.get("id")
            state = movie.get("state")
            hash = movie.get("hash")

            # Do nothing with movies not found or already completed
            if state in [self.db.states.SEARCHING, self.db.states.COMPLETED]:
                continue

            # Catch movies without hashes
            if not hash:
                self.db.delete_movie(id)
                continue
            
            # Check if the movies should change the state
            torrents = self.qbit.torrents_info(status_filter=None, hashes=hash)
            for torrent in torrents:
                # State changed from paused,  therefore reusme
                if state != self.db.states.PAUSED and 'paused' in torrent["state"].lower():
                    self.qbit.resume(hash)

                # Remove the torrent if it is older than the retention period
                if state == self.db.states.SEEDING: 
                    time_since_added_sec = int(time.time()) - int(torrent["added_on"])
                    if time_since_added_sec > self.retention_preiod_sec:
                        self.qbit.delete(hash)
                        self.db.update_movie(id, state=self.db.states.COMPLETED)
                # Change the torrent state if it finished the download and it is now uploading
                elif state == self.db.states.DOWNLOADING and torrent["state"] == "uploading":
                    self.db.update_movie(id, state=self.db.states.SEEDING)
                # Stop download for torrents stopped
                elif state == self.db.states.PAUSED:
                    self.qbit.stop(hash)
                # Remove torrent marked for removing
                elif state == self.db.states.DELETING:
                    self.qbit.delete(hash)
                    self.db.delete_movie(id)


    def shutdown(self) -> None:
        """Close resources"""
        self.db.close()

    def mb_to_bytes(self, value: int) -> int:
        """convert the specified value int megabytes to bytes

        Args:
            value (int): the value in megabytes

        Returns:
            [int]: the value in byes
        """
        return value * 1024 * 1024
