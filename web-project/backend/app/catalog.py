import json
import os
import sqlite3

from .config import WEB_PROJECT_DIR


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

# The frontend's fallback catalog (web-project/src/tasteCatalog.js) reads the
# same file, so this is the single source of truth for which items exist.
CATALOG_SEED_PATH = os.path.join(WEB_PROJECT_DIR, 'src', 'catalogSeed.json')


def _load_seed_items(seed_path):
    with open(seed_path, encoding='utf-8') as seed_file:
        raw_items = json.load(seed_file)

    return [
        (item['id'], item['category'], item['name'], item.get('description', ''), item['imageFilename'])
        for item in raw_items
    ]


SEED_CATALOG_ITEMS = _load_seed_items(CATALOG_SEED_PATH)

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
    'local-artist',
    'local-movie',
    'local-show',
    'fallback-artist-dream-pop',
    'fallback-artist-jazz-club',
    'fallback-artist-indie-rock',
    'fallback-movie-noir',
    'fallback-movie-sunlit',
    'fallback-movie-sci-fi',
    'fallback-show-prestige',
    'fallback-show-comedy',
    'fallback-show-adventure',
]


def get_database_connection(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_database(database_path):
    with get_database_connection(database_path) as connection:
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
            [(item_id,) for item_id in [*LEGACY_SEED_IDS, *[item[0] for item in SEED_CATALOG_ITEMS]]],
        )
        connection.executemany(
            """
            INSERT INTO catalog_items (id, category, name, description, image_filename)
            VALUES (?, ?, ?, ?, ?)
            """,
            SEED_CATALOG_ITEMS,
        )


def load_catalog(database_path, host_url, categories):
    catalog = {
        category: {
            **CATALOG_DETAILS[category],
            'options': [],
        }
        for category in categories
    }

    with get_database_connection(database_path) as connection:
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
            'imageUrl': f"{host_url.rstrip('/')}/catalog-images/{row['image_filename']}",
        })

    return catalog
