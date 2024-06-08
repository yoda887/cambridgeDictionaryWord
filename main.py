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

    # Extract the pronunciation
    pronunciation = soup.find('span', class_='pron dpron').text.strip() if soup.find('span', class_='pron dpron') else 'N/A'
    pronunciation = pronunciation.replace('/', '')  # Remove "/"

    # Extract the pronunciation sound file links
    audio_tag = soup.find('audio', class_='hdn')
    if audio_tag:
        sources = audio_tag.find_all('source')
        sound_files = [urljoin(base_url, source['src']) for source in sources]
    else:
        sound_files = []

    # Extract parts of speech, definitions, examples, and subheadings
    entries = soup.find_all('div', class_='pr entry-body__el')

    results = []
    for entry in entries:
        part_of_speech = entry.find('span', class_='pos dpos').text if entry.find('span', class_='pos dpos') else ''

        sense_blocks = entry.find_all('div', class_='sense-body dsense_b')

        for sense in sense_blocks:
            subheading = sense.find('span', class_='dsense-title dsense-title--collocation').text.strip() if sense.find(
                'span', class_='dsense-title dsense-title--collocation') else ''
            definition_blocks = sense.find_all('div', class_='def-block ddef_block')

            for block in definition_blocks:

                # definition_text = block.find('div', class_='def ddef_d db').text.strip() if block.find('div',
                #                                                                                        class_='def ddef_d db') else ''
                definition_text = block.find('div', class_='def ddef_d db').text.strip()[:-1] if block.find('div',
                                                                                                            class_='def ddef_d db') else ''
                example_texts = [ex.text.strip() for ex in block.find_all('div', class_='examp dexamp')]
                results.append({
                    'part_of_speech': part_of_speech,
                    'subheading': subheading,
                    'definition': definition_text,
                    'examples': example_texts
                })

    return {
        'word': word,
        'pronunciation': pronunciation,
        'sound_files': sound_files,
        'entries': results
    }

def format_anki(results, start_id):
    """Format the extracted results into Anki note format."""
    word = results['word']
    pronunciation = results['pronunciation']
    entries = results['entries']

    definitions = []
    examples = []
    parts_of_speech = []
    counter = 1

    for entry in entries:
        part_of_speech = entry['part_of_speech']
        if not parts_of_speech or parts_of_speech[-1] != part_of_speech:
            parts_of_speech.append(part_of_speech)

        subheading = f" ({entry['subheading']})" if entry['subheading'] else ''
        definitions.append(f"{counter}. {part_of_speech}{subheading}: {entry['definition']}")
        if entry['examples']:  # Check if there are examples
            for example in entry['examples']:
                examples.append(f"{counter}. {example}")
        counter += 1

    definitions_text = "<br>".join(definitions)
    examples_text = "<br>".join(examples)
    parts_of_speech_text = ", ".join(filter(None, parts_of_speech))  # Skip empty parts of speech

    # Placeholder values for translation, image, and sound link
    translation = " "
    image = " "

    sound_link = results['sound_files'][0] if results['sound_files'] else ''
    sound_link = f"[sound:{sound_link}]"

    # Generate the ID
    id_text = f"MY_ENG_{start_id:04d}"

    anki_note = f" {id_text}\t{word}\t{pronunciation}\t{parts_of_speech_text}\t{definitions_text}\t{examples_text}\t{translation}\t{image}\t{sound_link}"
    return anki_note

def main():
    """Main function to run the script."""
    base_url = "https://dictionary.cambridge.org"
    words = input("Enter words separated by commas: ").split(',')
    start_id = int(input("Enter the starting ID number: "))

    not_found_words = []

    for word in words:
        word = word.strip()
        url = f"https://dictionary.cambridge.org/dictionary/learner-english/{word}"
        webpage_content = fetch_webpage(url)
        if webpage_content:
            results = parse_webpage(webpage_content, base_url)
            if results['word'] != 'N/A':
                anki_note = format_anki(results, start_id)
                print(anki_note)
                start_id += 1
            else:
                not_found_words.append(word)
        else:
            not_found_words.append(word)

    if not_found_words:
        print("The following words were not found:")
        for word in not_found_words:
            print(word)

if __name__ == "__main__":
    main()
