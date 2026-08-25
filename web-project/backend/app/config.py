import os


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB_PROJECT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, '..'))
PUBLIC_IMAGE_DIR = os.path.join(WEB_PROJECT_DIR, 'public', 'images')
DATA_DIR = os.environ.get('TASTE_COLLAGE_DATA_DIR', os.path.join(BACKEND_DIR, 'instance'))
DATABASE_PATH = os.path.join(DATA_DIR, 'taste_catalog.db')
STORAGE_DIR = os.path.join(DATA_DIR, 'processed_images')

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
DEFAULT_CORS_ORIGINS = ['http://localhost:3000']


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


def default_app_config():
    return {
        'PUBLIC_IMAGE_DIR': PUBLIC_IMAGE_DIR,
        'DATABASE_PATH': DATABASE_PATH,
        'STORAGE_DIR': STORAGE_DIR,
        'STORAGE_CATEGORIES': STORAGE_CATEGORIES,
        'CORS_ALLOWED_ORIGINS': get_allowed_origins(),
    }


def get_allowed_origins():
    raw_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
    origins = [
        origin.strip()
        for origin in raw_origins.split(',')
        if origin.strip()
    ]

    return origins or DEFAULT_CORS_ORIGINS
