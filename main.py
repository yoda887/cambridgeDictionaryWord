# Install the necessary libraries
# pip install requests beautifulsoup4

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from urllib.parse import urljoin

def fetch_webpage(url):
    """Fetch the webpage content with retries and timeout."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # Set up a session with retries
        session = requests.Session()
        retry = Retry(
            total=5,  # Increase total retries
            backoff_factor=1,  # Increase backoff factor
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        # Make the request with a timeout and custom headers
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None

def parse_webpage(content, base_url):
    """Parse the webpage content and extract information."""
    soup = BeautifulSoup(content, 'html.parser')

    # Extract the word
    word = soup.find('span', class_='hw dhw').text if soup.find('span', class_='hw dhw') else 'N/A'

    # Extract the part of speech
    part_of_speech = soup.find('span', class_='pos dpos').text if soup.find('span', class_='pos dpos') else 'N/A'

    # Extract the pronunciation
    pronunciation = soup.find('span', class_='pron dpron').text.strip() if soup.find('span', class_='pron dpron') else 'N/A'

    # Extract the pronunciation sound file links
    audio_tag = soup.find('audio', class_='hdn')
    if audio_tag:
        sources = audio_tag.find_all('source')
        sound_files = [urljoin(base_url, source['src']) for source in sources]
    else:
        sound_files = []

    # Extract definitions and their examples
    definitions = []
    definition_blocks = soup.find_all('div', class_='def-block ddef_block')
    for block in definition_blocks:
        definition_text = block.find('div', class_='def ddef_d db').text.strip() if block.find('div', class_='def ddef_d db') else 'N/A'
        example_texts = [ex.text.strip() for ex in block.find_all('div', class_='examp dexamp')]
        definitions.append({
            'definition': definition_text,
            'examples': example_texts
        })

    return {
        'word': word,
        'part_of_speech': part_of_speech,
        'pronunciation': pronunciation,
        'sound_files': sound_files,
        'definitions': definitions
    }

def display_results(results):
    """Display the extracted results."""
    print(f"Word: {results['word']}")
    print(f"Part of Speech: {results['part_of_speech']}")
    print(f"Pronunciation: {results['pronunciation']}")
    print("Pronunciation Sound Files:")
    for sound_file in results['sound_files']:
        print(f"- {sound_file}")
    print("Definitions and Examples:")
    for idx, definition in enumerate(results['definitions'], start=1):
        print(f"Definition {idx}: {definition['definition']}")
        print("Examples:")
        for example in definition['examples']:
            print(f"- {example}")

def main():
    """Main function to run the script."""
    url = "https://dictionary.cambridge.org/dictionary/english/abide"
    base_url = "https://dictionary.cambridge.org"
    webpage_content = fetch_webpage(url)
    if webpage_content:
        results = parse_webpage(webpage_content, base_url)
        display_results(results)

if __name__ == "__main__":
    main()
