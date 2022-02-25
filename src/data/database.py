from collections import namedtuple
import sqlite3


class TorrentState:
    SEARCHING = "SEARCHING"  # Still being searched
    DOWNLOADING = "DOWNLOADING"  # Currently being downloading
    SEEDING = "SEEDING"  # Currently uploading
    COMPLETED = "COMPLETED"  # Removed from seeding

    @staticmethod
    def get_states() -> list:
        return [
            TorrentState.SEARCHING,
            TorrentState.DOWNLOADING,
            TorrentState.SEEDING,
            TorrentState.COMPLETED
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
        # Create Movies table (state must be in (SEARCHING; DOWNLOADING; SEEDING; COMPLETED))
        sql = f"""CREATE TABLE IF NOT EXISTS movies (
            "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
            "name" TEXT UNIQUE NOT NULL,
            "max_size_mb" INTEGER NOT NULL,
            "resolutions"	TEXT NOT NULL,
            "state" TEXT NOT NULL DEFAULT '{self.states.SEARCHING}',
            "hash" TEXT)
        """
        cur.execute(sql)

        # commit changes and close the connection
        self.connection.commit()

    def get_movies(self, state: str) -> list:
        """Retrieves all movies stored in the database

        Returns:
            list: the list of movies
        """
        if state not in self.states.get_states():
            raise Exception(f"Non allowed state={state}!")
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM movies WHERE state=?", (state,))
        return cur.fetchall()

    def get_all_movies(self) -> list:
        """Retreives all movies

        Returns:
            list: the the list of movies
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM movies")
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

    def delete_movie(self, id: str) -> None:
        """Delete a movie

        Args:
            id (str): the id of the movie to delete
        """
        cur = self.connection.cursor()
        cur.execute("DELETE FROM movies WHERE id=?", (id,))
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
    print(db.get_movies())
    db.close()
