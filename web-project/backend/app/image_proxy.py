from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import ALLOWED_IMAGE_HOSTS


class ImageProxyError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def validate_proxy_url(image_url):
    parsed_url = urlparse(image_url)

    if parsed_url.scheme != 'https' or parsed_url.hostname not in ALLOWED_IMAGE_HOSTS:
        raise ImageProxyError('Image host is not allowed.', 400)

    return parsed_url


def fetch_proxy_image(image_url):
    validate_proxy_url(image_url)

    try:
        image_request = Request(image_url, headers={'User-Agent': 'TasteCollage/1.0'})
        with urlopen(image_request, timeout=15) as response:
            content_type = response.headers.get_content_type()
            if not content_type.startswith('image/'):
                raise ImageProxyError('The provider did not return an image.', 502)

            return response.read(), content_type
    except ImageProxyError:
        raise
    except (HTTPError, URLError, TimeoutError) as error:
        raise ImageProxyError('Could not download the provider image.', 502) from error
