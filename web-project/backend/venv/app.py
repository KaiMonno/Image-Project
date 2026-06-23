from flask import Flask, request, send_file, send_from_directory, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFile
import base64
import json
import os
import sqlite3
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

app = Flask(__name__)
CORS(app)
ImageFile.LOAD_TRUNCATED_IMAGES = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
PUBLIC_IMAGE_DIR = os.path.join(PROJECT_DIR, 'public', 'images')
DATABASE_PATH = os.path.join(BASE_DIR, 'taste_catalog.db')
STORAGE_CATEGORIES = ['artist', 'movie', 'show']
CARD_SIZE = (540, 840)
CIRCLE_CENTER = (270, 390)
CIRCLE_RADIUS = 112
BACKGROUND_COLOR = '#d9ecfb'
BORDER_COLOR = '#111827'
TMDB_API_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_URL = 'https://image.tmdb.org/t/p/w500'
SPOTIFY_API_URL = 'https://api.spotify.com/v1'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
ALLOWED_IMAGE_HOSTS = {'image.tmdb.org', 'i.scdn.co', 'mosaic.scdn.co'}
spotify_token_cache = {'access_token': None, 'expires_at': 0}

def load_environment_file(filepath):
    if not os.path.exists(filepath):
        return

    with open(filepath, encoding='utf-8') as environment_file:
        for raw_line in environment_file:
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue

            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

load_environment_file(os.path.join(PROJECT_DIR, '.env'))

CATALOG_DETAILS = {
    'artist': {
        'label': 'Artist',
        'prompt': 'Pick an artist that represents your sound.',
    },
    'movie': {
        'label': 'Movie',
        'prompt': 'Pick a movie that fits your visual taste.',
    },
    'show': {
        'label': 'Show',
        'prompt': 'Pick a show that belongs on your profile.',
    },
}

SEED_CATALOG_ITEMS = [
    ('local-artist', 'artist', 'Local Artist', 'Current local artist image.', 'image1.jpeg'),
    ('local-movie', 'movie', 'Local Movie', 'Current local movie poster.', 'image2.jpg'),
    ('local-show', 'show', 'Local Show', 'Current local show image.', 'image3.jpg'),
]
LEGACY_SEED_IDS = [
    'artist-visual',
    'artist-indie',
    'artist-classic',
    'movie-dreamy',
    'movie-action',
    'movie-comfort',
    'show-binge',
    'show-prestige',
    'show-comedy',
]

storage_dir = os.path.join(BASE_DIR, 'processed_images')
os.makedirs(storage_dir, exist_ok=True)

def get_database_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_database():
    with get_database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS catalog_items (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                image_filename TEXT NOT NULL
            )
            """
        )
        connection.executemany(
            "DELETE FROM catalog_items WHERE id = ?",
            [(item_id,) for item_id in LEGACY_SEED_IDS],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO catalog_items (id, category, name, description, image_filename)
            VALUES (?, ?, ?, ?, ?)
            """,
            SEED_CATALOG_ITEMS,
        )

init_database()

