import time

class MoviesBot:
    """
    A movie download bot. It uses jackett to search for torrents in the configured trackers and 
    qbittorrent for downloading.

    Attributes
    ----------
    jackett : JackettClient
        the jacket client
    qbit: QbittorrentClient
        the qbittorrent client

    """

    def __init__(self, jackett, qbit) -> None:
        self.jackett = jackett
        self.qbit = qbit
    
    def start_download(self, movies_dir: str, movies_list: list) -> None:
        """Download the specified movies list into the specified directory

        Args:
            movies_dir (str): the directory where the movies will be sotred
            movies_list (list): the movies list
        """
        for movie in movies_list:
            name = movie.get("name")
            max_size_bytes = movie.get("max_size_bytes", None)
            year = movie.get("year", None)
            res = movie.get(
                "res",
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
                max_size_bytes=max_size_bytes,
                year=year,
                lang=lang,
                min_number_seeds=2,
            )
            if not movies:
                print(f"No torrents found for the movie with title {name}.")
            else:
                # @TODO don't download movies already being downloaded
                self.qbit.download(movies[0]["MagnetUri"], movies_dir)

    def cleanup(self, retention_preiod_sec: int) -> None:
        """Remove completed torrents that were added before the specified retention period

        Args:
            retention_preiod_sec (int): retention period in seconds
        """
        completed_torrents = self.qbit.torrents_info("completed")
        torrents_to_delete = []
        for torrent in completed_torrents:
            time_since_added_sec = int(time.time()) - int(torrent['added_on'])
            if time_since_added_sec > retention_preiod_sec:
                torrents_to_delete.append(torrent['hash'])
        
        self.qbit.delete(torrents_to_delete)

    def shutdown(self) -> None:
        # No resources to clean
        pass