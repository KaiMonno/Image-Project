import os
import re


# user_id comes straight from a request query param and is used to build a
# filesystem path (get_category_path), so it must be restricted to a safe
# charset. Without this, a value like '../../etc/passwd' would let a caller
# write (and later read back, via the combine step) files outside
# storage_dir. crypto.randomUUID() (the frontend's id) and the legacy
# timestamp+random-string format both match this pattern.
USER_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,128}$')


def is_valid_user_id(user_id):
    return bool(USER_ID_PATTERN.match(user_id))


def get_category_path(storage_dir, user_id, category):
    filename = f"{user_id}_{category}.png"
    return os.path.join(storage_dir, filename)


def get_remaining_categories(storage_dir, categories, user_id):
    return [
        category
        for category in categories
        if not os.path.exists(get_category_path(storage_dir, user_id, category))
    ]


def all_images_uploaded(storage_dir, categories, user_id):
    return not get_remaining_categories(storage_dir, categories, user_id)
