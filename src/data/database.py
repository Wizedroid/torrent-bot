from collections import namedtuple
import sqlite3


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
            "resolutions"	TEXT NOT NULL,
            "state" TEXT NOT NULL DEFAULT '{self.states.SEARCHING}',
            "hash" TEXT)
        """
        cur.execute(sql)

        # Create TV Series Table
        sql = f"""CREATE TABLE IF NOT EXISTS tv_series (
            "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
            "name" TEXT UNIQUE NOT NULL,
            "max_episode_size_mb" INTEGER NOT NULL,
            "resolutions"	TEXT NOT NULL,
            "state" TEXT NOT NULL DEFAULT '{self.states.SEARCHING}'
        )
        """
        cur.execute(sql)

        # Create TV series seasons
        sql = f"""CREATE TABLE IF NOT EXISTS tv_series_seasons (
            "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
            "series_id" INTEGER,
            "season_number" INTEGER NOT NULL,
            "season_number_episodes" INTEGER NOT NULL,
            "state" TEXT NOT NULL DEFAULT '{self.states.SEARCHING}',
            "hash" TEXT,
            FOREIGN KEY(series_id) REFERENCES tv_series(id),
            UNIQUE(series_id, season_number))
        """
        cur.execute(sql)

        # Create Complete tv series view
        sql = f"""CREATE VIEW IF NOT EXISTS tv_series_with_seasons_view
            AS
            SELECT 
                tv_series.id as series_id,
                tv_series.name as series_name,
                tv_series.state as series_state,
                tv_series_seasons.id as season_id,
                tv_series_seasons.season_number as season_number,
                tv_series_seasons.season_number_episodes as season_number_episodes,
                tv_series_seasons.state as season_state,
                tv_series_seasons.hash as season_hash
            FROM tv_series
            INNER JOIN tv_series_seasons on tv_series.id = tv_series_seasons.series_id;
        """
        cur.execute(sql)

        # commit changes and close the connection
        self.connection.commit()

    def get_movies_with_state(self, state: str) -> list:
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
    
    def get_series_with_state(self, state: str) -> list:
        """Retrieves all tv series stored in the database with the specified state

        Args:
            state (str): the state (must match a valid state)

        Returns:
            list: the list of tv series
        """
        if state not in self.states.get_states():
            raise Exception(f"Non allowed state={state}!")
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_series WHERE state=?", (state,))
        return cur.fetchall()

    def get_all_movies(self) -> list:
        """Retreives all movies

        Returns:
            list: the the list of movies
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM movies")
        return cur.fetchall()
    
    def get_all_series(self) -> list:
        """Retreives all tv series

        Returns:
            list: the list of tv series
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_series;")
        return cur.fetchall()
    
    def get_all_series_with_seasons(self) -> list:
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_series_with_seasons_view;")
        return cur.fetchall()
    
    def get_tv_series_with_seasons(self, series_id: str) -> list:
        """Retreives all seasons for the tv series with the sepecified id

        Args:
            id (str): the tv series id

        Returns:
            list: the list of seasons
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * from tv_series_with_seasons_view WHERE series_id=?", (series_id,))
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
    
    def get_series(self, id: str) -> dict:
        """retreives a tv series

        Args:
            id (str): the id of the tv series to retreive

        Returns:
            dict: the tv series
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM tv_series WHERE id=?", (id,))
        return cur.fetchone()

    def delete_movie(self, id: str) -> None:
        """Delete a movie

        Args:
            id (str): the id of the movie to delete
        """
        cur = self.connection.cursor()
        cur.execute("DELETE FROM movies WHERE id=?", (id,))
        self.connection.commit()
    
    def delete_series(self, id: str) -> None:
        """Delete a tv series

        Args:
            id (str): the id of the tv series to delete
        """
        cur = self.connection.cursor()
        cur.execute("DELETE FROM tv_series WHERE id=?", (id,))
        self.connection.commit()
    
    def delete_season(self, id: str):
        cur = self.connection.cursor()
        cur.execute("DELETE FROM tv_series_seasons WHERE id=?", (id,))
        self.connection.commit()

    def add_movie(self, name: str, max_size_mb: int, resolutions: str) -> None:
        """Adds a movie to the database

        Args:
            name (str): the movie name
            max_size_mb (int): the movie max size in megabytes
            resolutions (str): the desired resolutions
        """
        cur = self.connection.cursor()
        cur.execute(
            """
                INSERT INTO movies(name,max_size_mb,resolutions)
                VALUES(?,?,?)
                """,
            (name, max_size_mb, resolutions),
        )
        self.connection.commit()

    def add_series(self, name: str, max_episode_size_mb: int, resolutions: str) -> None:
        """Adds a tv series to the database

        Args:
            name (str): the tv seties name
            max_episode_size_mb (int): the  max size of an episode
            resolutions (str): the desired resolutions
        """
        cur = self.connection.cursor()
        cur.execute(
            """
                INSERT INTO tv_series(name,max_episode_size_mb,resolutions)
                VALUES(?,?,?)
                """,
            (name, max_episode_size_mb, resolutions),
        )
        self.connection.commit()
    

    def add_series_season(self, series_id: str, season_number: str, season_number_episodes: int):
        """Add series season

        Args:
            series_id (str): the series id
            season_number (str): the season number
        """
        cur = self.connection.cursor()
        cur.execute(
            """
                INSERT INTO tv_series_seasons(series_id,season_number, season_number_episodes)
                VALUES(?,?,?)
                """,
            (series_id, season_number, season_number_episodes),
        )
        self.connection.commit()

    def update_movie(self, id: str, **kwargs: dict) -> None:
        """[summary]

        Args:
            id (str): The movie identifier

        Raises:
            Exception: if the kwargs is empty or none or if the key arguments don't correspond to
            a database column
        """
        movie_table_columns = ["name", "max_size_mb", "resolutions", "state", "hash"]
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
    
    def update_series(self, id: str, **kwargs: dict) -> None:
        """[summary]

        Args:
            id (str): The tv series identifier

        Raises:
            Exception: if the kwargs is empty or none or if the key arguments don't correspond to
            a database column
        """
        tv_series_table_columns = ["name", "max_episode_size_mb", "resolutions", "state"]
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        columns_to_update = ""
        values = ()
        if not kwargs:
            raise Exception("At least one argument must be specified")

        for key, value in kwargs.items():
            if key not in tv_series_table_columns:
                raise Exception(
                    f"The key argument must be one of the following: {tv_series_table_columns}"
                )
            columns_to_update += f"{key}=?, "
            values += (value,)
        values += (id,)
        columns_to_update = columns_to_update[:-2]

        cur.execute(
            f"UPDATE tv_series SET {columns_to_update} WHERE id=?",
            values,
        )
        self.connection.commit()

    def update_series_season(self, id, **kwargs: dict) -> None:
        tv_series_season_table_columns = [ "season_number", "season_number_episodes", "state", "hash"]
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        columns_to_update = ""
        values = ()
        if not kwargs:
            raise Exception("At least one argument must be specified")

        for key, value in kwargs.items():
            if key not in tv_series_season_table_columns:
                raise Exception(
                    f"The key argument must be one of the following: {tv_series_season_table_columns}"
                )
            columns_to_update += f"{key}=?, "
            values += (value,)
        values += (id,)
        columns_to_update = columns_to_update[:-2]

        cur.execute(
            f"UPDATE tv_series_seasons SET {columns_to_update} WHERE id=?",
            values,
        )
        self.connection.commit()
    
    def get_season_states(self, series_id: str):
        cur = self.connection.cursor()
        cur.execute("SELECT season_state FROM tv_series_with_seasons_view WHERE series_id=?", (series_id,))
        result =  cur.fetchall()
        state_set = set()
        for row in result:
            state_set.add(row['season_state'])
        return state_set

    def close(self) -> None:
        """Close database connection"""
        self.connection.close()


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
