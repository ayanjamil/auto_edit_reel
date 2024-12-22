import os
import json
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from openai import OpenAI
from dotenv import load_dotenv
import nltk
import re


# Download required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# Load environment variables
load_dotenv()


# Initialize OpenAI client
def initialize_openai(api_key):
    return OpenAI(api_key=api_key)


# Function to extract keywords from the script
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


# Function to refine keywords using GPT
def get_best_keywords_via_chatgpt(openai_client, keywords, max_keywords=15):
    """
    Use ChatGPT API to refine and select the top keywords for stock clips.
    """
    try:
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
        print(f"Error refining keywords: {e}")


# Function to filter the best media


def filter_best_media(openai_client, script, media_items, max_items=5, media_type="images"):
    """
    Filters the best media items (images or videos) using GPT based on the script context.
    """
    results = []
    for media in media_items:
        prompt = (
            f"The following is the content of a video script: {script}. "
            f"Based on this script, evaluate the relevance of this {media_type[:-1]}: {media['alt'] if media_type == 'images' else media['url']}. "
            "Give a score between 1 to 10 (10 being most relevant), and explain your reasoning briefly."
        )
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": "You are an assistant for selecting relevant media for a given script."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.5
            )
            reasoning = response.choices[0].message.content

            # Extract score using regex to ensure it's a number
            match = re.search(r'\bScore:\s*(\d+)', reasoning)
            if match:
                score = int(match.group(1))
                results.append({"media": media, "score": score, "reasoning": reasoning})
            else:
                print(f"Could not extract a valid score for media {media['url']}. Response: {reasoning}")

        except Exception as e:
            print(f"Error with media {media['url']}: {e}")

    results = sorted(results, key=lambda x: x['score'], reverse=True)[:max_items]
    return results


# Main script execution
def main():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_client = initialize_openai(openai_api_key)

    # Load script content
    script_file = "/home/ayan/fn/script/vid_automation/input/script/timestamps.txt"  # Replace with the path to your script file
    with open(script_file, "r") as f:
        script_content = f.read()

    # Load Pexels JSON data
    json_file = "/home/ayan/fn/script/vid_automation/output/stocks/pexels_results.json"  # Replace with your JSON file path
    with open(json_file, "r") as f:
        pexels_data = json.load(f)

    # Extract keywords
    extracted_keywords = extract_keywords(script_file)
    print("Extracted Keywords:", extracted_keywords)

    # Refine keywords using GPT
    best_keywords = get_best_keywords_via_chatgpt(openai_client, extracted_keywords, max_keywords=15)
    print("Top Keywords for Stock Clips:", best_keywords)

    # Filter images and videos
    best_images = filter_best_media(openai_client, script_content, pexels_data["images"], media_type="images")
    best_videos = filter_best_media(openai_client, script_content, pexels_data["videos"], media_type="videos")

    # Save results to a final JSON file
    final_results = {
        "best_images": best_images,
        "best_videos": best_videos
    }
    output_file = "/home/ayan/fn/script/vid_automation/output/stocks/final_results.json"
    with open(output_file, "w") as f:
        json.dump(final_results, f, indent=4)
    print(f"Filtered results saved to {output_file}")


if __name__ == "__main__":
    main()
