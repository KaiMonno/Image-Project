from PIL import Image, ImageDraw, ImageFilter, ImageStat

from .config import BACKGROUND_COLOR, BORDER_COLOR, CARD_SIZE, CIRCLE_CENTER, CIRCLE_RADIUS

# How many candidate crop positions to sample along the overflow axis when
# picking a smart-crop offset. Higher is more precise but slower; 15 is
# plenty for the modest image sizes this app handles.
SMART_CROP_CANDIDATES = 15


class CollageGenerationError(Exception):
    pass


def combine_images(images):
    missing_categories = {'artist', 'movie', 'show'} - set(images)
    if missing_categories:
        missing = ', '.join(sorted(missing_categories))
        raise CollageGenerationError(f'Missing source images: {missing}.')

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


def combine_image_files(paths_by_category):
    try:
        images = {
            category: Image.open(filepath).convert('RGB')
            for category, filepath in paths_by_category.items()
        }
        return combine_images(images)
    except CollageGenerationError:
        raise
    except Exception as error:
        raise CollageGenerationError('Could not generate the collage.') from error


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

    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left, top = choose_crop_offset(image, size)
    return image.crop((left, top, left + size[0], top + size[1]))


def choose_crop_offset(image, size):
    """Pick where to crop along whichever axis has overflow, biasing toward
    the sub-window with the most visual detail (edge density) instead of
    always cutting from the exact center. This is a generic "smart crop"
    heuristic — it has no notion of faces or text, but tends to keep
    busier/more detailed regions (which is usually where a face, a poster's
    subject, or title text ends up) rather than blindly centering.

    `image` must already be sized so at most one axis overflows `size`
    (fill_box guarantees this by resizing the other axis to match exactly).
    """
    max_left = max(image.width - size[0], 0)
    max_top = max(image.height - size[1], 0)

    if max_left == 0 and max_top == 0:
        return 0, 0

    edge_map = image.convert('L').filter(ImageFilter.FIND_EDGES)
    # FIND_EDGES treats the outside of the image as black, so it reports a
    # spurious "edge" along the outermost pixel ring even for a perfectly
    # flat image. Zero that ring out so a flat image ties everywhere (and
    # falls back to the center, per _most_detailed_offset) instead of
    # always preferring whichever candidate happens to touch the border.
    ImageDraw.Draw(edge_map).rectangle((0, 0, edge_map.width - 1, edge_map.height - 1), outline=0, width=1)

    if max_left >= max_top:
        return _most_detailed_offset(edge_map, max_left, size[0], horizontal=True), 0
    return 0, _most_detailed_offset(edge_map, max_top, size[1], horizontal=False)


def _most_detailed_offset(edge_map, max_offset, window_size, horizontal):
    if max_offset == 0:
        return 0

    def score_at(offset):
        if horizontal:
            box = (offset, 0, offset + window_size, edge_map.height)
        else:
            box = (0, offset, edge_map.width, offset + window_size)
        return ImageStat.Stat(edge_map.crop(box)).sum[0]

    # Default to (and tie-break toward) the center crop, so an image with no
    # meaningful edge signal (e.g. a flat background) behaves exactly like
    # the old always-center behavior instead of drifting to an arbitrary
    # corner.
    best_offset = max_offset // 2
    best_score = score_at(best_offset)

    step = max(1, max_offset // SMART_CROP_CANDIDATES)
    # Explicitly include max_offset: range() alone would only land on it by
    # coincidence when it happens to be a multiple of step, otherwise the
    # most extreme valid crop position would never be considered.
    for offset in (*range(0, max_offset, step), max_offset):
        score = score_at(offset)
        if score > best_score:
            best_score = score
            best_offset = offset

    return best_offset


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
