import imdb


class IMDBFinder:
    """_summary_
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
        return self.finder.search_movie(title)

    def update_with_seasons(self, series: object) -> None:
        """Updates the specified series object with the seasons and episodes

        Args:
            series (object): the series
        """
        self.finder.update(series, 'episodes')
    
    def get_show_info(self, show_title: str) -> object:
        """Search for the show with the specified title and update 
        it with the respective seasons and episodes

        Args:
            show_title (str): the show title

        Returns:
            object: the show object
        """
        show = self.search(show_title)
        self.update_with_seasons(show)
        return show


if __name__ == '__main__':
    finder = IMDBFinder()
    movies = finder.search('The twilight zone')
    for movie in movies:
        print(movie.get('title'))
        print(movie.get('full-size cover url'))
        if 'series' in movie['kind']:
            finder.update_with_seasons(movie)
            print(f"seasons:{len(movie['episodes'].keys())}")
            for season in movie['episodes']:
                print(f"Season:{season}")
                for episode in movie['episodes'][season]:
                    print(f"Episode:{episode}")
                    print(movie['episodes'][season][episode]['long imdb episode title'])
                    if 'original air date' in movie['episodes'][season][episode]:
                        print(movie['episodes'][season][episode]['original air date'])
                    if 'year' in movie['episodes'][season][episode]:
                        print(movie['episodes'][season][episode]['year'])
