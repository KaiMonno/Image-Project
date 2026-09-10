# Project Handoff

This document describes the current implementation state of the project for the next coding assistant. It is factual to the codebase as it exists now.

## Tech Stack And Architecture

The app is split into a React frontend and a Python/Flask backend under `web-project/`.

Frontend:

- Framework: React 18 via Create React App.
- Main UI: `web-project/src/QuestionInput.js`.
- API helper: `web-project/src/ImageService.js`.
- Runtime API base URL: `web-project/src/config.js`.
- Default backend URL: `http://127.0.0.1:5001`.
- Override variable: `REACT_APP_API_BASE_URL`.
- Local fallback catalog: `web-project/src/tasteCatalog.js`.
- Static images: `web-project/public/images/`.

Backend:

- Framework: Flask.
- App package: `web-project/backend/app/`.
- App factory: `web-project/backend/app/__init__.py`.
- Local dev entry point: `web-project/backend/run.py`.
- Gunicorn import target: `app:app` from `web-project/backend/app/__init__.py`.
- Default backend port for local dev: `5001`.
- Runtime data directory default: `web-project/backend/instance/`.

Backend API routes are defined in `web-project/backend/app/routes.py`:

- `GET /`: simple health/welcome response.
- `GET /api/catalog`: returns the local catalog from SQLite.
- `GET /catalog-images/<filename>`: serves bundled local catalog images from `web-project/public/images/`.
- `GET /api/search/<category>?q=<query>`: searches external providers for `artist`, `movie`, or `show`.
- `GET /api/image-proxy?url=<encoded-url>`: proxies allowed third-party image URLs for browser compatibility.
- `POST /upload-image/<category>?user_id=<id>`: receives selected category images and returns the completed collage once all required categories are uploaded.

The frontend starts at `http://localhost:3000` when using `npm start`. It calls the backend at `REACT_APP_API_BASE_URL` or `http://127.0.0.1:5001` by default. The backend allows CORS origins from `CORS_ALLOWED_ORIGINS`, defaulting to `http://localhost:3000`.

The frontend build process is the standard Create React App build:

```bash
cd web-project
npm run build
```

## Third-Party Integrations

Third-party provider code lives in `web-project/backend/app/providers.py`.

Spotify is used for artist search only:

- Route: `GET /api/search/artist?q=<query>`.
- Credentials:
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`
- Credential source: environment variables loaded from the shell and from `web-project/.env` by `load_environment_file()` in `web-project/backend/app/config.py`.
- Auth flow: Spotify Client Credentials grant.
- Token URL: `https://accounts.spotify.com/api/token`.
- Search URL: `https://api.spotify.com/v1/search`.
- The backend caches the Spotify access token in memory until shortly before expiry.
- Returned artist data includes the artist name, Spotify ID, optional genres as description, and the first Spotify image URL if available.
- Spotify image URLs are wrapped through `/api/image-proxy`.

TMDB is used for movie and television show search:

- Movie route: `GET /api/search/movie?q=<query>`.
- Show route: `GET /api/search/show?q=<query>`.
- Credential:
  - `TMDB_API_TOKEN`
- Credential source: environment variables loaded from the shell and from `web-project/.env`.
- Search URLs:
  - `https://api.themoviedb.org/3/search/movie`
  - `https://api.themoviedb.org/3/search/tv`
- Auth method: bearer token in the `Authorization` header.
- Returned data includes TMDB ID, title/name, optional release year or first-air-date year as description, and poster image URL if available.
- TMDB poster URLs use `https://image.tmdb.org/t/p/w500...` and are wrapped through `/api/image-proxy`.

If provider credentials are missing, the search route returns HTTP `503` with JSON containing `code: "provider_not_configured"`. If credentials are rejected, the provider is rate-limited, or a provider request fails, the route returns an error JSON response, usually HTTP `502` or `503` depending on the condition.

The local catalog still works without Spotify or TMDB credentials. The no-API-key experience is intended to show curated bundled fallback options instead of a broken empty app.

## Image Processing

Image processing is implemented with Pillow in `web-project/backend/app/collage.py`.

The pipeline is triggered when the frontend posts selected images to:

```text
POST /upload-image/<category>?user_id=<id>
```

The expected categories are:

- `artist`
- `movie`
- `show`

For each selected item, the frontend fetches the selected `imageUrl`, converts the response blob to a file, and uploads it as multipart form data with the field name `image`.

The backend then:

1. Validates that the category is one of the configured storage categories.
2. Opens and verifies the uploaded image with Pillow.
3. Converts the image to RGB.
4. Saves it as a PNG named `<user_id>_<category>.png`.
5. Stores it in `web-project/backend/instance/processed_images/` by default.

