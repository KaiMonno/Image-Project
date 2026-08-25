from PIL import Image, ImageDraw

from .config import BACKGROUND_COLOR, BORDER_COLOR, CARD_SIZE, CIRCLE_CENTER, CIRCLE_RADIUS


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
