from collections import namedtuple
import sqlite3

import imdb


class TorrentState:
    SEARCHING = "SEARCHING"  # Still being searched
    DOWNLOADING = "DOWNLOADING"  # Currently being downloading
    SEEDING = "SEEDING"  # Currently uploading
    COMPLETED = "COMPLETED"  # Removed from seeding
    DELETING  = "DELETING" # Torrent marked for deletion
    PAUSED = "PAUSED" # Download stopped

    @staticmethod
    def get_states() -> list:
        return [
            TorrentState.SEARCHING,
            TorrentState.DOWNLOADING,
            TorrentState.SEEDING,
            TorrentState.COMPLETED,
            TorrentState.DELETING,
            TorrentState.PAUSED
        ]


class TBDatabase:
    """
    Database Handler

    Attributes
    ----------
    db_file_path : str
        the database file path (sqlite)

    """

    def __init__(self, db_file_path: str) -> None:
        self.db_file_path = db_file_path
        self.connection = sqlite3.connect(self.db_file_path)
        self.connection.row_factory = dict_factory
        self.states = TorrentState()

    def create_schema(self) -> None:
        """Initializes the database by creating the necessary schema.

        Args:
            db_file (str): the file to were the database state will be stored
        """

        cur = self.connection.cursor()
        # Create Movies table
        sql = f"""CREATE TABLE IF NOT EXISTS movies (
            "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
            "name" TEXT UNIQUE NOT NULL,
            "max_size_mb" INTEGER NOT NULL,
            "resolution_profile"	TEXT NOT NULL,
            "state" TEXT NOT NULL DEFAULT '{self.states.SEARCHING}',
            "imdbid"	TEXT NOT NULL,
            "hash" TEXT)
        """
        cur.execute(sql)

        # Create TV Shows Table
        sql = f"""CREATE TABLE IF NOT EXISTS tv_shows (
            "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
            "name" TEXT UNIQUE NOT NULL,
            "max_episode_size_mb" INTEGER NOT NULL,
            "resolution_profile"	TEXT NOT NULL,
            "imdbid"	TEXT NOT NULL,
            "state" TEXT NOT NULL DEFAULT '{self.states.SEARCHING}'
        )
        """
        cur.execute(sql)

        # Create TV Show seasons
        sql = f"""CREATE TABLE IF NOT EXISTS tv_show_seasons (
            "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
            "show_id" INTEGER,
            "season_number" INTEGER NOT NULL,
            "season_number_episodes" INTEGER NOT NULL,
            "state" TEXT NOT NULL DEFAULT '{self.states.SEARCHING}',
            "hash" TEXT,
            FOREIGN KEY(show_id) REFERENCES tv_shows(id),
            UNIQUE(show_id, season_number))
        """
        cur.execute(sql)

         # Create TV Show season episodes
        sql = f"""CREATE TABLE IF NOT EXISTS tv_show_season_episodes (
            "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
            "season_id" INTEGER,
            "episode_number" INTEGER NOT NULL,
            "air_date" TEXT NOT NULL,
            "state" TEXT NOT NULL DEFAULT '{self.states.SEARCHING}',
            "hash" TEXT,
            FOREIGN KEY(season_id) REFERENCES tv_show_seasons(id),
            UNIQUE(season_id, episode_number))
        """
        cur.execute(sql)

        # Create tv shows with seasons view
        sql = f"""CREATE VIEW IF NOT EXISTS tv_shows_with_seasons_view
            AS
            SELECT 
                tv_shows.id as show_id,
                tv_shows.name as show_name,
                tv_shows.state as show_state,
                tv_shows.resolution_profile as resolution_profile,
                tv_shows.name as show_name,
                tv_shows.max_episode_size_mb as max_episode_size_mb,
                tv_show_seasons.id as season_id,
                tv_show_seasons.season_number as season_number,
                tv_show_seasons.season_number_episodes as season_number_episodes,
                tv_show_seasons.state as season_state,
                tv_show_seasons.hash as season_hash
            FROM tv_shows
            INNER JOIN tv_show_seasons on tv_shows.id = tv_show_seasons.show_id;
        """
        cur.execute(sql)

        # Create seaons with episodes view
        sql = f"""CREATE VIEW IF NOT EXISTS tv_show_seasons_with_episodes_view
            AS
            SELECT 
                tv_show_seasons.id as season_id,
                tv_show_seasons.hash as season_hash,
                tv_show_seasons.state as season_state,
                tv_show_season_episodes.id as episode_id,
                tv_show_season_episodes.episode_number as episode_number,
                tv_show_season_episodes.state as episode_state,
                tv_show_season_episodes.hash as episode_hash
            FROM tv_show_seasons
            INNER JOIN tv_show_season_episodes on tv_show_seasons.id = tv_show_season_episodes.season_id;
        """
        cur.execute(sql)

        # commit changes and close the connection
        self.connection.commit()

    def get_movies_by_state(self, state: str) -> list:
        """Retrieves all movies stored in the database with the specified state

        Args:
            state (str): the state (must match a valid state)

        Returns:
            list: the list of movies
        """
        if state not in self.states.get_states():
            raise Exception(f"Non allowed state={state}!")
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM movies WHERE state=?", (state,))
        return cur.fetchall()
    
    def get_tv_shows_by_state(self, state: str) -> list:
        """Retrieves all tv shows stored in the database with the specified state

        Args:
            state (str): the state (must match a valid state)

        Returns:
            list: the list of tv shows
        """
        if state not in self.states.get_states():
            raise Exception(f"Non allowed state={state}!")
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_shows WHERE state=?", (state,))
        return cur.fetchall()
    
    def get_tv_show_with_seasons_by_state(self, state: str) -> list:
        if state not in self.states.get_states():
            raise Exception(f"Non allowed state={state}!")
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_shows_with_seasons_view WHERE season_state=?", (state,))
        return cur.fetchall()

    def get_all_movies(self) -> list:
        """Retreives all movies

        Returns:
            list: the the list of movies
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM movies")
        return cur.fetchall()
    
    def get_all_tv_shows(self) -> list:
        """Retreives all tv shows

        Returns:
            list: the list of tv shows
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_shows;")
        return cur.fetchall()
    
    def get_all_seasons(self) -> list:
        """Retreives all tv show seasons

        Returns:
            list: the list of seasons
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_show_seasons;")
        return cur.fetchall()
    
    def get_all_episodes(self) -> list:
        """Retreives all episodes

        Returns:
            list: the list of episdoes
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_show_season_episodes;")
        return cur.fetchall()

    def get_all_tv_shows_with_seasons(self) -> list:
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_shows_with_seasons_view;")
        return cur.fetchall()
    
    def get_tv_show_with_seasons(self, id: str) -> list:
        """Retreives all seasons for the tv show with the sepecified id

        Args:
            id (str): the tv show id

        Returns:
            list: the list of seasons
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * from tv_shows_with_seasons_view WHERE show_id=?", (id,))
        return cur.fetchall()

    def get_movie(self, id: str) -> dict:
        """retreives a movie

        Args:
            id (str): the id of the movie to retreive

        Returns:
            dict: the movie
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM movies WHERE id=?", (id,))
        return cur.fetchone()
    
    def get_tv_show(self, id: str) -> dict:
        """retreives a tv show

        Args:
            id (str): the id of the tv show to retreive

        Returns:
            dict: the tv show
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_shows WHERE id=?", (id,))
        return cur.fetchone()

    def delete_movie(self, id: str) -> None:
        """Delete a movie

        Args:
            id (str): the id of the movie to delete
        """
        cur = self.connection.cursor()
        cur.execute("DELETE FROM movies WHERE id=?", (id,))
        self.connection.commit()
    
    def delete_tv_show(self, id: str) -> None:
        """Delete a tv show

        Args:
            id (str): the id of the tv show to delete
        """
        cur = self.connection.cursor()
        cur.execute("DELETE FROM tv_shows WHERE id=?", (id,))
        self.connection.commit()
    
    def delete_season(self, id: str):
        cur = self.connection.cursor()
        cur.execute("DELETE FROM tv_show_seasons WHERE id=?", (id,))
        self.connection.commit()

    def add_movie(self, name: str, max_size_mb: int, resolution_profile: str) -> None:
        """Adds a movie to the database

        Args:
            name (str): the movie name
            max_size_mb (int): the movie max size in megabytes
            resolution_profile (str): the desired resolutions
        """
        cur = self.connection.cursor()
        cur.execute(
            """
                INSERT INTO movies(name,max_size_mb,resolution_profile)
                VALUES(?,?,?)
                """,
            (name, max_size_mb, resolution_profile),
        )
        self.connection.commit()

    def add_tv_show(self, name: str, max_episode_size_mb: int, resolution_profile: str, imdbid: str) -> None:
        """Adds a tv show to the database

        Args:
            name (str): the tv show name
            max_episode_size_mb (int): the  max size of an episode
            resolution_profile (str): the desired resolutions
            imdbid (str): the imdb id
        """
        cur = self.connection.cursor()
        cur.execute(
            """
                INSERT INTO tv_shows(name,max_episode_size_mb,resolution_profile, imdbid)
                VALUES(?,?,?,?)
                """,
            (name, max_episode_size_mb, resolution_profile, imdbid),
        )
        self.connection.commit()
    

    def add_tv_show_season(self, show_id: str, season_number: str, season_number_episodes: int):
        """Add tv show season

        Args:
            show_id (str): the tv show id
            season_number (str): the season number
        """
        cur = self.connection.cursor()
        cur.execute(
            """
                INSERT INTO tv_show_seasons(show_id,season_number, season_number_episodes)
                VALUES(?,?,?)
                """,
            (show_id, season_number, season_number_episodes),
        )
        self.connection.commit()
        return  cur.execute('SELECT last_insert_rowid() as id').fetchone()['id']
    
    def add_season_episode(self, season_id: str, episode_number: int, air_date: str ):
        """Add a new episode

        Args:
            season_id (str): _description_
            episode_number (int): _description_
            air_date (str): _description_
        """
        cur = self.connection.cursor()
        cur.execute(
            """
                INSERT INTO tv_show_season_episodes(season_id, episode_number, air_date)
                VALUES(?,?,?)
                """,
            (season_id, episode_number, air_date),
        )
        self.connection.commit()
        return  cur.execute('SELECT last_insert_rowid() as id').fetchone()['id']

    def get_season_id(self, show_id: str, season_number: int):
        cur = self.connection.cursor()
        row = cur.execute(
            """
            SELECT id FROM tv_show_seasons WHERE show_id=? AND season_number=?
            """,
            (show_id, season_number),
        ).fetchone()
        return row['id']

    def update_movie(self, id: str, **kwargs: dict) -> None:
        """[summary]

        Args:
            id (str): The movie identifier

        Raises:
            Exception: if the kwargs is empty or none or if the key arguments don't correspond to
            a database column
        """
        movie_table_columns = ["name", "max_size_mb", "resolution_profile", "state", "hash", "imdbid"]
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        columns_to_update = ""
        values = ()
        if not kwargs:
            raise Exception("At least one argument must be specified")

        for key, value in kwargs.items():
            if key not in movie_table_columns:
                raise Exception(
                    f"The key argument must be one of the following: {movie_table_columns}"
                )
            columns_to_update += f"{key}=?, "
            values += (value,)
        values += (id,)
        columns_to_update = columns_to_update[:-2]

        cur.execute(
            f"UPDATE movies SET {columns_to_update} WHERE id=?",
            values,
        )
        self.connection.commit()
    
    def update_tv_show(self, id: str, **kwargs: dict) -> None:
        """[summary]

        Args:
            id (str): The tv show id

        Raises:
            Exception: if the kwargs is empty or none or if the key arguments don't correspond to
            a database column
        """
        tv_shows_table_columns = ["name", "max_episode_size_mb", "resolution_profile", "state", "imdbid1"]
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        columns_to_update = ""
        values = ()
        if not kwargs:
            raise Exception("At least one argument must be specified")

        for key, value in kwargs.items():
            if key not in tv_shows_table_columns:
                raise Exception(
                    f"The key argument must be one of the following: {tv_shows_table_columns}"
                )
            columns_to_update += f"{key}=?, "
            values += (value,)
        values += (id,)
        columns_to_update = columns_to_update[:-2]

        cur.execute(
            f"UPDATE tv_shows SET {columns_to_update} WHERE id=?",
            values,
        )
        self.connection.commit()

    def update_show_season(self, id, **kwargs: dict) -> None:
        tv_show_season_table_columns = [ "season_number", "season_number_episodes", "state", "hash"]
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        columns_to_update = ""
        values = ()
        if not kwargs:
            raise Exception("At least one argument must be specified")

        for key, value in kwargs.items():
            if key not in tv_show_season_table_columns:
                raise Exception(
                    f"The key argument must be one of the following: {tv_show_season_table_columns}"
                )
            columns_to_update += f"{key}=?, "
            values += (value,)
        values += (id,)
        columns_to_update = columns_to_update[:-2]

        cur.execute(
            f"UPDATE tv_show_seasons SET {columns_to_update} WHERE id=?",
            values,
        )
        self.connection.commit()
    
    def update_tv_show_season_episode(self, id, **kwargs: dict) -> None:
        tv_show_season_episode_table_columns = [ "season_id", "episode_number", "air_date", "state", "hash"]
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        columns_to_update = ""
        values = ()
        if not kwargs:
            raise Exception("At least one argument must be specified")

        for key, value in kwargs.items():
            if key not in tv_show_season_episode_table_columns:
                raise Exception(
                    f"The key argument must be one of the following: {tv_show_season_episode_table_columns}"
                )
            columns_to_update += f"{key}=?, "
            values += (value,)
        values += (id,)
        columns_to_update = columns_to_update[:-2]

        cur.execute(
            f"UPDATE tv_show_season_episodes SET {columns_to_update} WHERE id=?",
            values,
        )
        self.connection.commit()

    def get_season_states(self, show_id: str):
        cur = self.connection.cursor()
        cur.execute("SELECT season_state FROM tv_shows_with_seasons_view WHERE show_id=?", (show_id,))
        result =  cur.fetchall()
        state_set = set()
        for row in result:
            state_set.add(row['season_state'])
        return state_set

    def close(self) -> None:
        """Close database connection"""
        self.connection.close()
    

    def get_tv_show_season_numbers(self, id: str) -> set:
        cur = self.connection.cursor()
        cur.execute("SELECT season_number FROM tv_show_seasons WHERE show_id=?", (id,))
        result =  cur.fetchall()
        seasons = set()
        for row in result:
            seasons.add(row['season_number'])
        return seasons

    def get_tv_show_season_episode_numbers(self, id) -> set:
        cur = self.connection.cursor()
        cur.execute("SELECT episode_number FROM tv_show_season_episodes WHERE season_id=?", (id,))
        result =  cur.fetchall()
        episodes = set()
        for row in result:
            episodes.add(row['episode_number'])
        return episodes
    
    def get_season_episodes(self, season_id):
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_show_season_episodes WHERE season_id=?", (season_id,))
        result = cur.fetchall()
        return result


def dict_factory(cursor, row) -> dict:
    """Transform tuple rows into a dictionary with column names and values

    Args:
        cursor: database cursor
        row: row

    Returns:
        dict: a dictionary containing the column names as keys and the respective values
    """
    output = {}
    for idx, col in enumerate(cursor.description):
        output[col[0]] = row[idx]
    return output


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python database.py <db_path>", file=sys.stderr)
        exit(0)

    db = TBDatabase(sys.argv[1])
    db.create_schema()
    print(db.get_all_movies())
    db.close()
