import os
import requests
from dotenv import load_dotenv

# .env dosyasındaki TMDB anahtarını okur
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def search_content(query, content_type="movie"):
    url = f"{BASE_URL}/search/{content_type}"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": "en-US"
    }
    response = requests.get(url, params=params).json()
    
    if response.get("results"):
        return response["results"][0]
    return None

def get_streaming_platforms(content_id, region="US", content_type="movie"):
    url = f"{BASE_URL}/{content_type}/{content_id}/watch/providers"
    params = {"api_key": TMDB_API_KEY}
    response = requests.get(url, params=params).json()
    
    results = response.get("results", {})
    if region in results:
        providers = results[region].get("flatrate", [])
        return [provider["provider_name"] for provider in providers]
    return []