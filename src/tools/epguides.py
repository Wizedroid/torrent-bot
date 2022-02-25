from urllib.parse import quote
from itsdangerous import json
import requests

class EPGuidesClient:

    def __init__(self) -> None:
        self.base_url = "https://epguides.frecar.no"

    def get_show_info(self, name: str) -> dict:
        encoded_name = EPGuidesClient.encode(name)
        result = requests.get(f"{self.base_url}/show/{encoded_name}")
        result.raise_for_status()
        return result.json()

    @staticmethod
    def encode(name: str) -> str:
        return quote(name.strip().lower())

if __name__ == '__main__':
    epgclient = EPGuidesClient()
    info = epgclient.get_show_info('The twilight zone')
    print(info['1'][0])