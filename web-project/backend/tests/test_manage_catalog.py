import json

import pytest

from app.manage_catalog import build_parser, cmd_add, cmd_list, cmd_remove


SEED_ITEMS = [
    {'id': 'artist-drake', 'category': 'artist', 'name': 'Drake', 'description': '', 'imageFilename': 'artist-drake.jpg'},
    {'id': 'movie-godfather', 'category': 'movie', 'name': 'The Godfather', 'description': '', 'imageFilename': 'movie-godfather.jpg'},
]


@pytest.fixture()
def seed_path(tmp_path):
    path = tmp_path / 'catalogSeed.json'
    path.write_text(json.dumps(SEED_ITEMS), encoding='utf-8')
    return str(path)


@pytest.fixture()
def image_dir(tmp_path):
    directory = tmp_path / 'images'
    directory.mkdir()
    (directory / 'show-the-wire.jpg').write_bytes(b'fake-image-bytes')
    return str(directory)


def parse(args):
    return build_parser().parse_args(args)


def test_cmd_add_appends_new_entry(seed_path, image_dir):
    args = parse([
        'add', '--id', 'show-the-wire', '--category', 'show',
        '--name', 'The Wire', '--image-filename', 'show-the-wire.jpg',
    ])

    cmd_add(args, seed_path=seed_path, image_dir=image_dir)

    items = json.loads(open(seed_path, encoding='utf-8').read())
    assert {'id': 'show-the-wire', 'category': 'show', 'name': 'The Wire',
            'description': '', 'imageFilename': 'show-the-wire.jpg'} in items
    assert len(items) == len(SEED_ITEMS) + 1


def test_cmd_add_rejects_duplicate_id(seed_path, image_dir):
    args = parse([
        'add', '--id', 'artist-drake', '--category', 'artist',
        '--name', 'Drake Again', '--image-filename', 'show-the-wire.jpg',
    ])

    with pytest.raises(SystemExit):
        cmd_add(args, seed_path=seed_path, image_dir=image_dir)


def test_cmd_add_rejects_missing_image_file(seed_path, image_dir):
    args = parse([
        'add', '--id', 'show-new', '--category', 'show',
        '--name', 'New Show', '--image-filename', 'does-not-exist.jpg',
    ])

    with pytest.raises(SystemExit):
        cmd_add(args, seed_path=seed_path, image_dir=image_dir)


def test_cmd_remove_deletes_entry(seed_path, image_dir):
    args = parse(['remove', '--id', 'artist-drake'])

    cmd_remove(args, seed_path=seed_path, image_dir=image_dir)

    items = json.loads(open(seed_path, encoding='utf-8').read())
    assert all(item['id'] != 'artist-drake' for item in items)
    assert len(items) == len(SEED_ITEMS) - 1


def test_cmd_remove_rejects_unknown_id(seed_path, image_dir):
    args = parse(['remove', '--id', 'does-not-exist'])

    with pytest.raises(SystemExit):
        cmd_remove(args, seed_path=seed_path, image_dir=image_dir)


def test_cmd_list_runs_without_error(seed_path, image_dir, capsys):
    args = parse(['list'])

    cmd_list(args, seed_path=seed_path, image_dir=image_dir)

    output = capsys.readouterr().out
    assert 'artist-drake' in output
    assert 'movie-godfather' in output
