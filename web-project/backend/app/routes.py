import logging
import os

from flask import Blueprint, current_app, jsonify, request, send_file, send_from_directory
from PIL import Image, UnidentifiedImageError

from .catalog import load_catalog
from .collage import CollageGenerationError, combine_image_files
from .image_proxy import ImageProxyError, fetch_proxy_image
from .providers import (
    ProviderConfigurationError,
    ProviderRequestError,
    search_spotify_artists,
    search_tmdb,
)
from .storage import all_images_uploaded, get_category_path, get_remaining_categories


blueprint = Blueprint('taste_collage', __name__)
logger = logging.getLogger(__name__)


@blueprint.route('/api/catalog', methods=['GET'])
def get_catalog():
    catalog = load_catalog(
        current_app.config['DATABASE_PATH'],
        request.host_url,
        current_app.config['STORAGE_CATEGORIES'],
    )
    return jsonify(catalog)


@blueprint.route('/catalog-images/<path:filename>', methods=['GET'])
def get_catalog_image(filename):
    return send_from_directory(current_app.config['PUBLIC_IMAGE_DIR'], filename)


@blueprint.route('/api/search/<category>', methods=['GET'])
def search_external_catalog(category):
    if category not in current_app.config['STORAGE_CATEGORIES']:
        return jsonify(error='Unknown category.'), 400

    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify(error='Enter at least two characters.'), 400

    try:
        if category == 'artist':
            options = search_spotify_artists(query, request.host_url)
        else:
            options = search_tmdb(query, category, request.host_url)
    except ProviderConfigurationError as error:
        logger.info('Provider is not configured: %s', error)
        return jsonify(error=str(error), code='provider_not_configured'), 503
    except ProviderRequestError as error:
        logger.warning('Provider request failed: %s', error)
        return jsonify(error=str(error), code='provider_request_failed'), 502

    return jsonify(options=options)


@blueprint.route('/api/image-proxy', methods=['GET'])
def proxy_external_image():
    image_url = request.args.get('url', '').strip()

    try:
        image_bytes, content_type = fetch_proxy_image(image_url)
    except ImageProxyError as error:
        return jsonify(error=str(error)), error.status_code

    return image_bytes, 200, {
        'Content-Type': content_type,
        'Cache-Control': 'public, max-age=86400',
    }


@blueprint.route('/upload-image/<category>', methods=['POST'])
def upload_image(category):
    categories = current_app.config['STORAGE_CATEGORIES']
    storage_dir = current_app.config['STORAGE_DIR']

    if category not in categories:
        return jsonify(error='Unknown category.'), 400

    if 'image' not in request.files:
        return jsonify(error='No image was uploaded.'), 400

    user_id = request.args.get('user_id', 'default_user').strip() or 'default_user'
    image_file = request.files['image']

    try:
        filepath = get_category_path(storage_dir, user_id, category)
        image = Image.open(image_file.stream)
        image.verify()
        image_file.stream.seek(0)
        Image.open(image_file.stream).convert('RGB').save(filepath, format='PNG')

        if all_images_uploaded(storage_dir, categories, user_id):
            paths_by_category = {
                current_category: get_category_path(storage_dir, user_id, current_category)
                for current_category in categories
            }
            combined_image = combine_image_files(paths_by_category)
            combined_image_path = os.path.join(storage_dir, f'{user_id}_combined.png')
            combined_image.save(combined_image_path, format='PNG', optimize=True)

            return send_file(combined_image_path, mimetype='image/png')
    except UnidentifiedImageError:
        return jsonify(error='Unsupported or corrupted image file.'), 400
    except OSError as error:
        logger.warning('Could not process uploaded image: %s', error)
        return jsonify(error='Could not process the uploaded image.'), 400
    except CollageGenerationError as error:
        logger.exception('Collage generation failed')
        return jsonify(error=str(error)), 500

    return jsonify(
        status='pending',
        savedCategory=category,
        remainingCategories=get_remaining_categories(storage_dir, categories, user_id),
    ), 202


@blueprint.route('/')
def index():
    return 'Welcome to the Flask backend!'
