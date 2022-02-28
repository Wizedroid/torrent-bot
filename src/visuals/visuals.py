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
        self.app.add_url_rule("/tv_series", "tv_series", self.tv_series)
        self.app.add_url_rule(
            "/tv_series_seasons/<string:id>",
            "tv_series_seasons",
            self.tv_series_seasons,
        )
        self.app.add_url_rule(
            "/edit_movie/<string:id>",
            "edit_movie",
            self.edit_movie,
            methods=["POST", "GET"],
        )
        self.app.add_url_rule(
            "/edit_series/<string:id>",
            "edit_series",
            self.edit_series,
            methods=["POST", "GET"],
        )
        self.app.add_url_rule(
            "/add_movie", "add_movie", self.add_movie, methods=["POST", "GET"]
        )
        self.app.add_url_rule(
            "/add_series", "add_series", self.add_series, methods=["POST", "GET"]
        )
        self.app.add_url_rule(
            "/delete_movie/<string:id>",
            "delete_movie",
            self.delete_movie,
            methods=["POST", "DELETE"],
        )
        self.app.add_url_rule(
            "/delete_series/<string:id>",
            "delete_series",
            self.delete_series,
            methods=["POST", "DELETE"],
        )
        self.app.add_url_rule(
            "/delete_series_season/<string:series_id>/<string:season_id>",
            "delete_series_season",
            self.delete_series_season,
            methods=["POST", "DELETE"],
        )
        self.app.add_url_rule(
            "/set_series_complete/<string:id>",
            "set_series_complete",
            self.set_series_complete,
            methods=["GET", "POST"],
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
        thread.daemon = True
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

    def tv_series(self) -> str:
        """TV Series endpoint

        Returns:
            str: tv_series.html template
        """
        db = self.get_db()
        g.tv_series = db.get_all_series()
        return render_template("tv_series.html")

    def tv_series_seasons(self, id) -> str:
        """TV Series endpoint

        Returns:
            str: tv_series.html template
        """
        db = self.get_db()
        g.tv_series_seasons = db.get_tv_series_with_seasons(id)
        if g.tv_series_seasons:
            g.series_name = g.tv_series_seasons[0]['series_name']
        return render_template("tv_series_seasons.html")

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

    def edit_series(self, id: str) -> str:
        """Edit Series endpoint

        Returns:
            str: edit_series.html template
        """
        db = self.get_db()
        g.id = id
        if request.method == "POST":
            name = request.form["name"]
            max_episode_size_mb = request.form.get("max_episode_size_mb", type=int)
            resolutions = request.form["resolutions"]
            valid_input = self.validate_movie_fields(
                name, max_episode_size_mb, resolutions
            )
            if valid_input:
                db.update_series(
                    id=id,
                    name=name,
                    max_episode_size_mb=max_episode_size_mb,
                    resolutions=resolutions,
                )
                flash("Series Updated", "success")
                return redirect(url_for("tv_series"))
        data = db.get_series(id)
        g.name = data["name"]
        g.max_episode_size_mb = data["max_episode_size_mb"]
        g.resolutions = data["resolutions"]
        g.resolution_options = self.resolution_profiles
        return render_template("edit_series.html")

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

    def delete_series(self, id: str) -> str:
        """Deletes a movie

        Args:
            id (str): the id of the movie to delete

        Returns:
            str: movies template page
        """
        db = self.get_db()
        db.delete_series(id)
        flash("Tv Series Deleted", "success")
        return redirect(url_for("tv_series"))
    
    def delete_series_season(self, series_id, season_id):
        db = self.get_db()
        db.delete_series_season(series_id, season_id)
        flash("Tv Season deleted", "success")
        return redirect(url_for("tv_series_seasons",id=series_id))


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

    def add_series(self) -> str:
        """Add series endpoint

        Returns:
            str: add_series.html template
        """
        if request.method == "POST":
            db = self.get_db()
            name = request.form["name"]
            max_episode_size_mb = request.form.get("max_episode_size_mb", type=int)
            resolutions = request.form["resolutions"]
            valid_input = self.validate_movie_fields(
                name, max_episode_size_mb, resolutions
            )

            if valid_input:
                db.add_series(name, max_episode_size_mb, resolutions)
                flash("TV Series Added", "success")
                return redirect(url_for("tv_series"))

        g.resolution_options = self.resolution_profiles
        return render_template("add_series.html")
    
    def set_series_complete(self, id: str) -> str:
        """Set series state as complete

        Args:
            id (str): the series if

        Returns:
            str: tv series template page
        """
        db = self.get_db()
        db.update_series(id=id, state=db.states.COMPLETED)
        flash("Tv Series Marked as Completed!", "success")
        return redirect(url_for("tv_series"))

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
        if len(name) < 3:
            valid_input = False
            flash("The name must have at least 3 characters", "danger")

        # Movie Maximum Size
        if max_size_mb < 1:
            valid_input = False
            flash("The max size must be at least 1 MB!", "danger")

        # Movie Resolution Set
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
