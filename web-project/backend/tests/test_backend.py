import importlib
import os
import time
from io import BytesIO
from urllib.parse import urlsplit

import pytest
from PIL import Image, ImageDraw

from app import create_app
from app import image_proxy
from app.cleanup import cleanup_stale_images
from app.collage import CARD_SIZE, CollageGenerationError, choose_crop_offset, combine_images, fill_box
from app.image_proxy import ImageProxyError, fetch_proxy_image, validate_proxy_url
from app.providers import ProviderConfigurationError, ProviderRequestError
from app.storage import get_remaining_categories


@pytest.fixture()
def client(tmp_path):
    app = create_app({
        'TESTING': True,
        'DATABASE_PATH': str(tmp_path / 'taste_catalog.db'),
        'STORAGE_DIR': str(tmp_path / 'processed_images'),
    })

    return app.test_client()


def make_image_file(color, size=(120, 180), image_format='PNG'):
    image = Image.new('RGB', size, color)
    output = BytesIO()
    image.save(output, format=image_format)
    output.seek(0)
    return output


def test_importing_app_package_does_not_eagerly_boot_the_app():
    # app/__init__.py must only define create_app(), not call it at module
    # scope -- otherwise importing any submodule (app.config, app.catalog,
    # the manage_catalog CLI, or even pytest collecting this file) would
    # boot a real Flask app against the default instance/ paths as a side
    # effect, including running cleanup_stale_images() against real files.
    # The actual WSGI app instance lives in wsgi.py instead.
    import app as app_package

    importlib.reload(app_package)

    assert not hasattr(app_package, 'app')


def test_search_rejects_invalid_category(client):
    response = client.get('/api/search/book?q=test')

    assert response.status_code == 400
    assert response.get_json()['error'] == 'Unknown category.'


def test_search_rejects_short_query(client):
    response = client.get('/api/search/movie?q=a')

    assert response.status_code == 400
    assert response.get_json()['error'] == 'Enter at least two characters.'


def test_upload_requires_image(client):
    response = client.post('/upload-image/artist?user_id=test-user')

    assert response.status_code == 400
    assert response.get_json()['error'] == 'No image was uploaded.'


def test_upload_rejects_invalid_category(client):
    response = client.post(
        '/upload-image/book?user_id=test-user',
        data={'image': (make_image_file('red'), 'image.png')},
        content_type='multipart/form-data',
    )

    assert response.status_code == 400
    assert response.get_json()['error'] == 'Unknown category.'


def test_upload_rejects_path_traversal_user_id(client, tmp_path):
    response = client.post(
        '/upload-image/artist',
        query_string={'user_id': '../../evil'},
        data={'image': (make_image_file('red'), 'image.png')},
        content_type='multipart/form-data',
    )

    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid user_id.'
    # Confirms the rejection happens before any file write is attempted.
    assert os.listdir(tmp_path / 'processed_images') == []


def test_upload_rejects_corrupted_image(client):
    response = client.post(
        '/upload-image/artist?user_id=test-user',
        data={'image': (BytesIO(b'not an image'), 'image.txt')},
        content_type='multipart/form-data',
    )

    assert response.status_code == 400
    assert response.get_json()['error'] == 'Unsupported or corrupted image file.'


def test_provider_configuration_error_returns_503(client, monkeypatch):
    def fake_search(query, host_url):
        raise ProviderConfigurationError('missing credentials')

    monkeypatch.setattr('app.routes.search_spotify_artists', fake_search)
    response = client.get('/api/search/artist?q=test')

    assert response.status_code == 503
    assert response.get_json()['code'] == 'provider_not_configured'


def test_provider_request_error_returns_502(client, monkeypatch):
    def fake_search(query, category, host_url):
        raise ProviderRequestError('rate limited')

    monkeypatch.setattr('app.routes.search_tmdb', fake_search)
    response = client.get('/api/search/movie?q=test')

    assert response.status_code == 502
    assert response.get_json()['code'] == 'provider_request_failed'


def test_image_proxy_rejects_unapproved_host(client):
    response = client.get('/api/image-proxy?url=https://example.com/poster.jpg')

    assert response.status_code == 400
    assert response.get_json()['error'] == 'Image host is not allowed.'


def test_image_proxy_rejects_non_https_url():
    with pytest.raises(ImageProxyError):
        validate_proxy_url('http://image.tmdb.org/t/p/w500/poster.jpg')


class FakeProxyResponse:
    def __init__(self, body, content_type='image/jpeg', content_length=None):
        self._body = body
        self._content_type = content_type
        self._content_length = content_length

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        if size is None or size < 0:
            data, self._body = self._body, b''
        else:
            data, self._body = self._body[:size], self._body[size:]
        return data

    @property
    def headers(self):
        response = self

        class Headers:
            def get_content_type(self):
                return response._content_type

            def get(self, key, default=None):
                if key == 'Content-Length':
                    return response._content_length
                return default

        return Headers()


def test_fetch_proxy_image_rejects_oversized_content_length(monkeypatch):
    monkeypatch.setattr(
        image_proxy, 'urlopen', lambda *args, **kwargs: FakeProxyResponse(b'small', content_length='999')
    )

    with pytest.raises(ImageProxyError):
        fetch_proxy_image('https://image.tmdb.org/t/p/w500/poster.jpg', max_bytes=10)


def test_fetch_proxy_image_rejects_oversized_body_without_content_length(monkeypatch):
    monkeypatch.setattr(image_proxy, 'urlopen', lambda *args, **kwargs: FakeProxyResponse(b'x' * 20))

    with pytest.raises(ImageProxyError):
        fetch_proxy_image('https://image.tmdb.org/t/p/w500/poster.jpg', max_bytes=10)


