import logging
import os
import time


logger = logging.getLogger(__name__)


def cleanup_stale_images(storage_dir, max_age_seconds):
    """Remove files in storage_dir last modified more than max_age_seconds ago.

    Best-effort: a file that can't be removed (permissions, a concurrent
    delete) is logged and skipped rather than raising, since this runs at
    app startup and shouldn't prevent the app from serving requests.
    """
    if max_age_seconds <= 0 or not os.path.isdir(storage_dir):
        return

    cutoff = time.time() - max_age_seconds
    for filename in os.listdir(storage_dir):
        filepath = os.path.join(storage_dir, filename)
        try:
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)
                logger.info('Removed stale processed image: %s', filepath)
        except OSError as error:
            logger.warning('Could not remove stale image %s: %s', filepath, error)
