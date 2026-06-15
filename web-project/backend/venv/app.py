from flask import Flask, request, send_file, send_from_directory, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFile
import os
import sqlite3

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
    ('artist-visual', 'artist', 'Neon Headliner', 'Bright, high-energy, and stage-ready.', 'image1.jpeg'),
    ('artist-indie', 'artist', 'Indie Favorite', 'Warm, personal, and a little unexpected.', 'image2.jpg'),
    ('artist-classic', 'artist', 'Classic Icon', 'Timeless taste with a polished edge.', 'image3.jpg'),
    ('movie-dreamy', 'movie', 'Dream Sequence', 'Soft, cinematic, and atmospheric.', 'image1.jpeg'),
    ('movie-action', 'movie', 'Midnight Feature', 'Bold pacing with a dramatic finish.', 'image2.jpg'),
    ('movie-comfort', 'movie', 'Comfort Rewatch', 'Familiar, expressive, and easy to love.', 'image3.jpg'),
    ('show-binge', 'show', 'Weekend Binge', 'A little addictive and full of momentum.', 'image1.jpeg'),
    ('show-prestige', 'show', 'Prestige Pick', 'Carefully made and conversation-worthy.', 'image2.jpg'),
    ('show-comedy', 'show', 'Easy Favorite', 'Reliable, bright, and rewatchable.', 'image3.jpg'),
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
        item_count = connection.execute("SELECT COUNT(*) FROM catalog_items").fetchone()[0]
        if item_count == 0:
            connection.executemany(
                """
                INSERT INTO catalog_items (id, category, name, description, image_filename)
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
    app.run(debug=True)
