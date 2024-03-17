# CREATE RANDOM GAME @ SPOTLE.IO

import random,requests,json
from base64 import b64encode

client_id = '7039fa9e3ff9490fae786fd557679ad5'
client_secret = '60c22025159943a3818f404fdce76da4'


# GET RANDOM SPOTIFY ARTIST FROM TOP 1000 ARTISTS
def get_random_artist(token):
    import random
    import requests
    import json

    # GET TOP 1000 ARTISTS
    url = 'https://api.spotify.com/v1/playlists/37i9dQZEVXbMDoHDwVN2tF'
    headers = {
        'Authorization': 'Bearer ' + token
    }
    response = requests.get(url, headers=headers)
    artists = response.json()['tracks']['items']
    artist = random.choice(artists)['track']['artists'][0]['name']
    return artist

def get_token():
    url = 'https://accounts.spotify.com/api/token'
    client_creds = b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    headers = {
        'Authorization': f'Basic {client_creds}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json()['access_token']

def get_chrome_driver():
    import selenium
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    return driver


if __name__ == '__main__':
    token = get_token()
    artist = get_random_artist(token)
    print(artist)