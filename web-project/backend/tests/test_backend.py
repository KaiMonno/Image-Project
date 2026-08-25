from io import BytesIO

import pytest
from PIL import Image

from app import create_app
from app.collage import CARD_SIZE, CollageGenerationError, combine_images, fill_box
from app.image_proxy import ImageProxyError, validate_proxy_url
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
