import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import config
import logging

logger = logging.getLogger(__name__)

def get_resilient_session():

    session = requests.Session()

    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429,500,502,503,504]
    )

    adapter = HTTPAdapter(max_retries=retry)

    session.mount("https://",adapter)
    session.mount("http://",adapter)

    return session

def extract_data(url):

    session = get_resilient_session()

    try:
        response = session.get(url,timeout=config.TIMEOUT)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"ERROR: {e}")
        return None