def test_fetch_proxy_image_allows_body_within_limit(monkeypatch):
    monkeypatch.setattr(image_proxy, 'urlopen', lambda *args, **kwargs: FakeProxyResponse(b'x' * 5))

    image_bytes, content_type = fetch_proxy_image(
        'https://image.tmdb.org/t/p/w500/poster.jpg', max_bytes=10
    )

    assert image_bytes == b'x' * 5
    assert content_type == 'image/jpeg'


def test_cleanup_stale_images_removes_old_files_only(tmp_path):
    storage_dir = tmp_path / 'processed_images'
    storage_dir.mkdir()

    old_file = storage_dir / 'old-user_combined.png'
    old_file.write_bytes(b'old')
    new_file = storage_dir / 'new-user_combined.png'
    new_file.write_bytes(b'new')

    old_time = time.time() - (48 * 3600)
    os.utime(old_file, (old_time, old_time))

    cleanup_stale_images(str(storage_dir), max_age_seconds=24 * 3600)

    assert not old_file.exists()
    assert new_file.exists()


def test_cleanup_stale_images_is_noop_when_disabled(tmp_path):
    storage_dir = tmp_path / 'processed_images'
    storage_dir.mkdir()

    old_file = storage_dir / 'old-user_combined.png'
    old_file.write_bytes(b'old')
    old_time = time.time() - (48 * 3600)
    os.utime(old_file, (old_time, old_time))

    cleanup_stale_images(str(storage_dir), max_age_seconds=0)

    assert old_file.exists()


def test_missing_uploaded_images_are_reported(tmp_path):
    storage_dir = tmp_path / 'processed_images'
    storage_dir.mkdir()

    remaining = get_remaining_categories(str(storage_dir), ['artist', 'movie', 'show'], 'user-1')

    assert remaining == ['artist', 'movie', 'show']


def test_successful_collage_generation_endpoint(client):
    for category, color in [('artist', 'red'), ('movie', 'blue')]:
        response = client.post(
            f'/upload-image/{category}?user_id=test-user',
            data={'image': (make_image_file(color), f'{category}.png')},
            content_type='multipart/form-data',
        )
        assert response.status_code == 202

    response = client.post(
        '/upload-image/show?user_id=test-user',
        data={'image': (make_image_file('green'), 'show.png')},
        content_type='multipart/form-data',
    )

    assert response.status_code == 200
    assert response.mimetype == 'image/png'

    output = Image.open(BytesIO(response.data))
    assert output.size == CARD_SIZE
    assert output.format == 'PNG'


def test_full_catalog_to_collage_flow_via_http(client):
    """Mirrors the real frontend flow end-to-end at the HTTP layer: load the
    catalog, fetch each selected item's image through the app's own routes
    (not a synthetic image), then upload it — same order and same requests
    QuestionInput.js/ImageService.js make.
    """
    catalog_response = client.get('/api/catalog')
    assert catalog_response.status_code == 200
    catalog = catalog_response.get_json()

    user_id = 'flow-test-user'
    final_response = None

    for category in ('artist', 'movie', 'show'):
        option = catalog[category]['options'][0]
        image_path = urlsplit(option['imageUrl']).path

        image_response = client.get(image_path)
        assert image_response.status_code == 200

        final_response = client.post(
            f'/upload-image/{category}?user_id={user_id}',
            data={'image': (BytesIO(image_response.data), f'{category}.jpg')},
            content_type='multipart/form-data',
        )

    assert final_response.status_code == 200
    assert final_response.mimetype == 'image/png'

    output = Image.open(BytesIO(final_response.data))
    assert output.size == CARD_SIZE
    assert output.format == 'PNG'


def test_uploads_for_different_user_ids_do_not_interfere(client):
    client.post(
        '/upload-image/artist?user_id=user-a',
        data={'image': (make_image_file('red'), 'artist.png')},
        content_type='multipart/form-data',
    )

    response = client.post(
        '/upload-image/movie?user_id=user-b',
        data={'image': (make_image_file('blue'), 'movie.png')},
        content_type='multipart/form-data',
    )

    assert response.status_code == 202
    assert response.get_json()['remainingCategories'] == ['artist', 'show']


def test_combine_images_requires_all_categories():
    with pytest.raises(CollageGenerationError):
        combine_images({'artist': Image.new('RGB', (100, 100), 'red')})


@pytest.mark.parametrize(
    ('source_size', 'target_size'),
    [
        ((300, 100), (100, 100)),
        ((100, 300), (100, 100)),
        ((100, 100), (240, 120)),
    ],
)
def test_fill_box_preserves_target_dimensions_for_aspect_ratios(source_size, target_size):
    output = fill_box(Image.new('RGB', source_size, 'purple'), target_size)

    assert output.size == target_size


def test_choose_crop_offset_centers_when_no_detail_signal():
    # A flat image has no edges anywhere, so smart-crop should fall back to
    # the old always-center behavior instead of drifting to a corner.
    image = Image.new('RGB', (300, 100), 'gray')

    left, top = choose_crop_offset(image, (100, 100))

    assert left == (300 - 100) // 2
    assert top == 0


def test_choose_crop_offset_prefers_the_more_detailed_region():
    # Wide flat image with a busy checkerboard confined to the right third.
    width, height = 300, 100
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    tile = 5
    for x in range(2 * width // 3, width, tile * 2):
        for y in range(0, height, tile * 2):
            draw.rectangle((x, y, x + tile, y + tile), fill='black')

    left, top = choose_crop_offset(image, (100, 100))

    assert left > width // 3  # crop window pulled toward the checkerboard, away from center
    assert top == 0
