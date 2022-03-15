import logging
import time
from abc import ABC, abstractmethod
from tools import JackettClient
from tools import QbittorrentClient
from data import TBDatabase
from requests.exceptions import ConnectionError
from imdb._exceptions import IMDbDataAccessError


class Probe(ABC):
    """
    Torrent Bot Probe (Abs)

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
    storage_dir: str
        the path were the data will be stored
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
            storage_dir: str,
            retention_period_sec: int,
    ) -> None:
        self.jackett = JackettClient(jackett_api_key, jackett_api_url)
        self.qbit = QbittorrentClient(qbit_hostname, qbit_port)
        self.db = TBDatabase(data_path)
        self.storage_dir = storage_dir
        self.retention_period_sec = retention_period_sec

    def start(self) -> None:
        """Starts the probe which initiates the search, download and update
        """
        try:
            self.probe()
            self.update()
        except ConnectionError:
            logging.info(f"Failed to reach jackett!")
        except IMDbDataAccessError:
            logging.error(f"Failed to find show information on imdb")

    @abstractmethod
    def probe(self):
        pass

    @abstractmethod
    def update(self):
        pass

    def update_torrent_states(self, id: int, hash: str, current_state: str, type: str) -> None:
        """Update the db states to match the torrent states and vice-versa.

        Args:
            id (int): the id
            hash (str): the torrent hash
            current_state (str): the current state
            type (str): Either SEASON, EPISODE or MOVIE
        """
        if type not in ['SEASON', 'EPISODE', 'MOVIE']:
            raise Exception(f"invalid type: {type}")

        new_state = current_state
        torrents = self.qbit.torrents_info(status_filter=None, hashes=hash)

        # If it can't find the torrent, it was deleted manually by the user, delete from db as well
        if not torrents:
            self._delete_db_entry(id, type)

        for torrent in torrents:
            # Remove torrent marked for deleting
            if new_state == self.db.states.DELETING:
                self.qbit.delete(hash)
                self._delete_db_entry(id, type)

            # State changed from paused, therefore resume
            if current_state != self.db.states.PAUSED and 'paused' in torrent["state"].lower():
                self.qbit.resume(hash)

            # Remove the torrent (not the files) if it is older than the retention period
            if current_state == self.db.states.SEEDING:
                time_since_added_sec = int(time.time()) - int(torrent["added_on"])
                if time_since_added_sec > self.retention_period_sec:
                    self.qbit.delete(hash)
                    self._update_db_entry_state(id, type, self.db.states.COMPLETED)

            # Change the torrent state if it finished the download and it's now uploading
            if current_state == self.db.states.DOWNLOADING and torrent["state"] == "uploading":
                self._update_db_entry_state(id, type, self.db.states.SEEDING)

            # Stop download for torrents stopped
            if current_state == self.db.states.PAUSED and 'paused' not in torrent["state"].lower():
                self.qbit.stop(hash)

    def _delete_db_entry(self, id: int, type: str) -> None:
        """Delete an EPISODE, SEASON or MOVIE

        Args:
            id (int): the id of the databse
            type (str): the type (EPISODE, SEASON or MOVIE)
        """
        if type == 'EPISODE':
            self.db.delete_episode(id)
        elif type == 'SEASON':
            self.db.delete_season(id)
        elif type == 'MOVIE':
            self.db.delete_movie(id)

    def _update_db_entry_state(self, id: int, type: str, new_state: str) -> None:
        """Update an EPISODE, SEASON or MOVIE state

        Args:
            id (int): the id of the databse
            type (str): the type (EPISODE, SEASON or MOVIE)
        """
        if type == 'EPISODE':
            self.db.update_tv_show_season_episode(id, state=new_state)
        elif type == 'SEASON':
            self.db.update_show_season(id, state=new_state)
        elif type == 'MOVIE':
            self.db.update_movie(id, state=new_state)

    def mb_to_bytes(self, value: int) -> int:
        """convert the specified value int megabytes to bytes

        Args:
            value (int): the value in megabytes

        Returns:
            [int]: the value in byes
        """
        return value * 1024 * 1024

    def shutdown(self) -> None:
        """Close resources"""
        self.db.close()
