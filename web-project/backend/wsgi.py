"""WSGI entrypoint for gunicorn (see Procfile: `gunicorn wsgi:app`).

This is a separate module from app/__init__.py on purpose: create_app()
does real work (creates the instance directory, seeds SQLite, deletes
stale processed images), and Python runs a package's __init__.py as a side
effect of importing *any* of its submodules. If create_app() were called
at the bottom of app/__init__.py instead, that work would fire just from
`from app import create_app` or `from app.config import ...` -- including
from pytest collecting tests, or from running the app.manage_catalog CLI,
neither of which wants the app booted against the real default paths.
"""
from app import create_app


app = create_app()
