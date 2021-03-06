from typing import List
import requests
import json
import re


class JackettClient:
    """
    A wrapper client for jackett api cals

    Attributes
    ----------
    api_key : str
        the jacket api key
    api_url : str
        the jacket api url

    """

    def __init__(self, api_key: str, api_url="http://127.0.0.1:9117/api/v2.0") -> None:
        self.api_key = api_key
        self.api_url = api_url

    def search_movies(
        self,
        name: str,
        resolution_profile: list,
        max_size_bytes: int = None,
        year: str = None,
        lang: str = None,
        min_number_seeds: int = None,
        imdbid: int = None
    ) -> list:
        """Searches Jackett for a movie with the specified characteristics.

        Args:
            name (str): the name of the movie
            resolution_profile (list): The resolution profile, check the docs for details
            max_size_bytes (int, optional): the maximum size of the movie in bytes
            year (str, optional):  The year when the movie was released.
            lang (str, optional): The desired language
            min_number_seeds (int, optional): The minimum seeds
            imdbid (int, optional) the movie imdbid

        Returns:
            list: a list of movies sorted by Seeders, ascending
        """
        movies = []
        for res in resolution_profile:
            if res.lower() == 'any':
                query = name
            else:
                query = f"{name}+{res}"

            request_url = f"{self.api_url}/indexers/all/results?"\
                f"apikey={self.api_key}&"\
                f"query={query}&"\
                f"category=2000"
            result = requests.get(request_url)
            result.raise_for_status()
            contents = result.json()
            if len(contents["Results"]) > 0:
                for result in contents["Results"]:
                    size = result["Size"]
                    title = result["Title"].lower()
                    seeders = result['Seeders']
                    tracker_imdb = result['Imdb']
                    if max_size_bytes is not None and size > max_size_bytes:
                        continue
                    if year is not None and year not in title:
                        continue
                    if lang is not None and lang.lower() not in title:
                        continue
                    if min_number_seeds is not None and seeders < min_number_seeds:
                        continue
                    if imdbid and tracker_imdb and tracker_imdb != imdbid:
                        continue
                    movies.append(result)
        return sorted(movies, key=lambda i: i['Seeders'], reverse=True)

    def search_tvseries(
        self,
        name: str,
        resolution_profile: set,
        season: int,
        max_size_bytes: int = None,
        lang: str = None,
        min_number_seeds: int = None,
        episode: int = None,
        imdbid: int = None
    ) -> list:
        """Searches Jackett for a TV Series with the specified characteristics.

        Args:
            name (str): The name of the TV Series
            resolution_profile (set): The resolution profile, check the docs for details
            season (int): The season
            max_size_bytes (int, optional): the maximum size of the TV Series in bytes
            lang (str, optional): The desired language
            min_number_seeds (int, optional): The minimum seeds
            episode(int, optional): The episode number
            imdbid (int, optional) the movie imdbid
        Returns:
            list: [description]
        """
        tv_series = []
        for res in resolution_profile:
            if res.lower() == 'any':
                query = name
            else:
                query = f"{name}+{res}"

            request_url = f"{self.api_url}/indexers/all/results?"\
                f"apikey={self.api_key}&"\
                f"query={query}&"\
                f"category=5000"
            result = requests.get(request_url)
            result.raise_for_status()
            contents = result.json()
            if len(contents["Results"]) > 0:
                for result in contents["Results"]:
                    size = result["Size"]
                    title = result["Title"].lower()
                    seeders = result['Seeders']
                    tracker_imdb = result['Imdb']
                    if max_size_bytes is not None and size > max_size_bytes:
                        continue
                    if lang is not None and lang.lower() not in title:
                        continue
                    if min_number_seeds is not None and seeders < min_number_seeds:
                        continue
                    if not re.search(f"(season|s).?[0-9]?{season}", title):
                        continue
                    if not episode and re.search(f"(episode|ep|e).?[0-9]+", title):
                        continue
                    if episode and not re.search(f"(episode|ep|e).?0*{episode}", title):
                        continue
                    if imdbid and tracker_imdb and tracker_imdb != imdbid:
                        continue
                    tv_series.append(result)
        return sorted(tv_series, key=lambda i: i['Seeders'], reverse=True)