If not all three category images have been uploaded yet, the backend returns HTTP `202` with pending status and a list of remaining categories.

Once all three category images exist for the same `user_id`, the backend:

1. Loads the saved artist, movie, and show PNGs.
2. Creates a `540x840` RGB canvas.
3. Center-crops and resizes each image with Pillow's Lanczos resampling.
4. Places the movie image into the right/background polygon.
5. Places the show image into the left/background polygon.
6. Places the artist image into a circular crop centered near the upper-middle of the card.
7. Draws dark divider lines, a circular artist border, and an outer border.
8. Saves `<user_id>_combined.png` to the processed images directory.
9. Returns the combined image directly as `image/png`.

The crop behavior is simple center-crop fitting. There is no face detection, saliency detection, logo detection, or text-aware crop logic.

Image proxying is handled in `web-project/backend/app/image_proxy.py`. The proxy only accepts HTTPS URLs whose host is in the configured allowlist:

- `image.tmdb.org`
- `i.scdn.co`
- `mosaic.scdn.co`

The proxy rejects non-image content types. It returns the proxied image bytes with a one-day public cache header. There is currently no explicit maximum download byte limit.

## SQLite Usage

SQLite support lives in `web-project/backend/app/storage.py`. Catalog seed data lives in `web-project/backend/app/catalog.py`.

The SQLite table is `catalog_items` with these columns:

- `id`
- `category`
- `name`
- `description`
- `image_filename`

The database stores local catalog metadata for bundled fallback content. Current seeded catalog entries are:

Artists:

- The Weeknd
- Olivia Rodrigo
- Drake

Movies:

- 2001: A Space Odyssey
- The Shawshank Redemption
- The Godfather

Shows:

- Planet Earth
- Avatar: The Last Airbender
- The Wire

Descriptions for the current seeded entries are blank strings. The current UI does not need descriptions for these local fallback cards.

The database file default is:

```text
web-project/backend/instance/taste_catalog.db
```

That file is generated at runtime by `init_database()` and should not be committed. The seeded static catalog does not need database persistence across restarts because it is recreated deterministically from source code. Uploaded user images and generated combined images are stored on the local filesystem under `backend/instance/processed_images`; those files would need persistent storage only if a deployment is expected to preserve in-progress or generated collages across restarts.

## How To Run Locally

Install and run the backend:

```bash
cd web-project/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
gunicorn app:app --bind 127.0.0.1:5001
```

For local Flask debug mode, this also works:

```bash
cd web-project/backend
. .venv/bin/activate
python run.py
```

Install and run the frontend:

```bash
cd web-project
npm install
npm start
```

The frontend will be available at:

```text
http://localhost:3000
```

The backend will be available at:

```text
http://127.0.0.1:5001
```

Environment variables can be set in the shell or in:

```text
web-project/.env
```

Useful variables:

```bash
TMDB_API_TOKEN=your_tmdb_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
TASTE_COLLAGE_DATA_DIR=backend/instance
REACT_APP_API_BASE_URL=http://127.0.0.1:5001
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.example.com
```

Spotify and TMDB credentials are optional for the local fallback catalog, but external search will return provider configuration errors without them.

## Current State

There is some minimal deployment configuration already present:

- `web-project/backend/Procfile`
- `gunicorn==22.0.0` in `web-project/backend/requirements.txt`
- Gunicorn app target exposed as `app:app`

There is no Dockerfile in the current repository. There is also no platform-specific hosting configuration found in the inspected project files, such as `.openai/hosting.json`.

There is an automated test suite already present:

- Backend pytest tests: `web-project/backend/tests/test_backend.py`
- Frontend Create React App test: `web-project/src/App.test.js`

The backend tests cover several route and image-processing behaviors, but they should be treated as a starting point rather than a complete deployment-readiness suite.

## Known Issues Or Incomplete Pieces

- The image cropper uses simple center crop logic, so faces, posters, logos, and title text may be cropped awkwardly.
- Uploaded and generated images are stored on the local filesystem with no cleanup job.
- Runtime image storage has no authentication or per-user access control beyond the generated `user_id` naming convention.
- The image proxy validates scheme, hostname, and content type, but it does not enforce a maximum response size.
- The frontend fallback catalog duplicates backend seed data, so the two can drift if one is updated without the other.
- `CORS_ALLOWED_ORIGINS` defaults to localhost only; deployed frontend origins need to be configured explicitly.
- Provider search uses synchronous `urllib` requests inside Flask handlers.
- The SQLite catalog is static seeded data. There is no admin UI or API for editing catalog entries.
- A local `web-project/.env` file exists on disk. It should remain ignored and should not be committed.
- Basic tests exist, but there is no comprehensive end-to-end test suite for the full React-to-Flask image selection and collage flow.
