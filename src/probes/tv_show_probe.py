import logging
from datetime import datetime
from tools import IMDBFinder
from utils import config
from .probe import Probe


class TVShowProbe(Probe):
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
    tv_shows_storage_dir: str
        the path were the TV Shows will be stored
    retention_period_sec:int
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
            retention_period_sec: int,
    ) -> None:
        super().__init__(jackett_api_key, jackett_api_url, qbit_hostname,
                         qbit_port, data_path, tv_shows_storage_dir, retention_period_sec)
        self.imdb_finder = IMDBFinder()

    @staticmethod
    def new(config: config):
        """Create a new tv show probe directly from the resources

        Args:
            config (resources): the configuration parameters for the application

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

    def probe(self) -> None:
        """Search and download tv shows added to the database (state=SEARCHING)
        Only probe if the database 'state' column matches the self.db.states.SEARCHING state.
        """
        # Keep searching for new episodes and seasons while the show isn't complete
        for show in self.db.get_tv_shows_by_state(state=self.db.states.SEARCHING):
            self.search_seasons(show)

        # Search for the torrents of the seasons
        for season in self.db.get_tv_show_with_seasons_by_state(state=self.db.states.SEARCHING):
            self.download_season(season)

    def search_seasons(self, tv_show: dict) -> None:
        """Search for new seasons and episodes of the specified show

        Args:
            tv_show (dict): the tv show database entry
        """
        show_id = tv_show.get('id')
        show_imdbid = tv_show.get('imdbid')
        known_seasons = self.db.get_tv_show_season_numbers(show_id)
        imdb_show = self.imdb_finder.fetch_show(show_imdbid)

        # Search on imdb for all seasons of the show
        for imdb_season_number in imdb_show['episodes']:
            imdb_season = imdb_show['episodes'][imdb_season_number]
            if imdb_season_number not in known_seasons:
                season_id = self.db.add_tv_show_season(
                    show_id=show_id,
                    season_number=imdb_season_number,
                    season_number_episodes=len(imdb_season))
            else:
                season_id = self.db.get_season_id(show_id,
                                                  season_number=imdb_season_number)
                self.db.update_show_season(season_id,
                                           season_number_episodes=len(imdb_season.keys()))

            # Update with new episodes added during the season release
            known_episodes = self.db.get_tv_show_season_episode_numbers(season_id)
            for episode in imdb_season:
                if episode not in known_episodes and 'original air date' in imdb_season[episode]:
                    self.db.add_season_episode(
                        season_id=season_id,
                        episode_name=imdb_season[episode]['title'],
                        episode_number=episode,
                        air_date=imdb_season[episode]['original air date'])

    def download_season(self, season: dict) -> None:
        """Download all the available episodes for the specified season.

        Note: A show is never downloaded as a whole @TODO

        Args:
            season (dict): the tv show season database entry
        """
        season_id = season['season_id']
        season_number = season['season_number']
        season_number_episodes = season['season_number_episodes']
        show_resolution_profile = set(season.get("resolution_profile").split(','))
        max_episode_size_bytes = self.mb_to_bytes(season["max_episode_size_mb"])
        show_name = season['show_name']
        imdbid = season['show_imdbid']

        episodes = self.db.get_season_episodes(season_id=season_id)
        # Download full season (if available)
        if episodes and self.is_season_complete(episodes):
            hash = self.download(show_name,
                                 season_number,
                                 max_episode_size_bytes * season_number_episodes,
                                 show_resolution_profile,
                                 imdbid)
            if hash:
                self.db.update_show_season(
                    id=season_id,
                    state=self.db.states.DOWNLOADING,
                    hash=hash)
        # Download individual episodes (if full season wasn't available)
        else:
            for episode in episodes:
                if episode['state'] == self.db.states.SEARCHING:
                    episode_number = episode['episode_number']
                    hash = self.download(
                        show_name,
                        season_number,
                        max_episode_size_bytes,
                        show_resolution_profile,
                        imdbid,
                        episode_number=episode_number)
                    if hash:
                        self.db.update_tv_show_season_episode(
                            id=season_id,
                            state=self.db.states.DOWNLOADING,
                            hash=hash)

    def is_season_complete(self, episodes: list) -> bool:
        """Checks if the specified list of episodes for a season
        is complete. A season is considered complete if none of the episodes
        was individually downloaded before and the last episode in the season
        was already released. 

        Args:
            episodes (list): the list of episodes

        Returns:
            bool: true if the season is complete, false otherwise
        """
        for episode in episodes:
            if episode['state'] != self.db.states.SEARCHING:
                return False

        last_episode_number = len(episodes)

        try:
            last_episode_date = self.parse_date(episodes[last_episode_number - 1]['air_date'].replace('.', ''))
            return (datetime.now() - last_episode_date).days > 0
        except ValueError as e:
            logging.error(e)
            return False

    def download(self, name: str,
                 season: int,
                 max_size_bytes: int,
                 resolution_profile: set,
                 imdbid: int,
                 episode_number: int = None) -> str:
        """Download the season for the specified show (name).

        Args:
            name (str): the name of the show
            season (int): the season number
            max_season_size_mb (int): max season size in megabytes
            resolution_profile (set): resolution profile
            episode_number (int, optional): The episode number. Defaults to None.

        Returns:
            str: The torrent hash
        """
        jackett_result = self.jackett.search_tvseries(
            name=name,
            season=season,
            resolution_profile=resolution_profile,
            max_size_bytes=max_size_bytes,
            min_number_seeds=2,
            episode=episode_number,
            imdbid=imdbid)
        if jackett_result:
            tv_show = jackett_result[0]  # Highest number of seeds
            magnetUri = tv_show["MagnetUri"]
            self.qbit.download(magnetUri, self.storage_dir)
            return tv_show["InfoHash"]
        else:
            logging.debug(f"TV Show {name}.S{season}.E{episode_number} not found!")

    def update(self) -> None:
        """Updates the database state to reflect the current downloads
        """

        # Update tv show season episodes
        episodes = self.db.get_all_episodes()
        for episode in episodes:
            episode_id = episode['id']
            episode_state = episode['state']
            episode_hash = episode['hash']
            season_id = episode['season_id']
            # If there's episodes with no hash, 
            # it means that the season was downloaded as a whole or the episode hasn't been released
            # in both cases, match the episode state with season state
            if not episode_hash:
                season_state = self.db.get_tv_show_season(season_id)['state']
                self.db.update_tv_show_season_episode(episode_id, state=season_state)
                continue
            # Do nothing
            if episode_state in [self.db.states.SEARCHING, self.db.states.COMPLETED]:
                continue

            self.update_torrent_states(episode_id, episode_hash, episode_state, type='EPISODE')

        # Update tv show seasons
        seasons = self.db.get_all_seasons()
        for season in seasons:
            season_id = season['id']
            season_state = season['state']
            season_hash = season['hash']
            season_episodes_states = self.db.get_season_episodes_states(season_id)
            # If there's no season hash, it means that the episodes were downloaded individually
            if not season_hash:
                new_show_state = self.calculate_parent_state(season_state, season_episodes_states)
                self.db.update_show_season(season_id, state=new_show_state)
                continue
            # Do nothing
            if season_state in [self.db.states.SEARCHING, self.db.states.COMPLETED]:
                continue

            self.update_torrent_states(season_id, season_hash, season_state, type='SEASON')

        # Update tv show
        shows = self.db.get_all_tv_shows()
        for show in shows:
            show_id = show['id']
            show_state = show['state']
            show_season_states = self.db.get_season_states(show_id=show_id)
            new_show_state = self.calculate_parent_state(show_state, show_season_states)
            if new_show_state == self.db.states.DELETING or show_state == self.db.states.DELETING:
                self.db.delete_tv_show(show_id)
            else:
                self.db.update_tv_show(show_id, state=new_show_state)

    def calculate_parent_state(self, current_parent_state: str, child_states: set) -> str:
        """Updates the parent (show or season) state to reflect the child
        states (season or episode)

        Args:
            current_parent_state (str): the current parent state
            child_states (set): the children state set

        Returns:
            str: the new parent state
        """
        parent_state = current_parent_state
        if self.db.states.SEARCHING in child_states:
            parent_state = self.db.states.SEARCHING
        elif self.db.states.DOWNLOADING in child_states:
            parent_state = self.db.states.DOWNLOADING
        elif self.db.states.PAUSED in child_states:
            parent_state = self.db.states.PAUSED
        if len(child_states) == 1 and not current_parent_state in child_states:
            if self.db.states.COMPLETED in child_states:
                parent_state = self.db.states.COMPLETED
            elif self.db.states.SEEDING in child_states:
                parent_state = self.db.states.SEEDING
            elif self.db.states.DELETING in child_states:
                parent_state = self.db.states.DELETING

        return parent_state

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

    @staticmethod
    def parse_date(date_text: str):
        for fmt in ("%d %b %Y", '%Y', '%d/%m/%Y', '%Y-%m-%d',  '%d%m%Y'):
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                pass
        raise ValueError(f'Failed to parse date {date_text}')