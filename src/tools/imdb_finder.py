import imdb


class IMDBFinder:
    """IMDB Finder
    """

    def __init__(self) -> None:
        self.finder = imdb.Cinemagoer()

    def search(self, title: str) -> object:
        """Search for the show/movie with the specified title
    
        Args:
            title (str): the show/movie title

        Returns:
            object: the movie object
        """
        results =  self.finder.search_movie(title)
        for result in results:
            result.data['imdbid'] = self.get_imdbid(result)
        return results
    
    def search_shows(self, show_title: str) -> set:
        """Search for the show with the specified title and update 
        it with the respective seasons and episodes

        Args:
            show_title (str): the show title

        Returns:
            set: the shows found
        """
        output = set()
        shows = self.search(show_title)
        for show in shows:
            if 'series' in show['kind'].lower():
                self.update_show_with_seasons(show)
                output.add(show)

        return output

    def fetch(self, imdbid: str) -> object:
        """Fetches the show/movie given by the specified imdb id

        Args:
            imdbid (str): the imdb unique identifier

        Returns:
            object: the show/movie object
        """
        return self.finder.get_movie(imdbid)

    def update_show_with_seasons(self, series: object) -> None:
        """Updates the specified series object with the seasons and episodes

        Args:
            series (object): the series
        """
        self.finder.update(series, 'episodes')

    def fetch_show(self, imdbid: str) -> object:
        """Fetches a show given by the specified imdb id

        Args:
            imdbid (str): the imdb id

        Returns:
            object: the show object
        """
        show = self.fetch(imdbid)
        self.update_show_with_seasons(show)
        return show

    def get_imdbid(self, entry: object) -> str:
        """Retreive the imdb for the specified entry (movie or show)

        Args:
            entry (object): the movie or show object

        Returns:
            str: the imdb id
        """
        return self.finder.get_imdbID(entry)

    def get_latest_tvshow_season(self, imdbid: str) -> tuple:
        """Retreives the tv show latest season

        season_info {
            <episode_number>:
                "title": <title>,
                "kind": "episode",
                "season": <season>,
                "episode": <episode_number>
                (...)
        }

        Args:
            imdbid (str): the show imdb id

        Returns:
            tuple: the season number, the season info
        """
        show = self.fetch_show(imdbid=imdbid)
        last_season = len(show['episodes'].keys())
        return (last_season, show['episodes'][last_season])


if __name__ == '__main__':
    finder = IMDBFinder()
    shows = finder.search_shows('Stranger Things')
    for show in shows:
        print("RAW DATA:")
        print(show.data.keys())  # dict_keys(['title', 'year', 'kind', 'cover url', 'episodes', 'number of episodes'])
        if 'episodes' in show.data:
            print(f"Number of seasons: {len(show['episodes'].keys())}")
            print(f"Number of episodes: {len(show['episodes'][1].keys())}")
            print(f"Episode data: {show['episodes'][1][1].keys()}") # ['title', 'kind', 'episode of', 'season', 'episode', 'rating', 'votes', 'original air date', 'year', 'plot', 'canonical title', 'long imdb title', 'long imdb canonical title', 'smart canonical title', 'smart long imdb canonical title', 'long imdb episode title', 'series title', 'canonical series title', 'episode title', 'canonical episode title', 'smart canonical series title', 'smart canonical episode title']