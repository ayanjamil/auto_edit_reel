import os
import requests

from dotenv import load_dotenv
# Your Pexels API Key



def fetch_images_and_videos(key,keywords, per_page=5):
    """
    Fetch images and videos from Pexels API for the given keywords.
    """
    base_url = "https://api.pexels.com/v1"
    headers = {"Authorization": key}

    if not key:
        print("Error: Pexels API key not found in environment variables.")
        return

    results = {"images": [], "videos": []}

    for keyword in keywords:
        try:
            # Search for photos
            photo_response = requests.get(
                f"{base_url}/search",
                headers=headers,
                params={"query": keyword, "per_page": per_page}
            )
            photo_response.raise_for_status()
            photos = photo_response.json().get("photos", [])
            results["images"].extend(photos)

            # Search for videos
            video_response = requests.get(
                f"{base_url}/videos/search",
                headers=headers,
                params={"query": keyword, "per_page": per_page}
            )
            video_response.raise_for_status()
            videos = video_response.json().get("videos", [])
            results["videos"].extend(videos)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching results for keyword '{keyword}': {e}")

    return results


def save_results_to_file(results, output_file="pexels_results.json"):
    """
    Save the fetched results to a JSON file for later use.
    """
    import json
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"Results saved to {output_file}")


# Example usage
if __name__ == "__main__":
    OUTPUT_PATH = "/home/ayan/fn/script/vid_automation/output/stocks/pexels_results.json"
    load_dotenv()
    PEXELS_API_KEY = os.getenv("PIXELS_API_KEYS")
    # Example keywords
    keywords = ["artificial intelligence", "technology", "healthcare"]

    # Fetch results from Pexels API
    pexels_results = fetch_images_and_videos(PEXELS_API_KEY,keywords, per_page=3)
    print(f"Fetched {len(pexels_results['images'])} images and {len(pexels_results['videos'])} videos.")

    # Save results to a file
    save_results_to_file(pexels_results,OUTPUT_PATH)
