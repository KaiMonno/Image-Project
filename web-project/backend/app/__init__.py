import logging
import os

from flask import Flask
from flask_cors import CORS
from PIL import ImageFile

from .catalog import init_database
from .cleanup import cleanup_stale_images
from .config import WEB_PROJECT_DIR, default_app_config, load_environment_file
from .routes import blueprint


def create_app(test_config=None):
    load_environment_file(os.path.join(WEB_PROJECT_DIR, '.env'))

    app = Flask(__name__)
    app.config.update(default_app_config())

    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO)
    CORS(
        app,
        resources={
            r"/*": {
                "origins": app.config['CORS_ALLOWED_ORIGINS'],
            }
        },
    )
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)
    os.makedirs(app.config['STORAGE_DIR'], exist_ok=True)
    init_database(app.config['DATABASE_PATH'])
    cleanup_stale_images(app.config['STORAGE_DIR'], app.config['IMAGE_RETENTION_SECONDS'])

    app.register_blueprint(blueprint)
    return app


app = create_app()
