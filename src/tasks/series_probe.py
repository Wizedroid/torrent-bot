import time
import logging
from datetime import datetime
from requests.models import HTTPError
from tools import JackettClient
from tools import QbittorrentClient
from tools import EPGuidesClient
from data import TBDatabase

class TVSeriesProbe:
    """
    TV Series probe

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
    series_storage_dir: str
        the path were the TV Series will be stored
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
        series_storage_dir: str,
        retention_preiod_sec: int,
    ) -> None:
        self.jackett = JackettClient(jackett_api_key, jackett_api_url)
        self.qbit = QbittorrentClient(qbit_hostname, qbit_port)
        self.db = TBDatabase(data_path)
        self.epguides = EPGuidesClient()
        self.series_storage_dir = series_storage_dir
        self.retention_preiod_sec = retention_preiod_sec

    def start(self) -> None:
        """Starts the probe which initiates the search, download and update
        of movies
        """
        self.probe()
        self.update()

    def probe(self) -> None:
        """Search and download series added to the databse (state=SEARCHING)
        """
        # Search for all seaons and episodes of each added series
        for series_row in self.db.get_series_with_state(state=self.db.states.SEARCHING):
            series_id = series_row.get('id')
            series_name = series_row.get('name')
            series_max_season_size_mb = self.mb_to_bytes(series_row.get("max_season_size_mb"))
            series_resolution_profile = series_row.get("resolutions")
            seasons = self.db.get_tv_series_seasons(series_id)
            season_numbers = [season['season_number'] for season in seasons]
            epguide_show_info = self.epguides.get_show_info(series_name)
            # Seach for missing seasons
            for season in [season_number for season_number in epguide_show_info.keys() if int(season_number) not in season_numbers]:
                if self.is_season_complete(epguide_show_info[season]):
                    self.db.add_series_season(series_id, season)
        
            # Download full seasons (@TODO support for individual episodes)
            for season in seasons:
                season_state = season['state']
                season_id = season['id']
                season_number = season['season_number']
                if season_state == self.db.states.SEARCHING:
                    hash = self.download_full_season(series_name, season_number, series_max_season_size_mb, series_resolution_profile)
                    if hash:
                        self.db.update_series_season(
                            id=season_id,
                            state=self.db.states.DOWNLOADING,
                            hash=hash,
                        )

    def is_season_complete(self, episodes: list):
        last_episode_date = datetime.strptime(episodes[len(episodes)-1]['release_date'], "%Y-%m-%d")
        return (datetime.now() - last_episode_date).days > 2 # 2 days buffer
    
    def download_full_season(self, name, season, max_season_size_mb, resolutions):
        jackett_result = self.jackett.search_tvseries(
                        name=name,
                        season=int(season),
                        resolution_profile=resolutions,
                        max_size_bytes=self.mb_to_bytes(max_season_size_mb),
                        min_number_seeds=2)
        if jackett_result:
            series = jackett_result[0]  # Highest number of seeds
            magnetUri = series["MagnetUri"]
            self.qbit.download(magnetUri, self.series_storage_dir)
            return series["InfoHash"]
        else:
            logging.info(f"TV Series {name} not found!")

    def update(self) -> None:
       pass

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
