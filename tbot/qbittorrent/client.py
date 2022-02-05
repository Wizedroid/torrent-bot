import qbittorrentapi

class QbittorrentClient:

    def __init__(self, host: str = 'localhost', port: int = 8080) -> None:
        self.qbt_client = qbittorrentapi.Client(
            host='localhost',
            port=8080
        )
    
    def download(self, magnetic_uri: str, save_path: str, is_paused: bool = False) -> None:
        self.qbt_client.torrents_add(urls=magnetic_uri, save_path=save_path, is_paused=is_paused)
    
    def torrents_info(self, status_filter: str = "completed") -> list:
        return self.qbt_client.torrents_info(status_filter=status_filter)

    def delete(self, torrent_hashes: list) -> None:
        self.qbt_client.torrents_delete(torrent_hashes=torrent_hashes)
