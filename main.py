import os

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from openai import OpenAI
from dotenv import load_dotenv
from pixels import fetch_images_and_videos, save_results_to_file

# Download required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')  # Added this line to fix the punkt_tab error

# Set your OpenAI API key
# openai.api_key = "your_openai_api_key"

def initialize_openai(api_key):
    return OpenAI(api_key=api_key)


def extract_keywords(script_file):
    """
    Extract keywords from the given script file by filtering out stopwords.
    """
    with open(script_file, 'r') as f:
        script = f.read()

    # Tokenize and filter stopwords
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(script)
    keywords = [word.lower() for word in words if word.isalnum() and word.lower() not in stop_words]

    return keywords


def get_best_keywords_via_chatgpt(openai_client,keywords, max_keywords=15):

    try :

        """
        Use ChatGPT API to refine and select the top keywords for stock clips.
        """
        keyword_prompt = ", ".join(keywords)
        prompt = (f"The following are keywords extracted from a video script: {keyword_prompt}. "
                  f"Select the top {max_keywords} most relevant keywords for finding stock images or videos. "
                  "Provide them in a comma-separated list.")

        # Call the ChatGPT API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant for refining keyword selection."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.7
        )
        refined_keywords = response.choices[0].message.content
        return [word.strip() for word in refined_keywords.split(",")]


    except Exception as e:
        print(f"Error summarizing row: {e}")


# Example usage
load_dotenv()
script_file = "script.txt"  # Replace with your script file path
extracted_keywords = extract_keywords(script_file)
print("Extracted Keywords:", extracted_keywords)
OUTPUT_PATH = "/home/ayan/fn/script/vid_automation/output/stocks/pexels_results.json"
# Refine the extracted keywords using ChatGPT
PEXELS_API_KEY = os.getenv("PIXELS_API_KEYS")
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = initialize_openai(openai_api_key)
best_keywords = get_best_keywords_via_chatgpt(openai_client,extracted_keywords, max_keywords=15)
print("Top Keywords for Stock Clips:", best_keywords)
pexels_results = fetch_images_and_videos(PEXELS_API_KEY,best_keywords, per_page=1)
print(f"Fetched {len(pexels_results['images'])} images and {len(pexels_results['videos'])} videos.")
save_results_to_file(pexels_results,OUTPUT_PATH)


