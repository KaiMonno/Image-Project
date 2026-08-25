import os


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
