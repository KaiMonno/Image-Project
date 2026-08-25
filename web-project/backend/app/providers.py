import base64
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .config import SPOTIFY_API_URL, SPOTIFY_TOKEN_URL, TMDB_API_URL, TMDB_IMAGE_URL


spotify_token_cache = {'access_token': None, 'expires_at': 0}


class ProviderConfigurationError(Exception):
    pass


class ProviderRequestError(Exception):
    pass


def build_proxy_url(image_url, host_url):
    return f"{host_url.rstrip('/')}/api/image-proxy?url={quote(image_url, safe='')}"


def search_tmdb(query, category, host_url):
    api_token = os.environ.get('TMDB_API_TOKEN')
    if not api_token:
        raise ProviderConfigurationError(
            'TMDB_API_TOKEN is required to search movies and shows.'
        )

    media_type = 'movie' if category == 'movie' else 'tv'
    payload = fetch_json(
        f"{TMDB_API_URL}/search/{media_type}?{urlencode({'query': query, 'include_adult': 'false'})}",
        headers={'Authorization': f'Bearer {api_token}'},
    )

    options = []
    for item in payload.get('results', []):
        poster_path = item.get('poster_path')
        if not poster_path:
            continue

        name = item.get('title') if category == 'movie' else item.get('name')
        date = item.get('release_date') if category == 'movie' else item.get('first_air_date')
        year = date[:4] if date else 'Date unavailable'
        provider_image_url = f"{TMDB_IMAGE_URL}{poster_path}"
        options.append({
            'id': f"tmdb-{category}-{item['id']}",
            'name': name or 'Untitled',
            'description': year,
            'imageUrl': build_proxy_url(provider_image_url, host_url),
            'provider': 'TMDB',
        })

        if len(options) == 12:
            break

    return options


def search_spotify_artists(query, host_url):
    token = get_spotify_access_token()
    payload = fetch_json(
        f"{SPOTIFY_API_URL}/search?{urlencode({'q': query, 'type': 'artist', 'limit': 10})}",
        headers={'Authorization': f'Bearer {token}'},
    )

    options = []
    for item in payload.get('artists', {}).get('items', []):
        images = item.get('images', [])
        if not images:
            continue

        genres = item.get('genres', [])
        description = ', '.join(genres[:2]) if genres else 'Artist'
        options.append({
            'id': f"spotify-artist-{item['id']}",
            'name': item.get('name', 'Unknown artist'),
            'description': description,
            'imageUrl': build_proxy_url(images[0]['url'], host_url),
            'provider': 'Spotify',
        })

    return options


def get_spotify_access_token():
    now = time.time()
    if (
        spotify_token_cache['access_token']
        and spotify_token_cache['expires_at'] > now + 30
    ):
        return spotify_token_cache['access_token']

    client_id = os.environ.get('SPOTIFY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
    if not client_id or not client_secret:
        raise ProviderConfigurationError(
            'SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are required to search artists.'
        )

    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode('utf-8')
    ).decode('ascii')
    token_request = Request(
        SPOTIFY_TOKEN_URL,
        data=urlencode({'grant_type': 'client_credentials'}).encode('utf-8'),
        headers={
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method='POST',
    )

    try:
        with urlopen(token_request, timeout=15) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise ProviderRequestError('Spotify authentication failed.') from error

    spotify_token_cache['access_token'] = payload['access_token']
    spotify_token_cache['expires_at'] = now + payload.get('expires_in', 3600)
    return spotify_token_cache['access_token']


def fetch_json(url, headers=None):
    api_request = Request(
        url,
        headers={
            'Accept': 'application/json',
            'User-Agent': 'TasteCollage/1.0',
            **(headers or {}),
        },
    )

    try:
        with urlopen(api_request, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code in (401, 403):
            message = 'The provider rejected the configured credentials.'
        elif error.code == 429:
            message = 'The provider rate limit was reached. Try again shortly.'
        else:
            message = 'The provider search request failed.'
        raise ProviderRequestError(message) from error
    except (URLError, TimeoutError, ValueError) as error:
        raise ProviderRequestError('Could not reach the image provider.') from error
