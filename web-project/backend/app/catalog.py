import sqlite3


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
    ('fallback-artist-dream-pop', 'artist', 'Dream Pop', 'Soft color, grain, and late-night synth mood.', 'fallback-artist-dream-pop.jpg'),
    ('fallback-artist-jazz-club', 'artist', 'Jazz Club', 'Warm stage lights with a classic live-session feel.', 'fallback-artist-jazz-club.jpg'),
    ('fallback-artist-indie-rock', 'artist', 'Indie Rock', 'High-contrast guitar texture and poster-wall energy.', 'fallback-artist-indie-rock.jpg'),
    ('fallback-movie-noir', 'movie', 'Neon Noir', 'Cinematic shadows, rain, and saturated city light.', 'fallback-movie-noir.jpg'),
    ('fallback-movie-sunlit', 'movie', 'Sunlit Drama', 'Open skies, warm light, and quiet character-study tone.', 'fallback-movie-sunlit.jpg'),
    ('fallback-movie-sci-fi', 'movie', 'Analog Sci-Fi', 'Clean geometry with a retro-futurist visual palette.', 'fallback-movie-sci-fi.jpg'),
    ('fallback-show-prestige', 'show', 'Prestige Mystery', 'Moody ensemble staging with a slow-burn atmosphere.', 'fallback-show-prestige.jpg'),
    ('fallback-show-comedy', 'show', 'Bright Comedy', 'Playful shapes, crisp color, and upbeat sitcom pacing.', 'fallback-show-comedy.jpg'),
    ('fallback-show-adventure', 'show', 'Adventure Serial', 'Bold landscape forms with serialized cliffhanger energy.', 'fallback-show-adventure.jpg'),
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
    'local-artist',
    'local-movie',
    'local-show',
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
            [(item_id,) for item_id in LEGACY_SEED_IDS],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO catalog_items (id, category, name, description, image_filename)
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
