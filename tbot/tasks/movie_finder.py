import time


class MovieFinder:
    """
    Movie Finder Task. It uses jackett to search for torrents in the configured trackers and
    qbittorrent for downloading.

    Attributes
    ----------
    jackett : JackettClient
        the jacket client
    qbit: QbittorrentClient
        the qbittorrent client

    """

    def __init__(self, jackett, qbit, db) -> None:
        self.jackett = jackett
        self.qbit = qbit
        self.db = db

    def start_download(self, movies_dir: str) -> None:
        """Download the movies in the database whose status is SEARCHING 
        into the specified directory

        Args:
            movies_dir (str): the directory where the movies will be sotred
        """
        for movie in self.db.get_movies(state=self.db.SEARCHING):
            id = movie.get("id")
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
            if not movies:
                print(f"No torrents found for the movie with title {name}.")
            else:
                self.qbit.download(movies[0]["MagnetUri"], movies_dir)
                self.db.update_movie(
                    id=id,
                    name=name,
                    max_size_mb=max_size_mb,
                    resolutions=res,
                    state=self.db.DOWNLOADING,
                )

    def cleanup(self, retention_preiod_sec: int) -> None:
        """Remove completed torrents that were added before the specified retention period

        Args:
            retention_preiod_sec (int): retention period in seconds
        """
        # @TODO (update torrent state)
        completed_torrents = self.qbit.torrents_info("completed")
        torrents_to_delete = []
        for torrent in completed_torrents:
            time_since_added_sec = int(time.time()) - int(torrent["added_on"])
            if time_since_added_sec > retention_preiod_sec:
                torrents_to_delete.append(torrent["hash"])

        self.qbit.delete(torrents_to_delete)

    def shutdown(self) -> None:
        """Close resources
        """
        self.db.close()

    def mb_to_bytes(self, value: int) -> int:
        """convert the specified value int megabytes to bytes 

        Args:
            value (int): the value in megabytes

        Returns:
            [int]: the value in byes
        """
        return  value * 1024 * 1024

