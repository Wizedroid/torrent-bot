from os import stat
import logging
from utils import config
from .probe import Probe


class MovieProbe(Probe):
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
        storage_dir: str,
        retention_preiod_sec: int,
    ) -> None:
        super().__init__(jackett_api_key, jackett_api_url, qbit_hostname,
                       qbit_port, data_path, storage_dir, retention_preiod_sec)

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

    def probe(self) -> None:
        """Search and download movies added to the databse (state=SEARCHING)
        """
        for movie_row in self.db.get_movies_by_state(state=self.db.states.SEARCHING):
                jackett_result = self.jackett.search_movies(
                    name=movie_row.get("name"),
                    resolution_profile=set(movie_row.get(
                        "resolution_profile").split(',')),
                    max_size_bytes=self.mb_to_bytes(movie_row.get("max_size_mb")),
                    min_number_seeds=2,
                )
                if jackett_result:
                    movie = jackett_result[0]  # Highest number of seeds
                    magnetUri = movie["MagnetUri"]
                    self.qbit.download(magnetUri, self.storage_dir)
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
            
            self.update_torrent_states(id, hash, state, type="MOVIE")