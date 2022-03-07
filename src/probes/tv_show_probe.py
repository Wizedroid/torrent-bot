import time
import logging
from datetime import datetime
from requests.models import HTTPError
from tools import JackettClient
from tools import QbittorrentClient
from tools import EPGuidesClient
from data import TBDatabase
from utils import config

class TVShowProbe:
    """
    TV Show probe

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
    tv_shows_storage_probe: str
        the path were the TV Shows will be stored
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
        tv_shows_storage_dir: str,
        retention_preiod_sec: int,
    ) -> None:
        self.jackett = JackettClient(jackett_api_key, jackett_api_url)
        self.qbit = QbittorrentClient(qbit_hostname, qbit_port)
        self.db = TBDatabase(data_path)
        self.epguides = EPGuidesClient()
        self.tv_shows_storage_dir = tv_shows_storage_dir
        self.retention_preiod_sec = retention_preiod_sec

    @staticmethod
    def new(config: config):
        """Create a new tv show probe directly from the config

        Args:
            config (config): the configuration parameters for the application

        Returns:
            TvShowProbe: The tv show probe
        """
        return TVShowProbe(
            config.jackett.api_key,
            config.jackett.api_url,
            config.qbit.hostname,
            config.qbit.port,
            config.DB_PATH,
            config.shows.directory,
            config.shows.rentention_period_sec,
        )

    def start(self) -> None:
        """Starts the probe which initiates the search, download and update
        of tv shows
        """
        self.probe()
        self.update()

    def probe(self) -> None:
        """Search and download tv shows added to the databse (state=SEARCHING)
        """
        # Search for all seaons and episodes of each added TV Show
        for show in self.db.get_all_tv_shows():
            show_id = show.get('id')
            show_name = show.get('name')
            max_episode_size_bytes = self.mb_to_bytes(show.get("max_episode_size_mb"))
            show_resolution_profile = set(show.get("resolution_profile").split(','))
            seasons = self.db.get_tv_show_with_seasons(show_id)
            season_numbers = [season['season_number'] for season in seasons]
            try:
                epguide_show_info = self.epguides.get_show_info(show_name)
                # Seach for missing seasons
                for season in [season_number for season_number in epguide_show_info.keys() if int(season_number) not in season_numbers]:
                    if self.is_season_complete(epguide_show_info[season]):
                        self.db.add_tv_show_season(show_id, season, len(epguide_show_info[season]))
            except HTTPError as error:
                logging.error(f"Failed to find TV Show: {show_name}!")
        
            # Download full seasons (@TODO support for individual episodes)
            for season in seasons:
                season_state = season['season_state']
                season_id = season['season_id']
                season_number = season['season_number']
                season_number_episodes = season['season_number_episodes']
                if season_state == self.db.states.SEARCHING:
                    hash = self.download_full_season(show_name, season_number, max_episode_size_bytes*season_number_episodes, show_resolution_profile)
                    if hash:
                        self.db.update_show_season(
                            id=season_id,
                            state=self.db.states.DOWNLOADING,
                            hash=hash,
                        )

    def is_season_complete(self, episodes: list):
        last_episode_date = datetime.strptime(episodes[len(episodes)-1]['release_date'], "%Y-%m-%d")
        return (datetime.now() - last_episode_date).days > 2 # 2 days buffer
    
    def download_full_season(self, name, season, max_season_size_mb, resolution_profile):
        jackett_result = self.jackett.search_tvseries(
                        name=name,
                        season=int(season),
                        resolution_profile=resolution_profile,
                        max_size_bytes=self.mb_to_bytes(max_season_size_mb),
                        min_number_seeds=2)
        if jackett_result:
            tv_show = jackett_result[0]  # Highest number of seeds
            magnetUri = tv_show["MagnetUri"]
            self.qbit.download(magnetUri, self.tv_shows_storage_dir)
            return tv_show["InfoHash"]
        else:
            logging.info(f"TV Show {name} not found!")

    def update(self) -> None:
        """Updates the database state to reflect the current downloads
        """
        #(@TODO !refractor this method and clean!)
        

        # Remove all torrents for deleted series
        tv_shows = self.db.get_tv_shows_with_state(self.db.states.DELETING)
        for show in tv_shows:
            seasons = self.db.get_tv_show_with_seasons(show['id'])
            for season in seasons:
                if season['season_hash']:
                    self.qbit.delete(season['season_hash'])
            self.db.delete_tv_show(show['id'])

        seasons = self.db.get_all_tv_shows_with_seasons()
        for season in seasons:
            show_id = season.get("show_id")
            show_state = season.get('show_state')

            show_season_states = self.db.get_season_states(show_id=show_id)
            if self.db.states.SEARCHING in show_season_states:
                self.db.update_tv_show(show_id, state=self.db.states.SEARCHING)
            elif self.db.states.DOWNLOADING in show_season_states:
                self.db.update_tv_show(show_id, state=self.db.states.DOWNLOADING)
            elif self.db.states.PAUSED in show_season_states:
                self.db.update_tv_show(show_id, state=self.db.states.PAUSED)
            if len(show_season_states)==1 and not show_state in show_season_states:
                if self.db.states.COMPLETED in show_season_states:
                    self.db.update_tv_show(show_id, state=self.db.states.COMPLETED)
                elif self.db.states.SEEDING in show_season_states:
                    self.db.update_tv_show(show_id, state=self.db.states.SEEDING)

            # Update seasons state 
            season_id = season.get("season_id")
            season_state = season.get("season_state")
            season_hash = season.get("season_hash")

            # Do nothing with movies not found or already completed
            if season_state in [self.db.states.SEARCHING, self.db.states.COMPLETED]:
                continue
            
            # Check if the movies should change the state
            torrents = self.qbit.torrents_info(status_filter=None, hashes=season_hash)
            for torrent in torrents:
                # State changed from paused,  therefore reusme
                if season_state != self.db.states.PAUSED and 'paused' in torrent["state"].lower():
                    self.qbit.resume(season_hash)
                
                # Remove the torrent if it is older than the retention period
                if season_state == self.db.states.SEEDING: 
                    time_since_added_sec = int(time.time()) - int(torrent["added_on"])
                    if time_since_added_sec > self.retention_preiod_sec:
                        self.qbit.delete(season_hash)
                        self.db.update_show_season(season_id, state=self.db.states.COMPLETED)
                # Change the torrent state if it finished the download and it is now uploading
                elif season_state == self.db.states.DOWNLOADING and torrent["state"] == "uploading":
                    self.db.update_show_season(season_id, state=self.db.states.SEEDING)
                # Stop download for torrents stopped
                elif season_state == self.db.states.PAUSED and not 'paused' in torrent["state"].lower():
                    self.qbit.stop(season_hash)
    


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
