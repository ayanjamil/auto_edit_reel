import os
import json
import openai
import requests
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

def download_file(url, output_path):
    """
    Download a file from a URL and save it locally.
    """
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return output_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None


def load_transcription(file_path):
    """
    Load transcription from a .txt file.
    """
    segments = []
    try:
        with open(file_path, "r") as file:
            for line in file:
                parts = line.strip().split(" ", 2)
                if len(parts) == 3:
                    start, end, text = parts
                    segments.append({
                        "start": float(start),
                        "end": float(end),
                        "text": text
                    })
        return segments
    except Exception as e:
        print(f"Error loading transcription: {e}")
        return []


def load_media_data(json_path):
    """
    Load media data from final_results.json.
    """
    try:
        with open(json_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading media data: {e}")
        return {"best_images": [], "best_videos": []}


def get_media_description(media_item, media_type="images"):
    """
    Extract a meaningful description from Pexels media item.
    """
    if not media_item or not isinstance(media_item, dict):
        return None

    media = media_item.get('media', {})
    if media_type == "images":
        return media.get('alt') or f"Image by {media.get('photographer', 'Unknown')}"
    else:  # videos
        user_name = media.get('user', {}).get('name', 'Unknown creator')
        duration = media.get('duration', 'unknown duration')
        return f"Video by {user_name}, {duration} seconds long"


def filter_best_media(openai_client, script, media_items, max_items=5, media_type="images"):
    """
    Filters the best media items using GPT based on the script context.
    """
    results = []
    if not media_items:
        print(f"No {media_type} provided")
        return []

    for media_item in media_items:
        description = get_media_description(media_item, media_type)
        if not description:
            continue

        prompt = (
            f"Script content: {script}\n\n"
            f"Media description: {description}\n\n"
            "Rate relevance of this media to the script (Score: 1-10) and explain briefly."
        )

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a media selection assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.5
            )

            reasoning = response.choices[0].message.content
            match = re.search(r'Score:\s*(\d+)', reasoning)

            if match:
                score = int(match.group(1))
                if score > 0:
                    results.append({"media": media_item['media'], "score": score, "description": description})
        except Exception as e:
            print(f"Error processing {media_type}: {str(e)}")

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:max_items]


def map_media_to_segments(openai_client, segments, media_data):
    """
    Map the most relevant media to each segment using GPT for semantic analysis.
    """
    script_content = " ".join([segment["text"] for segment in segments])
    best_images = filter_best_media(openai_client, script_content, media_data.get("best_images", []), media_type="images")
    best_videos = filter_best_media(openai_client, script_content, media_data.get("best_videos", []), media_type="videos")

    mapped_segments = []
    for i, segment in enumerate(segments):
        image_url = best_images[i % len(best_images)]["media"].get("src", {}).get("original") if best_images else None
        video_url = best_videos[i % len(best_videos)]["media"].get("video_files", [{}])[0].get("link") if best_videos else None

        mapped_segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"],
            "image": image_url,
            "video": video_url
        })
    return mapped_segments


def edit_video(video_path, segments, output_path, temp_dir):
    """
    Edit the video using mapped media segments.
    """
    try:
        os.makedirs(temp_dir, exist_ok=True)
        video = VideoFileClip(video_path)
        clips = []

        for i, segment in enumerate(segments):
            start, end = segment["start"], segment["end"]
            subclip = video.subclip(start, end)

            if segment.get("image"):
                image_path = download_file(segment["image"], os.path.join(temp_dir, f"image_{i}.png"))
                if image_path:
                    image_clip = ImageClip(image_path).set_duration(end - start).set_position("center")
                    subclip = CompositeVideoClip([subclip, image_clip])

            elif segment.get("video"):
                video_path = download_file(segment["video"], os.path.join(temp_dir, f"video_{i}.mp4"))
                if video_path:
                    overlay_video = VideoFileClip(video_path).subclip(0, end - start).resize(height=subclip.h * 0.8)
                    subclip = CompositeVideoClip([subclip, overlay_video])

            clips.append(subclip)

        final_video = concatenate_videoclips(clips)
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

    except Exception as e:
        print(f"Error in video editing: {e}")


def main():
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("Missing OPENAI_API_KEY")

        openai_client = openai.Client(api_key=openai_api_key)
        transcription_path = "/home/ayan/fn/script/vid_automation/input/script/timestamps.txt"
        media_json_path = "/home/ayan/fn/script/vid_automation/output/stocks/final_results.json"
        video_path = "/home/ayan/fn/script/vid_automation/input/raw_video/iu.mp4"
        output_video_path = "/home/ayan/fn/script/vid_automation/output/video/draft.mp4"
        temp_dir = "/home/ayan/fn/script/vid_automation/temp_dir"

        segments = load_transcription(transcription_path)
        media_data = load_media_data(media_json_path)

        mapped_segments = map_media_to_segments(openai_client, segments, media_data)
        edit_video(video_path, mapped_segments, output_video_path, temp_dir)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
