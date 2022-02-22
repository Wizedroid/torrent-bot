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

    def torrents_info(self, status_filter: str = "completed") -> list:
        """Get the list of torrents in QBittorrent

        Args:
            status_filter (str, optional): The torrent status (downloading, completed, paused, 
            active, inactive, resumed stalled, stalled_uploading and stalled_downloading). 
            Defaults to "completed".
        Returns:
            list: a list of torrents
        """
        return self.qbt_client.torrents_info(status_filter=status_filter)

    def delete(self, torrent_hashes: list) -> None:
        """Deletes the torrents given by the hash list

        Args:
            torrent_hashes (list): the hashes of the torrents to delete
        """
        self.qbt_client.torrents_delete(torrent_hashes=torrent_hashes)


qbit = QbittorrentClient()
# qbit.download('magnet:?xt=urn:btih:9BFAB920305925F9954D8C4B9DEDCD4C6B12FFEA&dn=Gladiator+(2000)+%5BEXTENDED%5D+1080p+BrRip+x264+-+1.6GB+-+YIFY&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2F9.rarbg.to%3A2710%2Fannounce&tr=udp%3A%2F%2Ftracker.internetwarriors.net%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.cyberia.is%3A6969%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce&tr=udp%3A%2F%2Fexplodie.org%3A6969%2Fannounce&tr=http%3A%2F%2Ftracker1.itzmx.com%3A8080%2Fannounce&tr=udp%3A%2F%2Ftracker.tiny-vps.com%3A6969%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce', save_path='/Users/pedro/Downloads')
# print(qbit.torrents_info('active'))
