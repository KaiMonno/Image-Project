from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import ALLOWED_IMAGE_HOSTS, MAX_PROXY_IMAGE_BYTES


class ImageProxyError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def validate_proxy_url(image_url):
    parsed_url = urlparse(image_url)

    if parsed_url.scheme != 'https' or parsed_url.hostname not in ALLOWED_IMAGE_HOSTS:
        raise ImageProxyError('Image host is not allowed.', 400)

    return parsed_url


def fetch_proxy_image(image_url, max_bytes=MAX_PROXY_IMAGE_BYTES):
    validate_proxy_url(image_url)

    try:
        image_request = Request(image_url, headers={'User-Agent': 'TasteCollage/1.0'})
        with urlopen(image_request, timeout=15) as response:
            content_type = response.headers.get_content_type()
            if not content_type.startswith('image/'):
                raise ImageProxyError('The provider did not return an image.', 502)

            content_length = response.headers.get('Content-Length')
            if content_length is not None:
                try:
                    if int(content_length) > max_bytes:
                        raise ImageProxyError('The provider image is too large.', 502)
                except ValueError:
                    pass

            # Read one byte past the limit so an oversized body is caught even
            # when the server omits or understates Content-Length.
            image_bytes = response.read(max_bytes + 1)
            if len(image_bytes) > max_bytes:
                raise ImageProxyError('The provider image is too large.', 502)

            return image_bytes, content_type
    except ImageProxyError:
        raise
    except (HTTPError, URLError, TimeoutError) as error:
        raise ImageProxyError('Could not download the provider image.', 502) from error