@app.route('/api/catalog', methods=['GET'])
def get_catalog():
    catalog = {
        category: {
            **CATALOG_DETAILS[category],
            'options': [],
        }
        for category in STORAGE_CATEGORIES
    }

    with get_database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, category, name, description, image_filename
            FROM catalog_items
            ORDER BY category, name
            """
        ).fetchall()

    for row in rows:
        if row['category'] not in catalog:
            continue

        catalog[row['category']]['options'].append({
            'id': row['id'],
            'name': row['name'],
            'description': row['description'],
            'imageUrl': f"{request.host_url.rstrip('/')}/catalog-images/{row['image_filename']}",
        })

    return jsonify(catalog)

@app.route('/catalog-images/<path:filename>', methods=['GET'])
def get_catalog_image(filename):
    return send_from_directory(PUBLIC_IMAGE_DIR, filename)

@app.route('/api/search/<category>', methods=['GET'])
def search_external_catalog(category):
    if category not in STORAGE_CATEGORIES:
        return jsonify(error='Unknown category.'), 400

    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify(error='Enter at least two characters.'), 400

    try:
        if category == 'artist':
            options = search_spotify_artists(query)
        else:
            options = search_tmdb(query, category)
    except ProviderConfigurationError as error:
        return jsonify(error=str(error), code='provider_not_configured'), 503
    except ProviderRequestError as error:
        return jsonify(error=str(error), code='provider_request_failed'), 502

    return jsonify(options=options)

@app.route('/api/image-proxy', methods=['GET'])
def proxy_external_image():
    image_url = request.args.get('url', '').strip()
    parsed_url = urlparse(image_url)

    if parsed_url.scheme != 'https' or parsed_url.hostname not in ALLOWED_IMAGE_HOSTS:
        return jsonify(error='Image host is not allowed.'), 400

    try:
        image_request = Request(image_url, headers={'User-Agent': 'TasteCollage/1.0'})
        with urlopen(image_request, timeout=15) as response:
            content_type = response.headers.get_content_type()
            if not content_type.startswith('image/'):
                return jsonify(error='The provider did not return an image.'), 502

            return response.read(), 200, {
                'Content-Type': content_type,
                'Cache-Control': 'public, max-age=86400',
            }
    except (HTTPError, URLError, TimeoutError):
        return jsonify(error='Could not download the provider image.'), 502

class ProviderConfigurationError(Exception):
    pass

class ProviderRequestError(Exception):
    pass

def search_tmdb(query, category):
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
            'imageUrl': build_proxy_url(provider_image_url),
            'provider': 'TMDB',
        })

        if len(options) == 12:
            break

    return options

def search_spotify_artists(query):
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
            'imageUrl': build_proxy_url(images[0]['url']),
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

def build_proxy_url(image_url):
    return f"{request.host_url.rstrip('/')}/api/image-proxy?url={quote(image_url, safe='')}"

@app.route('/upload-image/<category>', methods=['POST'])
def upload_image(category):
    if category not in STORAGE_CATEGORIES:
        return jsonify(error="Unknown category."), 400

    if 'image' not in request.files:
        return jsonify(error="No image was uploaded."), 400

    user_id = request.args.get('user_id', 'default_user')
    image_file = request.files['image']

    try:
        filepath = get_category_path(user_id, category)
        image = Image.open(image_file.stream).convert('RGB')
        image.save(filepath, format='PNG')

        if all_images_uploaded(user_id):
            combined_image = combine_images(user_id)
            combined_image_path = os.path.join(storage_dir, f"{user_id}_combined.png")
            combined_image.save(combined_image_path)

            return send_file(combined_image_path, mimetype='image/png')
    except Exception as error:
        return jsonify(error=str(error)), 500

    return jsonify(
        status="pending",
        savedCategory=category,
        remainingCategories=get_remaining_categories(user_id)
    ), 202

def get_category_path(user_id, category):
    filename = f"{user_id}_{category}.png"
    return os.path.join(storage_dir, filename)

def all_images_uploaded(user_id):
    return not get_remaining_categories(user_id)

def get_remaining_categories(user_id):
    return [
        category
        for category in STORAGE_CATEGORIES
        if not os.path.exists(get_category_path(user_id, category))
    ]

def combine_images(user_id):
    images = {
        category: Image.open(get_category_path(user_id, category)).convert('RGB')
        for category in STORAGE_CATEGORIES
    }

    card = Image.new('RGB', CARD_SIZE, BACKGROUND_COLOR)

    paste_region(
        card,
        images['movie'],
        [
            (0, 0),
            (CARD_SIZE[0], 0),
            (CARD_SIZE[0], CARD_SIZE[1]),
            (CIRCLE_CENTER[0] + 42, CIRCLE_CENTER[1] + 94),
            (CIRCLE_CENTER[0] - 70, CIRCLE_CENTER[1] - 88),
        ],
    )
    paste_region(
        card,
        images['show'],
        [
            (0, 0),
            (CIRCLE_CENTER[0] - 70, CIRCLE_CENTER[1] - 88),
            (CIRCLE_CENTER[0] + 42, CIRCLE_CENTER[1] + 94),
            (CARD_SIZE[0], CARD_SIZE[1]),
            (0, CARD_SIZE[1]),
        ],
    )
    paste_circle(card, images['artist'], CIRCLE_CENTER, CIRCLE_RADIUS)

    draw_borders(card)
    return card

def paste_region(card, source_image, polygon):
    tile = fill_card(source_image)
    mask = Image.new('L', CARD_SIZE, 0)
    ImageDraw.Draw(mask).polygon(polygon, fill=255)
    card.paste(tile, (0, 0), mask)

def paste_circle(card, source_image, center, radius):
    tile_size = radius * 2
    tile = fill_box(source_image, (tile_size, tile_size))
    mask = Image.new('L', (tile_size, tile_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, tile_size - 1, tile_size - 1), fill=255)
    card.paste(tile, (center[0] - radius, center[1] - radius), mask)

def fill_card(image):
    return fill_box(image, CARD_SIZE)

def fill_box(image, size):
    image = image.copy()
    image_ratio = image.width / image.height
    box_ratio = size[0] / size[1]

    if image_ratio > box_ratio:
        new_height = size[1]
        new_width = round(new_height * image_ratio)
    else:
        new_width = size[0]
        new_height = round(new_width / image_ratio)

    image = image.resize((new_width, new_height))
    left = (new_width - size[0]) // 2
    top = (new_height - size[1]) // 2
    return image.crop((left, top, left + size[0], top + size[1]))

def draw_borders(card):
    draw = ImageDraw.Draw(card)
    circle_box = (
        CIRCLE_CENTER[0] - CIRCLE_RADIUS,
        CIRCLE_CENTER[1] - CIRCLE_RADIUS,
        CIRCLE_CENTER[0] + CIRCLE_RADIUS,
        CIRCLE_CENTER[1] + CIRCLE_RADIUS,
    )
    draw.line([(0, 0), (CIRCLE_CENTER[0] - 70, CIRCLE_CENTER[1] - 88)], fill=BORDER_COLOR, width=3)
    draw.line([(CIRCLE_CENTER[0] + 42, CIRCLE_CENTER[1] + 94), CARD_SIZE], fill=BORDER_COLOR, width=3)
    draw.ellipse(circle_box, outline=BORDER_COLOR, width=3)
    draw.rectangle((0, 0, CARD_SIZE[0] - 1, CARD_SIZE[1] - 1), outline=BORDER_COLOR, width=3)

@app.route('/') 
def index(): return 'Welcome to the Flask backend!'

if __name__ == '__main__':
    app.run(debug=True, port=5001)
