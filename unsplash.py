import os
import requests
from dotenv import load_dotenv

def fetch_images_from_unsplash(api_key, keywords, per_page=5):
    """
    Fetch images from Unsplash API based on keywords.

    Args:
        api_key (str): Unsplash API Access Key.
        keywords (list): List of keywords to search for.
        per_page (int): Number of images to fetch per keyword.

    Returns:
        list: List of image URLs and metadata.
    """
    base_url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {api_key}"}
    images = []

    for keyword in keywords:
        params = {"query": keyword, "per_page": per_page}
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            for result in data.get("results", []):
                images.append({
                    "url": result["urls"].get("regular", ""),
                    "alt": result.get("alt_description", "No description"),
                    "photographer": result["user"].get("name", "Unknown"),
                    "photographer_url": result["user"]["links"].get("html", "")
                })
        else:
            print(f"Error fetching from Unsplash for keyword '{keyword}': {response.status_code}")
    return images

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Retrieve API key from environment
    api_key = os.getenv("UNSPLASH_API_KEY")
    if not api_key:
        print("Error: Unsplash API key not found. Ensure UNSPLASH_API_KEY is set in your .env file.")
        exit(1)

    # Sample keywords to test
    sample_keywords = ["nature", "technology", "architecture"]

    # Fetch images
    images = fetch_images_from_unsplash(api_key, sample_keywords)

    # Print the results
    for image in images:
        print(f"URL: {image['url']}")
        print(f"Description: {image['alt']}")
        print(f"Photographer: {image['photographer']}")
        print(f"Photographer URL: {image['photographer_url']}")
        print("---")
