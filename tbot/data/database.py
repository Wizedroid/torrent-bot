import sqlite3


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
        self.SEARCHING = "SEARCHING"
        self.DOWNLOADING = "DOWNLOADING"
        self.SEEDING = "SEEDING"
        self.COMPLETED = "COMPLETED"
        self.states = [self.SEARCHING, self.DOWNLOADING, self.SEEDING, self.COMPLETED]

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
            "state" TEXT NOT NULL DEFAULT '{self.SEARCHING}')
        """
        cur.execute(sql)

        # commit changes and close the connection
        self.connection.commit()

    def get_movies(self, state: str) -> list:
        """Retrieves all movies stored in the database

        Returns:
            list: the list of movies
        """
        if state not in self.states:
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
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM movies")
        return cur.fetchall()

    def update_movie(
        self, id: str, name: str, max_size_mb: int, resolutions: str, state: str
    ) -> None:
        """Updates a movie entry in the database with the specified id

        Args:
            id (str): the movie identifier
            name (str): the movie name
            max_size_mb (int): the movie max size
            resolutions (str): the resolution profile
            state (str): the movie state
        """
        self.connection.row_factory = dict_factory
        cur = self.connection.cursor()
        cur.execute(
            "UPDATE movies SET name=?, max_size_mb=?, resolutions=?, state=? WHERE id=?",
            (name, max_size_mb, resolutions, state, id),
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
