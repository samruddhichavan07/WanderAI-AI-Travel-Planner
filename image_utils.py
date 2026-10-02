import requests
import streamlit as st

WIKI_API = "https://en.wikipedia.org/w/api.php"

FALLBACK_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/8/8c/Blue_globe_icon.svg"


@st.cache_data(show_spinner=False)
def get_destination_image(place_name: str) -> str:
    """Fetch a real photo of a place from Wikipedia. Returns a fallback if not found."""
    try: 
        params = {
            "action": "query",
            "format": "json",
            "prop": "pageimages",
            "piprop": "original",
            "titles": place_name,
            "redirects": 1,
        }
        headers = {
            "User-Agent": "AI-Travel-Planner-StudentProject/1.0 (contact: student@example.com)"
        }
        response = requests.get(WIKI_API, params=params, headers=headers, timeout=8)
        response.raise_for_status()
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if "original" in page_data:
                return page_data["original"]["source"]
        return FALLBACK_IMAGE
    except Exception as e:
        print(f"[image_utils] Failed to fetch image for '{place_name}': {e}")
        return FALLBACK_IMAGE