import os
import json
from dotenv import load_dotenv
import whisper
from pixels import fetch_images_and_videos
from unsplash import fetch_images_from_unsplash
from shutterstock_fetch import fetch_images_from_shutterstock
from transcriber import save_transcription_to_file
from chatgpt_requests_handler import ChatGPTHandler

# Load environment variables
load_dotenv()

def transcribe_with_timestamps_clean(video_path, output_file):
    """
    Transcribe a video and save timestamps and text to a .txt file without extra labels.

    Args:
        video_path (str): Path to the input video file.
        output_file (str): Path to the output .txt file.

    Returns:
        list: List of transcription segments with start, end, and text.
    """
    model = whisper.load_model("base")
    result = model.transcribe(video_path, verbose=True)

    transcription_segments = []
    with open(output_file, "w") as f:
        for segment in result["segments"]:
            start = f"{segment['start']:.2f}"
            end = f"{segment['end']:.2f}"
            text = segment["text"]
            f.write(f"{start} {end} {text}\n")
            transcription_segments.append({"start": start, "end": end, "text": text})

    print(f"Cleaned transcript with timestamps saved to {output_file}")
    return transcription_segments

def validate_api_keys(api_keys):
    """
    Validates API keys and prints which ones are missing.

    Args:
        api_keys (dict): Dictionary of API keys with their names as keys and values as the actual keys.

    Returns:
        bool: True if all API keys are present, False otherwise.
    """
    missing_keys = [key_name for key_name, key_value in api_keys.items() if not key_value]
    if missing_keys:
        print("Error: The following API keys are missing:")
        for key in missing_keys:
            print(f"  - {key}")
        return False
    return True

def combine_image_results(pexels_results, unsplash_results, shutterstock_results):
    """
    Combines image results from Pexels, Unsplash, and Shutterstock.

    Returns:
        list: Unified list of image data from all sources.
    """
    combined_results = []
    if "images" in pexels_results:
        combined_results.extend([
            {
                "url": img["src"]["medium"],
                "alt": img.get("alt", "No description"),
                "photographer": img["photographer"],
                "photographer_url": img["photographer_url"]
            } for img in pexels_results["images"]
        ])
    combined_results.extend([
        {
            "url": img.get("url"),
            "alt": img.get("description", "No description"),
            "photographer": img.get("photographer", "Unknown"),
            "photographer_url": img.get("photographer_url", "")
        } for img in unsplash_results
    ])
    combined_results.extend([
        {
            "url": img.get("url"),
            "alt": img.get("alt", "No description"),
            "photographer": img.get("photographer", "Unknown")
        } for img in shutterstock_results
    ])
    return combined_results

def main():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    PEXELS_API_KEY = os.getenv("PIXELS_API_KEYS")
    UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")
    CLIENT_ID_SHUTTERSTOCK = os.getenv("SHUTTERSTOCK_CLIENT_ID")
    CLIENT_SECRET_SHUTTERSTOCK = os.getenv("SHUTTERSTOCK_CLIENT_SECRET")

    api_keys = {
        "OpenAI API Key": openai_api_key,
        "Pexels API Key": PEXELS_API_KEY,
        "Unsplash API Key": UNSPLASH_API_KEY,
        "Shutterstock Client ID": CLIENT_ID_SHUTTERSTOCK,
        "Shutterstock Client Secret": CLIENT_SECRET_SHUTTERSTOCK
    }

    if not validate_api_keys(api_keys):
        return

    video_path = "/home/ayan/fn/script/vid_automation/input/raw_video/iu.mp4"
    output_timestamp_file = "/home/ayan/fn/script/vid_automation/input/script/timestamps.txt"

    transcription_segments = transcribe_with_timestamps_clean(video_path, output_timestamp_file)
    if not transcription_segments:
        print("Error: Transcription segments are empty or None.")
        return

    chatgpt_handler = ChatGPTHandler(openai_api_key)

    script_file = "script.txt"
    try:
        with open(script_file, "r") as f:
            script_content = f.read()
    except FileNotFoundError:
        print(f"Script file not found: {script_file}")
        return

    # Fixed: Removed the extra chatgpt_handler argument
    keywords = chatgpt_handler.generate_keywords(script_content)
    print("Refined Keywords:", keywords)

    pexels_results = fetch_images_and_videos(PEXELS_API_KEY, keywords, per_page=5)
    unsplash_results = fetch_images_from_unsplash(UNSPLASH_API_KEY, keywords, per_page=5)
    shutterstock_results = fetch_images_from_shutterstock(CLIENT_ID_SHUTTERSTOCK, CLIENT_SECRET_SHUTTERSTOCK, keywords, per_page=5)

    combined_images = combine_image_results(pexels_results, unsplash_results, shutterstock_results)
    print(f"Fetched {len(combined_images)} images from all sources.")

    # Fixed: Removed the extra chatgpt_handler argument
    mapped_results = chatgpt_handler.map_transcription_to_images_with_script(
        transcription_segments, 
        script_content, 
        combined_images
    )

    mapped_results_file = "/home/ayan/fn/script/vid_automation/output/mapped_results.json"
    with open(mapped_results_file, "w") as f:
        json.dump(mapped_results, f, indent=4)
    print(f"Mapped results saved to {mapped_results_file}")

if __name__ == "__main__":
    main()