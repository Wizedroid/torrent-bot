from sqlite3.dbapi2 import Error
import threading
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import current_app, g
from tools import IMDBFinder, imdb_finder
from data.database import TBDatabase
from utils import config


class Visuals:
    """Torrent Bot Frontend (aka visuals) using Flask's framework.

    Attributes
    ----------
    database_path : str
        the database file path (sqlite)
    secret_key : str
        the the app secret key
    resolution_profiles: set
        set of allowed resolution_profile
    hostname: str
        the listen address for the frontend
    port: int
        the listen port for the frontend
    """

    def __init__(self, database_path: str, secret_key: str,
                 resolution_profiles: set, hostname: str, port: int):
        self.app = Flask(__name__)
        self.app.secret_key = secret_key
        self.app.config["DB"] = database_path
        self.app.teardown_appcontext(self.close_db)
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/index", "index", self.index)
        self.app.add_url_rule("/movies", "movies", self.movies)
        self.app.add_url_rule("/tv_shows", "tv_shows", self.tv_shows)
        self.app.add_url_rule("/tv_show_seasons/<string:id>",
                              "tv_show_seasons", self.tv_show_seasons)
        self.app.add_url_rule("/tv_show_season_episodes/<string:id>",
                              "tv_show_season_episodes", self.tv_show_season_episodes)
        self.app.add_url_rule("/edit_movie/<string:id>",
                              "edit_movie", self.edit_movie, methods=["POST", "GET"])
        self.app.add_url_rule("/edit_tv_show/<string:id>", "edit_tv_show",
                              self.edit_tv_show, methods=["POST", "GET"])
        self.app.add_url_rule("/add_movie", "add_movie",
                              self.add_movie, methods=["POST", "GET"])
        self.app.add_url_rule("/add_tv_show", "add_tv_show",
                              self.add_tv_show, methods=["POST", "GET"])
        self.app.add_url_rule("/delete_movie/<string:id>", "delete_movie",
                              self.delete_movie, methods=["POST", "DELETE"])
        self.app.add_url_rule("/pause_movie/<string:id>", "pause_movie",
                              self.pause_movie, methods=["POST", "DELETE"])
        self.app.add_url_rule("/resume_movie/<string:id>", "resume_movie",
                              self.resume_movie, methods=["POST", "DELETE"])
        self.app.add_url_rule("/delete_tv_show/<string:id>", "delete_tv_show",
                              self.delete_tv_show, methods=["POST", "DELETE"])
        self.app.add_url_rule("/pause_season/<string:id>/<string:show_id>",
                              "pause_season", self.pause_season, methods=["POST", "DELETE"])
        self.app.add_url_rule("/resume_season/<string:id>/<string:show_id>",
                              "resume_season", self.resume_season, methods=["POST", "DELETE"])
        self.app.add_url_rule("/search", "search", self.search)
        self.resolution_profiles = resolution_profiles
        self.imdb_finder = IMDBFinder()
        self.hostname = hostname
        self.port = port

    @staticmethod
    def new(config: config):
        """Create a new Visuals object directly from the config

        Args:
            config (config): the configuration parameters for the application

        Returns:
            Visuals: The visuals object
        """
        return Visuals(
            config.DB_PATH, config.frontend.secret_key, config.RES_PROFILES, config.frontend.hostname, config.frontend.port
        )

    def start(self) -> None:
        """Start the frontend

        Returns:
           None
        """
        thread = threading.Thread(target=lambda:
                                  self.app.run(debug=True,
                                               use_reloader=False,
                                               host=self.hostname,
                                               port=self.port))
        thread.daemon = True
        thread.start()

    def index(self) -> str:
        """Index endpoint

        Returns:
            str: index.html page
        """
        return render_template("index.html")

    def movies(self) -> str:
        """Movies endpoint

        Returns:
            str: movies.html page
        """
        db = self.get_db()
        g.movies = db.get_all_movies()
        return render_template("movies.html")

    def tv_shows(self) -> str:
        """TV Shows endpoint

        Returns:
            str: tv_shows.html page
        """
        db = self.get_db()
        g.tv_shows = db.get_all_tv_shows()
        return render_template("tv_shows.html")

    def tv_show_seasons(self, id: int) -> str:
        """TV Show seaons endpoint

        Returns:
            int: tv_show_seaons.html page
        """
        db = self.get_db()
        g.tv_show_seasons = db.get_tv_show_with_seasons(id)
        if g.tv_show_seasons:
            g.show_name = g.tv_show_seasons[0]['show_name']
        return render_template("tv_show_seasons.html")
    
    def tv_show_season_episodes(self, id: int) -> str:
        db = self.get_db()
        g.show_id = db.get_tv_show_season(id)['show_id']
        g.tv_show_season_episodes = db.get_tv_show_season_with_episodes(id)
        if g.tv_show_season_episodes:
            g.season_number = g.tv_show_season_episodes[0]['season_number']
        return render_template("tv_show_season_episodes.html")

    def edit_movie(self, id) -> str:
        """Edit Movie endpoint

        Returns:
            str: edit_movie.html page or movies.html page in case of a successful update
        """
        db = self.get_db()
        g.id = id
        if request.method == "POST":
            max_size_mb = request.form.get("max_size_mb", type=int)
            resolution_profile = request.form["resolution_profile"]
            imdbid = request.form.get("imdbid", type=int)
            cover_url = request.form["cover_url"]
            valid_input = self.validate_fields(max_size_mb, resolution_profile, imdbid)
            if valid_input:
                db.update_movie(
                    id=id,
                    max_size_mb=max_size_mb,
                    resolution_profile=resolution_profile,
                    state=db.states.SEARCHING,
                    imdbid=imdbid,
                    cover_url=cover_url
                )
                flash("Movie Updated", "success")
                return redirect(url_for("movies"))
        data = db.get_movie(id)
        g.name = data["name"]
        g.max_size_mb = data["max_size_mb"]
        g.resolution_profile = data["resolution_profile"]
        g.imdbid = data['imdbid']
        g.cover_url = data['cover_url']
        g.resolution_options = self.resolution_profiles
        return render_template("edit_movie.html")

    def edit_tv_show(self, id: str) -> str:
        """Edit Tv show endpoint

        Returns:
            str: edit_tv_show.html page
        """
        db = self.get_db()
        g.id = id
        if request.method == "POST":
            max_episode_size_mb = request.form.get("max_episode_size_mb", type=int)
            resolution_profile = request.form["resolution_profile"]
            imdbid = request.form.get("imdbid", type=int)
            cover_url = request.form['cover_url']
            valid_input = self.validate_fields(max_episode_size_mb, resolution_profile, imdbid)
            if valid_input:
                db.update_tv_show(
                    id=id,
                    max_episode_size_mb=max_episode_size_mb,
                    resolution_profile=resolution_profile,
                    imdbid=imdbid,
                    cover_url=cover_url
                )
                flash("Tv show Updated", "success")
                return redirect(url_for("tv_shows"))
        data = db.get_tv_show(id)
        g.name = data["name"]
        g.max_episode_size_mb = data["max_episode_size_mb"]
        g.resolution_profile = data["resolution_profile"]
        g.resolution_options = self.resolution_profiles
        g.imdbid = data['imdbid']
        g.cover_url = data['cover_url']
        return render_template("edit_tv_show.html")

    def delete_movie(self, id: str) -> str:
        """Delete movie endpoint

        Args:
            id (str): the id of the movie to delete

        Returns:
            str: movies.html page
        """
        db = self.get_db()
        db.update_movie(id, state=db.states.DELETING)
        flash("Movie Marked for deletion!", "success")
        return redirect(url_for("movies"))

    def pause_movie(self, id: str) -> str:
        """Pause movie endpoint

        Args:
            id (str): the movie id to pause

        Returns:
            str:  movies.html page
        """
        db = self.get_db()
        db.update_movie(id, state=db.states.PAUSED)
        flash("Movie Paused", "success")
        return redirect(url_for("movies"))

    def resume_movie(self, id: str) -> str:
        """Resume movie endpoint

        Args:
            id (str): the movie id

        Returns:
            str: the movies.html page
        """
        db = self.get_db()
        db.update_movie(id, state=db.states.SEARCHING)
        flash("Movie Download Resumed", "success")
        return redirect(url_for("movies"))

    def delete_tv_show(self, id: str) -> str:
        """Delete tv show endpoint

        Args:
            id (str): the id of the tv show to delete

        Returns:
            str: tv_shows.html page
        """
        db = self.get_db()
        db.update_tv_show(id=id, state=db.states.DELETING)
        flash("Tv Show Marked for deletion", "success")
        return redirect(url_for("tv_shows"))

    def pause_season(self, id: str, show_id: str):
        """Pause season endpoint

        Args:
            id (str): the season id
            show_id (str): the show id

        Returns:
            str: tv_show_seasons.html page
        """
        db = self.get_db()
        db.update_show_season(id, state=db.states.PAUSED)
        flash("Tv Season Paused", "success")
        return redirect(url_for("tv_show_seasons", id=show_id))

    def resume_season(self, id: str, show_id: str):
        """Resume season endpoint

        Args:
            id (str): the season id
            show_id (str): the show id

        Returns:
            str: tv_show_seasons.html page
        """
        db = self.get_db()
        db.update_show_season(id, state=db.states.SEARCHING)
        flash("Tv Season download resumed", "success")
        return redirect(url_for("tv_show_seasons", id=show_id))

    def add_movie(self) -> str:
        """Add movie endpoint

        Returns:
            str: add_movie.html page
        """
        if request.method == "POST":
            db = self.get_db()
            name = request.form["name"]
            max_size_mb = request.form.get("max_size_mb", type=int)
            resolution_profile = request.form["resolution_profile"]
            imdbid = request.form.get("imdbid", type=int)
            cover_url = request.form.get("cover_url", default="")
            valid_input = self.validate_fields(max_size_mb, resolution_profile, imdbid, name)
            if valid_input:
                db.add_movie(name, max_size_mb, resolution_profile, imdbid, cover_url)
                flash("Movie Added", "success")
                return redirect(url_for("movies"))
        g.name = request.args.get('name', default="")
        g.imdbid = request.args.get('imdbid', default="")
        g.cover_url = request.args.get('cover_url', default="")
        g.resolution_options = self.resolution_profiles
        return render_template("add_movie.html")

    def add_tv_show(self) -> str:
        """Add tv show endpoint

        Returns:
            str: tv_shows.html page
        """
        if request.method == "POST":
            db = self.get_db()
            name = request.form["name"]
            max_episode_size_mb = request.form.get("max_episode_size_mb", type=int)
            resolution_profile = request.form["resolution_profile"]
            imdbid = request.form.get("imdbid", type=int)
            cover_url = request.form["cover_url"]
            valid_input = self.validate_fields(max_episode_size_mb, resolution_profile, imdbid, name)

            if valid_input:
                db.add_tv_show(name, max_episode_size_mb, resolution_profile, imdbid, cover_url)
                flash("TV Show Added", "success")
                return redirect(url_for("tv_shows"))

        g.name = request.args.get('name', default="")
        g.imdbid = request.args.get('imdbid', default="")
        g.cover_url = request.args.get('cover_url', default="")
        g.resolution_options = self.resolution_profiles
        return render_template("add_tv_show.html")

    def search(self):
        """Search shows/movies endpoint

        Returns:
            str: search.html page
        """
        search_query = request.args.get('search')
        g.results = self.imdb_finder.search(search_query)
        return render_template('search.html')

    def get_db(self) -> TBDatabase:
        """Get database

        Returns:
            TBDatabase: Torrent Bot Database
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

    def validate_fields(self, max_size_mb: int, resolution_profile: set,  imdbid: int, name: str = None):
        """Validates if the fields: name, max_size_mb and resolution_profile
        have the proper valyes.

        Args:
            name (str): The movie name, must have be leat 3 character long
            max_size_mb (int): max size of the movie in megabytes, must me equal or larger than 1
            resolution_profile (set): the resolution profiles

        Returns:
            boolean: true if the fields are valid, false otherwise
        """
        valid_input = True
        # Movie name
        if name and len(name) < 3:
            valid_input = False
            flash("The name must have at least 3 characters", "danger")

        # Movie Maximum Size
        if max_size_mb < 1:
            valid_input = False
            flash("The max size must be at least 1 MB!", "danger")
        
        # IMDB ID
        if type(imdbid) != int:
            valid_input = False
            flash("The imdb id mustbe an integer!", "danger")

        # Movie Resolution Set
        if resolution_profile not in self.resolution_profiles:
            valid_input = False
            flash("Resolution profile not supported!", "danger")

        return valid_input


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python frontend.py <db_path>", file=sys.stderr)
        exit(0)

    t = Visuals(sys.argv[1], "secret_key", {"1080p"}, "localhost", 5000)
