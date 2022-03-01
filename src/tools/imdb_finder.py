import imdb


class IMDBFinder:

    def __init__(self) -> None:
        self.finder = imdb.Cinemagoer()

    
    def search(self, title: str):
        return self.finder.search_movie(title)
    

if __name__ == '__main__':
    finder = IMDBFinder()
    movies = finder.search('stranger')
    for movie in movies:
        print(movie.get('title'))
        print(movie.get('full-size cover url'))