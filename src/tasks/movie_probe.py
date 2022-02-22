import time
import logging
from tools import JackettClient
from tools import QbittorrentClient
from data import TBDatabase

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

    def probe(self) -> None:
        """Starts the probe which initiates the search and download of movies
        stored in the database
        """
        for movie_row in self.db.get_movies(state=self.db.states["searching"]):
            movie = self.find_movie(movie_row)
            if movie:
                magnetUri = movie["MagnetUri"]
                self.qbit.download(magnetUri, self.movies_storage_dir)
                self.db.update_movie(
                    id=movie_row.get("id"),
                    state=self.db.states["downloading"],
                    hash=movie['InfoHash'],
                )
            else:
                logging.info(f"Movie {movie_row.get('name')} not found!")

    def find_movie(self, movie: dict) -> dict:
        """Find the movie torrent that corresponds the the specified movie

        Args:
            movie (dict): the movie entry

        Returns:
            [dict]: the movie found or None if no movie was fod
        """
        name = movie.get("name")
        max_size_mb = movie.get("max_size_mb", None)
        res = movie.get(
            "resolutions",
            [
                "1080p+bluray",
                "1080p+webrip",
                "1080p+web-dl",
                "720p+bluray",
                "720p+webrip",
                "720p+web-dl",
            ],
        )
        lang = movie.get("lang", None)
        movies = self.jackett.search_movies(
            name=name,
            resolution_profile=res,
            max_size_bytes=self.mb_to_bytes(max_size_mb),
            lang=lang,
            min_number_seeds=2,
        )
        if movies:
            return movies[0] # Highest number of seeds

    def update(self) -> None:
        """Updates the database state to reflect the current downloads
        """
        movies = self.db.get_all_movies()
        for movie in movies:
            id = movie.get("id")
            state = movie.get("state")
            hash = movie.get("hash")
            if state == self.db.states["searching"]:
                continue
            torrents = self.qbit.torrents_info(status_filter=None, hashes=hash)
            if not torrents:  # Was deleted by user
                self.db.update_movie(id, state=self.db.states["deleted"])
            for torrent in torrents:
                if state == self.db.states["seeding"]:
                    time_since_added_sec = int(time.time()) - int(torrent["added_on"])
                    if time_since_added_sec > self.retention_preiod_sec:
                        self.qbit.delete(hash)
                        self.db.update_movie(id, state=self.db.states["completed"])
                elif torrent["state"] == "uploading":
                        self.db.update_movie(id, state=self.db.states["seeding"])

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
