from re import T
import qbittorrentapi


class QbittorrentClient:
    """
    QBitTorrent Client wrapper

    Attributes
    ----------
    host : str
        the listen address
    qbit: port
        the listen port

    """

    def __init__(self, host: str = "localhost", port: int = 8080) -> None:
        self.qbt_client = qbittorrentapi.Client(host="localhost", port=8080)

    def download(
        self, magnetic_uri: str, save_path: str, is_paused: bool = False
    ) -> None:
        """Downloads the file given by the magnetic_uri

        Args:
            magnetic_uri (str): the magnetic uri
            save_path (str): the file save path
            is_paused (bool, optional): true if the download should start as paused. 
            Defaults to False.
        """
        self.qbt_client.torrents_add(
            urls=magnetic_uri, save_path=save_path, is_paused=is_paused
        )
    

    def torrents_info(self, status_filter: str = "completed", hashes: str = None) -> list:
        """Get the list of torrents in QBittorrent

        Args:
            status_filter (str, optional): The torrent status (downloading, completed, paused, 
            active, inactive, resumed stalled, stalled_uploading and stalled_downloading). 
            Defaults to "completed". Set None to search for all.
            hashes(str, optional): The torret hashes to look for. Defaults to None (all)
        Returns:
            list: a list of torrents
        """
        return self.qbt_client.torrents_info(status_filter=status_filter, torrent_hashes=hashes)

    def delete(self, torrent_hashes: list) -> None:
        """Deletes the torrents given by the hash list

        Args:
            torrent_hashes (list): the hashes of the torrents to delete
        """
        self.qbt_client.torrents_delete(torrent_hashes=torrent_hashes)
    
    def stop(self, torrent_hashes: list) -> None:
        """Pauses the torrents given by the hash list

        Args:
            torrent_hashes (list): the hashes of the torrents to pause
        """
        self.qbt_client.torrents_pause(torrent_hashes=torrent_hashes)
    
    def resume(self, torrent_hashes: list) -> None:
        """Resumes the torrents given by the hash list

        Args:
            torrent_hashes (list): the hashes of the torrents to resume
        """
        self.qbt_client.torrents_resume(torrent_hashes)
