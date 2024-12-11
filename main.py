# Install the necessary libraries
# pip install requests beautifulsoup4
#  pip install groq
# pip install googletrans==4.0.0-rc1

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from urllib.parse import urljoin
import os
from tkinter import Tk
from tkinter.filedialog import askdirectory
import os
from groq import Groq
from collections import defaultdict
import json
# from googletrans import Translator
from translate import Translator

os.environ["GROQ_API_KEY"] = "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"


def select_main_word(main_word, text):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = (
        f" In text surround the main_word by <span class=headword-example>."
        "Text: I think the vacation is okay."
        "Main word: vacation."
        "Result:  I think the <span class=headword-example> vacation </span> is okay."
        f"Text: {text}"
        f"Main word: {main_word}."
        "Result: "
        # "Don't display - Here is the revised sentence:"
        # "Display only the modified sentence."
        .strip()
    )

    try:
        # Make a request to the Groq API for chat completion
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Always return only modified sentence.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            model="llama3-70b-8192",
            response_format={"type": "text"},
            temperature=0,
        )

        # Extract the summarized tasks from the response
        summaries = chat_completion.choices[0].message.content
        return summaries

    except Exception as e:
        # Handle any exceptions that may occur during the API call
        print(f"An error occurred: {e}")
        return None


def translate_word(word):
    translator = Translator(to_lang="ru")
    translated_text = translator.translate(word)
    return translated_text


def fetch_webpage(url):
    """Fetch the webpage content with retries and timeout."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None


def parse_webpage(content, base_url):
    """Parse the webpage content and extract information."""
    soup = BeautifulSoup(content, 'html.parser')
    word = soup.find('span', class_='hw dhw').text if soup.find('span', class_='hw dhw') else 'N/A'
    pronunciation = soup.find('span', class_='pron dpron').text.strip() if soup.find('span',
                                                                                     class_='pron dpron') else 'N/A'
    pronunciation = pronunciation.replace('/', '')
    audio_tag = soup.find('audio', class_='hdn')
    sound_files = [urljoin(base_url, source['src']) for source in audio_tag.find_all('source')] if audio_tag else []
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
                definition_text = block.find('div', class_='def ddef_d db').text.strip() if block.find('div',
                                                                                                       class_='def ddef_d db') else ''
                if definition_text.endswith(":"):
                    definition_text = definition_text[:-1]

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
    parts_of_speech = list({entry['part_of_speech'] for entry in entries})
    counter = 1
    for entry in entries:
        part_of_speech = entry['part_of_speech']
        subheading = f" ({entry['subheading']})" if entry['subheading'] else ''
        if len(parts_of_speech) > 1:
            definitions.append(
                f"{counter}. <span class=\"def-com\">{part_of_speech}{subheading}</span> {entry['definition']}")
        else:
            definitions.append(f"{counter}. {entry['definition']}")

        if entry['examples']:
            for example in entry['examples']:
                example = select_main_word(word, example)
                examples.append(f"{counter}. {example}")
        counter += 1
    definitions_text = "<br>".join(definitions)
    examples_text = "<br>".join(examples)
    # examples_text = select_main_word(word, examples_text)
    parts_of_speech_text = ", ".join(filter(None, parts_of_speech))
    # translation = " "
    translation = translate_word(word)
    image = " "
    sound_link = results['sound_files'][0] if results['sound_files'] else ''
    sound_link = f"[sound:{sound_link}]"
    id_text = f"MY_ENG_{start_id:04d}"
    anki_note = f"{id_text}\t{word}\t{pronunciation}\t{parts_of_speech_text}\t{definitions_text}\t{examples_text}\t{translation}\t{image}\t{sound_link}"
    return anki_note


def main():
    """Main function to run the script."""
    base_url = "https://dictionary.cambridge.org"
    words = input("Enter words separated by commas: ").split(',')
    start_id = int(input("Enter the starting ID number: "))

    # Use tkinter to open a directory chooser dialog
    root = Tk()
    root.withdraw()  # Hide the root window
    save_directory = askdirectory(title="Select Directory to Save File")

    if not save_directory:
        print("No directory selected. Exiting.")
        return

    if not os.path.exists(save_directory):
        print(f"Directory {save_directory} does not exist. Creating it.")
        os.makedirs(save_directory)

    not_found_words = []
    anki_notes = []
    for word in words:
        word = word.strip()
        url = f"https://dictionary.cambridge.org/dictionary/learner-english/{word}"
        webpage_content = fetch_webpage(url)
        if webpage_content:
            results = parse_webpage(webpage_content, base_url)
            if results['word'] == 'N/A':
                url = f"https://dictionary.cambridge.org/dictionary/english/{word}"
                webpage_content = fetch_webpage(url)
                if webpage_content:
                    results = parse_webpage(webpage_content, base_url)
            if results['word'] != 'N/A':
                anki_note = format_anki(results, start_id)
                anki_notes.append(anki_note)
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
    if anki_notes:
        save_path = os.path.join(save_directory, 'anki_notes.txt')
        with open(save_path, 'w', encoding='utf-8') as file:
            file.write("#separator:tab\n")
            file.write("#html:true\n")
            file.write("#tags column:11\n")
            for note in anki_notes:
                file.write(" " + note + "\n")
        print(f"File saved at: {os.path.abspath(save_path)}")


if __name__ == "__main__":
    main()
