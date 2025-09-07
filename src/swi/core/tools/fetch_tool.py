from langchain_core.tools import tool
import requests
from langgraph.config import get_stream_writer
from langgraph.types import  interrupt

from enum import Enum
class FETCH(Enum):
    URL = "fetch_url_content"
    

@tool()
def fetch_url_content(urls: list[str]) -> dict:
    """
    Downloads content from the given list of URLs.

    Args:
        urls (list[str]): List of URLs to fetch.

    Returns:
        dict: A dictionary where keys are URLs and values are either the content or 'not available'.
    """
    results = {}
    writer = get_stream_writer()
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                results[url] = response.text[:1000]  # limit size for safety
                writer(f"Downloaded {url}")
            else:
                results[url] = f"not available (status code {response.status_code})"
                writer(f"not available {url}")
        except Exception as e:
            results[url] = f"not available ({str(e)})"
            writer(f"not available {url}")

    return results


@tool
def ask_user(question:str):
    """
    Clarification from user

    Args:
        question (str): question of clarification to the user
    """
    
    human_response = interrupt(question)
    return human_response