from audioop import maxpp
from re import S
from sqlite3.dbapi2 import Connection, Error
import threading
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import current_app, g
from data import TBDatabase
import sys
import sqlite3

from data.database import TBDatabase


class Visuals:
    """Torrent Bot Visuals using Flask's framework.

    Attributes
    ----------
    database_path : str
        the database file path (sqlite)
    secret_key : str
        the the app secret key
    resolution_profiles: set
        set of allowed resolutions
    """

    def __init__(self, database_path: str, secret_key: str, resolution_profiles: set):
        self.app = Flask(__name__)
        self.app.secret_key = secret_key
        self.app.config["DB"] = database_path
        self.app.teardown_appcontext(self.close_db)
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/index", "index", self.index)
        self.app.add_url_rule("/movies", "movies", self.movies)
        self.app.add_url_rule(
            "/edit_movie/<string:id>",
            "edit_movie",
            self.edit_movie,
            methods=["POST", "GET"],
        )
        self.app.add_url_rule(
            "/add_movie", "add_movie", self.add_movie, methods=["POST", "GET"]
        )
        self.app.add_url_rule(
            "/delete_movie/<string:id>",
            "delete_movie",
            self.delete_movie,
            methods=["POST", "DELETE"],
        )
        self.resolution_profiles = resolution_profiles

    def start(self) -> None:
        """Start the frontend

        Returns:
           None
        """
        thread = threading.Thread(
            target=lambda: self.app.run(debug=True, use_reloader=False)
        )
        thread.daemon=True
        thread.start()

    def index(self) -> str:
        """Index endpoint

        Returns:
            str: index.html template
        """
        return render_template("index.html")

    def movies(self) -> str:
        """Movies endpoint

        Returns:
            str: movies.html template
        """
        db = self.get_db()
        g.movies = db.get_all_movies()
        return render_template("movies.html")

    def edit_movie(self, id) -> str:
        """Edit Movie endpoint

        Returns:
            str: edit_movie.html template
        """
        db = self.get_db()
        g.id = id
        if request.method == "POST":
            name = request.form["name"]
            max_size_mb = request.form.get("max_size_mb", type=int)
            resolutions = request.form["resolutions"]
            valid_input = self.validate_movie_fields(name, max_size_mb, resolutions)
            if valid_input:
                db.update_movie(
                    id=id,
                    name=name,
                    max_size_mb=max_size_mb,
                    resolutions=resolutions,
                    state=db.states.SEARCHING,
                )
                flash("Movie Updated", "success")
                return redirect(url_for("movies"))
        data = db.get_movie(id)
        g.name = data["name"]
        g.max_size_mb = data["max_size_mb"]
        g.resolutions = data["resolutions"]
        g.resolution_options = self.resolution_profiles
        return render_template("edit_movie.html")

    def delete_movie(self, id: str) -> str:
        """Deletes a movie

        Args:
            id (str): the id of the movie to delete

        Returns:
            str: movies template page
        """
        db = self.get_db()
        db.delete_movie(id)
        flash("Movie Deleted", "success")
        return redirect(url_for("movies"))

    def add_movie(self) -> str:
        """Add movie endpoint

        Returns:
            str: add_movie.html template
        """
        if request.method == "POST":
            db = self.get_db()
            name = request.form["name"]
            max_size_mb = request.form.get("max_size_mb", type=int)
            resolutions = request.form["resolutions"]
            valid_input = self.validate_movie_fields(name, max_size_mb, resolutions)

            if valid_input:
                db.add_movie(name, max_size_mb, resolutions)
                flash("Movie Added", "success")
                return redirect(url_for("movies"))

        g.resolution_options = self.resolution_profiles
        return render_template("add_movie.html")

    def get_db(self) -> TBDatabase:
        """Get database

        Returns:
            [type]: [description]
        """
        if "db" not in g:
            g.db = TBDatabase(current_app.config["DB"])

        return g.db

    def close_db(self, error: Error) -> None:
        """Closes the database connection

        Args:
            error (Error): Error
        """
        db = g.pop("db", None)

        if db is not None:
            db.close()

    def validate_movie_fields(self, name: str, max_size_mb: int, resolutions: set):
        """Validates if the fields: name, max_size_mb and resolutions
        have the proper valyes.

        Args:
            name (str): The movie name, must have be leat 3 character long
            max_size_mb (int): max size of the movie in megabytes, must me equal or larger than 1
            resolutions (set): the resolution profiles

        Returns:
            boolean: true if the fields are valid, false otherwise
        """
        valid_input = True
        # Movie name
        name = request.form["name"]
        if len(name) < 3:
            valid_input = False
            flash("The name must have at least 3 characters", "danger")

        # Movie Maximum Size
        max_size_mb = request.form.get("max_size_mb", type=int)
        if max_size_mb < 1:
            valid_input = False
            flash("The max size must be at least 1 MB!", "danger")

        # Movie Resolution Set
        resolutions = request.form["resolutions"]
        if resolutions not in self.resolution_profiles:
            valid_input = False
            flash("Resolution profile not supported!", "danger")

        return valid_input


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python frontend.py <db_path>", file=sys.stderr)
        exit(0)

    t = TBFrontend(sys.argv[1], "test", {"1080p"})
