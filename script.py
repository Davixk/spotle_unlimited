# CREATE RANDOM GAME @ SPOTLE.IO

import random,requests,json,logging,os,urllib3,webbrowser
from base64 import b64encode
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlencode
from base64 import b64encode

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger

client_id = '7039fa9e3ff9490fae786fd557679ad5'
client_secret = '60c22025159943a3818f404fdce76da4'
OUTPUT_FOLDER = 'output'
DEFAULT_LINK = 'https://spotle.io'
DEFAULT_MESSAGE = "Created by Dave's script with <3"
DEFAULT_SAMPLE_SIZE = 250


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

def save_to_json(data, filename):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = filename.split('.')[0] + '_' + timestamp + '.json'
    output_path = os.path.join(OUTPUT_FOLDER, filename)
    with open(output_path, 'w') as f:
        json.dump(data, f)

def get_top_2500_artists():
    response = requests.get('https://kworb.net/spotify/listeners.html')
    soup = BeautifulSoup(response.text)
    table_class = "addpos sortable"
    table = soup.find('table', {'class': table_class})
    # get tbody
    tbody = table.find('tbody')
    # get all rows
    rows = tbody.find_all('tr')
    # artist name = second column - chart position = first column
    top_2500_artists_namesonly = []
    top_2500_artists = []
    for row in rows:
        tds = row.find_all('td')
        artist_name = tds[0].text
        artist = {
            'name': artist_name,
            'listeners': tds[1].text,
            'daily_trend': tds[2].text,
            'peak': tds[3].text,
            'peak_listeners': tds[4].text,
        }
        top_2500_artists_namesonly.append(artist_name)
        top_2500_artists.append(artist)
    save_to_json(top_2500_artists, 'top_2500_artists.json')
    return top_2500_artists_namesonly

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

def get_chrome_driver(options=None):
    if not options:
        options = Options()
        options.headless = True
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    driver = webdriver.Chrome(options=options)
    return driver

def setup_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename='script.log',
                        level=logging.DEBUG,
                        format=log_format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger('').addHandler(console_handler)
    # selenium logs to info
    selenium_logger.setLevel(logging.INFO)
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.INFO)

def create_new_game(
    driver = None,
    artist_name = None,
    message = DEFAULT_MESSAGE,
    link = DEFAULT_LINK,
    ):
    if not driver:
        driver = get_chrome_driver()
    if not artist_name:
        artist = get_random_artist(get_token())
        artist_name = artist['name']
    driver.get(link)

    button_class = "challenge-btn"
    condition = EC.element_to_be_clickable((By.CLASS_NAME, button_class))
    WebDriverWait(driver, 10).until(condition).click()

    input_name = "search"
    condition = EC.visibility_of_element_located((By.NAME, input_name))
    WebDriverWait(driver, 10).until(condition)
    input_field = driver.find_element(By.NAME, input_name)
    input_field.send_keys(artist_name + Keys.ENTER)

    try:
        message_text = "Artist not in Spotify's Top 1000"
        error_message = WebDriverWait(driver, 1).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'info-prompt'))
        )
        if error_message and error_message.text == message_text:
            raise ValueError(f"Invalid artist name: {artist_name}. Please retry")
    except:
        challenge_form_class = "challenge-form"
        condition = EC.visibility_of_element_located((By.CLASS_NAME, challenge_form_class))
        WebDriverWait(driver, 10).until(condition)
        input_field = driver.find_element(By.CLASS_NAME, challenge_form_class)
        input_field.send_keys(message)

        share_button_class = "challenge-share-btn"
        condition = EC.element_to_be_clickable((By.CLASS_NAME, share_button_class))
        WebDriverWait(driver, 10).until(condition).click()
        # button uses Share feature from browser
        # we need to wait for the share window to open

        logs = driver.get_log('browser')
        source_file = "app.js"
        string = f'{link}/{source_file}'
        artist_source_line = " 1262:10"
        message_source_line = " 1263:10"
        spotle_logs = []
        artist_code = None
        message_code = None
        for log in logs:
            if log['message'].startswith(string):
                spotle_logs.append(log)
                restof_log = log['message'][len(string):]
                if restof_log.startswith(artist_source_line):
                    artist_code = restof_log[len(artist_source_line):].strip().strip('"')
                elif restof_log.startswith(message_source_line):
                    message_code = restof_log[len(message_source_line):].strip().strip('"')
        if artist_code and message_code:
            return artist_code, message_code
        else:
            raise Exception('Artist or message code not found. Please retry')
    finally:
        driver.quit()

def get_game_link(artist_code, message_code=None, link=DEFAULT_LINK):
    if not message_code:
        message_code = encode(DEFAULT_MESSAGE)
    params = {
        'artist': artist_code,
        'msg': message_code
    }
    encoded_params = urlencode(params)
    game_link = f'{link}?{encoded_params}'
    logging.info(f'Game link: {game_link}')
    return game_link

def encode(string):
    bytes_to_encode = string.encode('utf-8')
    encoded = b64encode(bytes_to_encode).decode('utf-8')
    return encoded

def open_game_link(game_link):
    webbrowser.open_new_tab(game_link)

def main():
    top_2500_artists = get_top_2500_artists()
    difficulty = input("Choose your difficulty : \n1. Super Easy (50)\n2. Easy (100)\n3. Medium (250)\n4. Hard (500)\n5. Super Hard (1000)\n")
    if difficulty == '1':
        sample_size = 50
    elif difficulty == '2':
        sample_size = 100
    elif difficulty == '3':
        sample_size = 250
    elif difficulty == '4':
        sample_size = 500
    elif difficulty == '5':
        sample_size = 1000
    else:
        sample_size = DEFAULT_SAMPLE_SIZE
    logging.debug(f'Sample size: {sample_size}')
    top_artists = top_2500_artists[:sample_size]
    
    success = False
    driver = get_chrome_driver()
    while not success:
        try:
            random_artist = random.choice(top_artists)
            position = top_2500_artists.index(random_artist) + 1
            logging.info(f'Random artist: {random_artist} - Position: {position}')
            
            # NOW WE PLAY SPOTLE.IO
            artist_code, message_code = create_new_game(
                driver=driver,
                artist_name=random_artist,
            )
            game_link = get_game_link(
                artist_code=artist_code,
                message_code=message_code
            )
            open_game_link(game_link)
            success = True
        except ValueError as e:
            logging.warning(f"{e}. Rerolling...")


if __name__ == '__main__':
    setup_logging()
    main()