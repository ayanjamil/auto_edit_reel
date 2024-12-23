import os
import json
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import openai  # Ensure you have the openai package installed
from dotenv import load_dotenv
from pixels import fetch_images_and_videos, save_results_to_file
from transcriber import save_transcription_to_file
import whisper





# Load environment variables
load_dotenv()

# Initialize OpenAI client
def initialize_openai(api_key):
    openai.api_key = api_key



def transcribe_with_timestamps_clean(video_path, output_file):
    """
    Transcribe a video and save timestamps and text to a .txt file without extra labels.

    Args:
        video_path (str): Path to the input video file.
        output_file (str): Path to the output .txt file.

    Returns:
        list: List of transcription segments with start, end, and text.
    """
    # Load the Whisper model
    model = whisper.load_model("base")

    # Transcribe the video
    result = model.transcribe(video_path, verbose=True)

    # Extract segments and save to file
    transcription_segments = []
    with open(output_file, "w") as f:
        for segment in result["segments"]:
            start = f"{segment['start']:.2f}"  # Start time in seconds
            end = f"{segment['end']:.2f}"  # End time in seconds
            text = segment["text"]

            # Write to the .txt file in the desired format
            f.write(f"{start} {end} {text}\n")

            # Add the segment to the list
            transcription_segments.append({
                "start": start,
                "end": end,
                "text": text
            })

    print(f"Cleaned transcript with timestamps saved to {output_file}")
    return transcription_segments



# Function to refine keywords using GPT
def get_best_keywords_via_chatgpt(openai_client, scripts, max_keywords=15):
    try:
        prompt = (
            f"The following is the script of a video: {scripts}. "
            f"Select the top {max_keywords} most relevant keywords from the script provided for finding stock images or videos. "
            "Provide them in a comma-separated list."
        )

        # Call the ChatGPT API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant for refining keyword selection for finding out stock images for short form content."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.7
        )
        refined_keywords = response.choices[0].message.content
        return [word.strip() for word in refined_keywords.split(",")]
    except Exception as e:
        print(f"Error refining keywords: {e}")
        return []
    
def get_most_relevant_image_with_script(openai_client, segment_text, script, images):
    """
    Uses GPT to determine the most relevant image for a transcription segment
    by considering the segment text, the script, and image descriptions.

    Args:
        openai_client: The OpenAI client instance.
        segment_text (str): The text of the transcription segment.
        script (str): The entire script of the video.
        images (list): List of available image data from Pexels.

    Returns:
        dict: The selected image data.
    """
    if not images:
        return None  # No images available

    try:
        image_descriptions = "\n".join(
            [f"Image {i+1}: {img.get('alt', 'No description')}" for i, img in enumerate(images)]
        )
        prompt = (
            f"The following is the script of the video:\n\n{script}\n\n"
            f"Here is the transcription segment: \"{segment_text}\".\n"
            f"Select the most contextually relevant image for this segment "
            f"from the following options:\n\n{image_descriptions}\n\n"
            "Reply with the number of the most relevant image."
        )

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant for selecting the most contextually relevant image."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=50,
            temperature=0.5
        )

        response_text = response.choices[0].message.content.strip()

        # Validate the response and convert to integer
        if response_text.isdigit():
            selected_image_index = int(response_text) - 1
            if 0 <= selected_image_index < len(images):
                return images[selected_image_index]
            else:
                print(f"No relevant image selected for segment: \"{segment_text}\".")
                return None
        else:
            print(f"Invalid GPT response for segment: \"{segment_text}\": {response_text}")
            return None

    except Exception as e:
        print(f"Error selecting image via GPT: {e}")
        return None


def map_transcription_to_images_with_script(openai_client, transcription_segments, script, pexels_results):
    """
    Maps transcription segments to stock images using GPT with script context for better selection.

    Args:
        openai_client: The OpenAI client instance.
        transcription_segments (list): List of transcription segments with start, end, and text.
        script (str): The entire script of the video.
        pexels_results (dict): Pexels results containing fetched images.

    Returns:
        list: List of dictionaries with transcription segments and mapped image URLs.
    """
    mapped_results = []

    images = pexels_results.get("images", [])

    for segment in transcription_segments:
        segment_text = segment["text"]

        # Use GPT to find the most relevant image
        image_data = get_most_relevant_image_with_script(openai_client, segment_text, script, images)

        if image_data:
            # Remove the selected image from the list to avoid reusing it
            images.remove(image_data)

        mapped_results.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment_text,
            "image_url": image_data["src"]["medium"] if image_data else None,
            "alt": image_data.get("alt", None) if image_data else None
        })

    return mapped_results


def main():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    PEXELS_API_KEY = os.getenv("PIXELS_API_KEYS")
    OUTPUT_PATH_STOCKS = "/home/ayan/fn/script/vid_automation/output/stocks/stocks_results.json"
    
    video_path = "/home/ayan/fn/script/vid_automation/input/raw_video/iu.mp4"  # Replace with the path to your video file
    output_timestamp_file = "/home/ayan/fn/script/vid_automation/input/script/timestamps.txt"  # Replace with the desired output .txt file path

        # Get the transcription segments
    transcription_segments = transcribe_with_timestamps_clean(video_path, output_timestamp_file)

    if transcription_segments is None or not transcription_segments:
        print("Error: Transcription segments are empty or None.")
        return
    
    # Save them to a file
    save_transcription_to_file(transcription_segments, output_timestamp_file)
    

    if not openai_api_key:
        print("OpenAI API key not found in environment variables.")
        return

    initialize_openai(openai_api_key)

    # Load script content
    script_file = "script.txt"  # Replace with your script file path
    try:
        with open(script_file, "r") as f:
            script_content = f.read()
    except FileNotFoundError:
        print(f"Script file not found: {script_file}")
        return

    # Get best keywords
    keywords = get_best_keywords_via_chatgpt(openai, script_content)

    print("Refined Keywords:", keywords)
    pexels_results = fetch_images_and_videos(PEXELS_API_KEY,keywords, per_page=3)
    print(f"Fetched {len(pexels_results['images'])} images ")
    save_results_to_file(pexels_results,OUTPUT_PATH_STOCKS)

      # Map transcription segments to images using GPT with script context
    mapped_results = map_transcription_to_images_with_script(openai, transcription_segments, script_content, pexels_results)

    # Save mapped results
    mapped_results_file = "/home/ayan/fn/script/vid_automation/output/mapped_results.json"
    with open(mapped_results_file, "w") as f:
        json.dump(mapped_results, f, indent=4)
    print(f"Mapped results saved to {mapped_results_file}")


if __name__ == "__main__":
    main()