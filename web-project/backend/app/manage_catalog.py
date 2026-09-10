"""CLI for safely adding/removing/listing entries in the shared catalog seed
file (web-project/src/catalogSeed.json) instead of hand-editing JSON.

Usage (from web-project/backend, with the venv active):

    python -m app.manage_catalog list

    python -m app.manage_catalog add --id show-the-office --category show \
        --name "The Office" --image-filename show-the-office.jpg

    python -m app.manage_catalog remove --id show-the-office

After add/remove, restart the backend so SQLite re-seeds from the updated
file (init_database() runs at app startup, see app/__init__.py).
"""
import argparse
import json
import os
import sys

from .config import PUBLIC_IMAGE_DIR, STORAGE_CATEGORIES, WEB_PROJECT_DIR


CATALOG_SEED_PATH = os.path.join(WEB_PROJECT_DIR, 'src', 'catalogSeed.json')


def load_items(seed_path):
    with open(seed_path, encoding='utf-8') as seed_file:
        return json.load(seed_file)


def save_items(seed_path, items):
    with open(seed_path, 'w', encoding='utf-8') as seed_file:
        json.dump(items, seed_file, indent=2)
        seed_file.write('\n')


def cmd_list(args, seed_path=CATALOG_SEED_PATH, image_dir=PUBLIC_IMAGE_DIR):
    items = load_items(seed_path)

    for category in STORAGE_CATEGORIES:
        print(f'{category}:')
        for item in items:
            if item['category'] == category:
                print(f"  {item['id']:<30} {item['name']}")


def cmd_add(args, seed_path=CATALOG_SEED_PATH, image_dir=PUBLIC_IMAGE_DIR):
    if args.category not in STORAGE_CATEGORIES:
        sys.exit(f"Unknown category '{args.category}'. Must be one of: {', '.join(STORAGE_CATEGORIES)}.")

    items = load_items(seed_path)

    if any(item['id'] == args.id for item in items):
        sys.exit(f"An entry with id '{args.id}' already exists. Use a different --id.")

    image_path = os.path.join(image_dir, args.image_filename)
    if not os.path.isfile(image_path):
        sys.exit(
            f'Image file not found: {image_path}\n'
            'Add the image to web-project/public/images/ first, then re-run this command.'
        )

    items.append({
        'id': args.id,
        'category': args.category,
        'name': args.name,
        'description': args.description or '',
        'imageFilename': args.image_filename,
    })
    save_items(seed_path, items)
    print(f"Added '{args.id}' to {args.category}. Restart the backend to apply it.")


def cmd_remove(args, seed_path=CATALOG_SEED_PATH, image_dir=PUBLIC_IMAGE_DIR):
    items = load_items(seed_path)
    remaining = [item for item in items if item['id'] != args.id]

    if len(remaining) == len(items):
        sys.exit(f"No entry with id '{args.id}' found.")

    save_items(seed_path, remaining)
    print(
        f"Removed '{args.id}' from the seed file.\n"
        'Note: an already-running app with an existing database will keep the old row '
        'until you either delete the SQLite file (web-project/backend/instance/taste_catalog.db '
        'by default) or add this id to LEGACY_SEED_IDS in app/catalog.py, then restart.'
    )


def build_parser():
    parser = argparse.ArgumentParser(description='Manage the local catalog seed data.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('list', help='List all catalog entries by category.').set_defaults(func=cmd_list)

    add_parser = subparsers.add_parser('add', help='Add a new catalog entry.')
    add_parser.add_argument('--id', required=True, help="Unique entry id, e.g. 'show-the-office'.")
    add_parser.add_argument('--category', required=True, choices=STORAGE_CATEGORIES)
    add_parser.add_argument('--name', required=True, help="Display name, e.g. 'The Office'.")
    add_parser.add_argument(
        '--image-filename', required=True,
        help='Filename already present in web-project/public/images/.',
    )
    add_parser.add_argument('--description', default='', help='Optional description text.')
    add_parser.set_defaults(func=cmd_add)

    remove_parser = subparsers.add_parser('remove', help='Remove a catalog entry by id.')
    remove_parser.add_argument('--id', required=True)
    remove_parser.set_defaults(func=cmd_remove)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == '__main__':
    main()
