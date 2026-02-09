import requests


def extract_drap_data(url, session: requests.Session = requests.Session()):
    """Extract DRAP data from the given URL."""
    response = session.get(url)
    response.raise_for_status()  # Ensure we notice bad responses
    return response.text
