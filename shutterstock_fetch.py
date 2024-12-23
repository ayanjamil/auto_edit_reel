import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def fetch_images_from_shutterstock(client_id, client_secret, keywords, per_page=5):
    """
    Fetch images from Shutterstock API based on keywords.

    Args:
        client_id (str): Shutterstock Client ID.
        client_secret (str): Shutterstock Client Secret.
        keywords (list): List of keywords to search for.
        per_page (int): Number of images to fetch per keyword.

    Returns:
        list: List of image URLs and metadata.
    """
    auth_url = "https://api.shutterstock.com/v2/oauth/access_token"
    search_url = "https://api.shutterstock.com/v2/images/search"

    # Get access token
    auth_response = requests.post(auth_url, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    })

    if auth_response.status_code != 200:
        print(f"Error authenticating Shutterstock: {auth_response.status_code}")
        return []

    access_token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    images = []

    for keyword in keywords:
        params = {"query": keyword, "per_page": per_page}
        response = requests.get(search_url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            for result in data["data"]:
                images.append({
                    "url": result["assets"]["preview"]["url"],
                    "alt": result.get("description", ""),
                    "photographer": result["contributor"].get("name", "Unknown")
                })
        else:
            print(f"Error fetching from Shutterstock for keyword '{keyword}': {response.status_code}")
    return images

if __name__ == "__main__":
    # Load API credentials
    client_id = os.getenv("SHUTTERSTOCK_CLIENT_ID")
    client_secret = os.getenv("SHUTTERSTOCK_CLIENT_SECRET")

    # Define test keywords
    test_keywords = ["nature", "technology", "travel"]

    # Fetch images
    results = fetch_images_from_shutterstock(client_id, client_secret, test_keywords)

    # Print the results
    for image in results:
        print(f"URL: {image['url']}, Alt: {image['alt']}, Photographer: {image['photographer']}")
