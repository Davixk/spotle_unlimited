# CREATE RANDOM GAME @ SPOTLE.IO

import random,requests,json,logging,os,urllib3,webbrowser,sys
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
from selenium.common.exceptions import TimeoutException

def is_compiled():
    # check if running in compiled mode (pyinstaller)
    is_compiled = getattr(sys, 'frozen', False)
    if not is_compiled:
        print('Running in development mode')
    else:
        print('Running in compiled mode')
    return is_compiled

client_id = '7039fa9e3ff9490fae786fd557679ad5'
client_secret = '60c22025159943a3818f404fdce76da4'
OUTPUT_FOLDER = 'output'
DEFAULT_LINK = 'https://spotle.io'
DEFAULT_MESSAGE = "Created by Dave's script with <3"
DEFAULT_SAMPLE_SIZE = 250
DEBUG_DIFFICULTY = False
DEBUG_ARTIST_NAME = False
DEBUG_BROWSER = False
DEBUG_SHOW_ARTISTS = False
DEBUG_IS_COMPILED = is_compiled()


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
    if DEBUG_IS_COMPILED is False:
        save_to_json(top_2500_artists, 'top_2500_artists.json')
    return top_2500_artists_namesonly

def get_chrome_driver(options=None):
    if not options:
        options = Options()
        options.headless = True
        if not DEBUG_BROWSER:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    driver = webdriver.Chrome(options=options)
    return driver

def setup_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if DEBUG_IS_COMPILED is False:
        logging.basicConfig(filename='script.log',
                            level=logging.DEBUG,
                            format=log_format)
    else:
        logging.basicConfig(level=logging.INFO, format=log_format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger('').addHandler(console_handler)
    # selenium logs to info
    selenium_logger.setLevel(logging.INFO)
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.INFO)

def initialize_game(driver=None, link=DEFAULT_LINK) -> webdriver.Chrome:
    if not driver:
        driver = get_chrome_driver()
    driver.get(link)
    
    button_class = "challenge-btn"
    condition = EC.element_to_be_clickable((By.CLASS_NAME, button_class))
    WebDriverWait(driver, 10).until(condition).click()
    
    return driver

def attempt_create_game(driver=None, artist_name=None, message=DEFAULT_MESSAGE) -> tuple:
    # Ensure the search input is visible and clear any existing text
    input_name = "search"
    condition = EC.visibility_of_element_located((By.NAME, input_name))
    WebDriverWait(driver, 10).until(condition)
    input_field = driver.find_element(By.NAME, input_name)
    input_field.clear()
    input_field.send_keys(artist_name + Keys.ENTER)

    # Wait briefly for the share button to become clickable, indicating successful artist input
    share_button_class = "challenge-share-btn"
    try:
        WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.CLASS_NAME, share_button_class)))
        challenge_form_class = "challenge-form"
        condition = EC.visibility_of_element_located((By.CLASS_NAME, challenge_form_class))
        WebDriverWait(driver, 10).until(condition)
        input_field = driver.find_element(By.CLASS_NAME, challenge_form_class)
        input_field.send_keys(message + Keys.ENTER)
        share_button = driver.find_element(By.CLASS_NAME, share_button_class)
        share_button.click()
        
        # Spotle.io changed how they pass the user the game link
        return extract_url_from_clipboard()
    except TimeoutException:
        # Share button didn't become visible within the expected timeframe
        if DEBUG_SHOW_ARTISTS:
            raise ValueError(f"Share button not found for artist {artist_name}. Possible issue with artist eligibility or page loading.")
        else:
            raise ValueError(f"Share button not found. Possible issue with artist eligibility or page loading.")

# DEPRECATED
def extract_codes_from_logs(
    logs: list,
    source_file: str = "app.js",
    ) -> tuple:
    string = f'{DEFAULT_LINK}/{source_file}'
    artist_source_line = " 1262:10"
    message_source_line = " 1263:10"
    artist_code = None
    message_code = None
    for log in logs:
        if log['message'].startswith(string):
            restof_log = log['message'][len(string):]
            if restof_log.startswith(artist_source_line):
                artist_code = restof_log[len(artist_source_line):].strip().strip('"')
            elif restof_log.startswith(message_source_line):
                message_code = restof_log[len(message_source_line):].strip().strip('"')
    return artist_code, message_code

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

def extract_url_from_clipboard():
    from pyperclip import paste
    import re
    text = paste()
    # extract url from clipboard using regex
    regex = r'(https?://\S+)'
    match = re.search(regex, text)
    if match:
        return match.group(1)

def encode(string): # Unused for now
    bytes_to_encode = string.encode('utf-8')
    encoded = b64encode(bytes_to_encode).decode('utf-8')
    return encoded

def open_game_link(game_link):
    webbrowser.open_new_tab(game_link)

def main():
    top_2500_artists = get_top_2500_artists()
    if DEBUG_DIFFICULTY:
        difficulty = '5'
    else:
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
    initialized_driver = initialize_game(driver)
    while not success:
        try:
            random_artist = random.choice(top_artists)
            position = top_2500_artists.index(random_artist) + 1
            if DEBUG_SHOW_ARTISTS:
                logging.info(f'Random artist: {random_artist} - Position: {position}')
            else:
                logging.info(f'Random artist chosen')
            if DEBUG_ARTIST_NAME:
                random_artist = "TESTING ARTIST NAME"
            
            # NOW WE PLAY SPOTLE.IO
            game_link = attempt_create_game(
                driver=initialized_driver,
                artist_name=random_artist,
            )
            logging.info(f"Game link created. Opening game link in your browser...")
            open_game_link(game_link)
            logging.info(f"Game link opened. Terminating...")
            success = True
            initialized_driver.quit()
        except ValueError as e:
            logging.warning(f"{e}. Rerolling...")


if __name__ == '__main__':
    setup_logging()
    main()