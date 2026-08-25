# Taste Collage

Taste Collage is a React and Flask application that lets a user choose an
artist, movie, and TV show, then combines the three selected images into one
portrait collage.

The final image follows the design in `Project Concepts`: the artist appears in
a center circle, while the movie and show fill diagonal background regions.

## Features

- Search movie posters and TV show posters through TMDB.
- Search artists and artist images through Spotify.
- Use a curated local catalog when external providers are not configured:
  - Artists: The Weeknd, Olivia Rodrigo, Drake
  - Movies: `2001: A Space Odyssey`, `The Shawshank Redemption`, `The Godfather`
  - Shows: `Planet Earth`, `Avatar: The Last Airbender`, `The Wire`
- Store local catalog metadata in SQLite.
- Proxy external images through Flask to avoid browser CORS problems.
- Generate a `540 x 840` PNG collage with Pillow.
- Keep API credentials on the backend.
- Run the backend through Gunicorn for production-style deployment.
- Restrict CORS to configured frontend origins.
- Keep backend API, provider integrations, image proxying, storage, and collage
  generation in separate modules.
- Test backend behavior with deterministic pytest tests.

## Project Structure

```text
Personal-Project/
├── Project Concepts/              # Original collage design
├── web-project/
│   ├── backend/
│   │   ├── app/                   # Flask app package
│   │   │   ├── routes.py          # API routes
│   │   │   ├── providers.py       # Spotify and TMDB integrations
│   │   │   ├── image_proxy.py     # Provider image proxy validation/fetching
│   │   │   ├── collage.py         # Pillow collage generation
│   │   │   ├── catalog.py         # SQLite catalog setup/loading
│   │   │   └── storage.py         # Uploaded image paths/state
│   │   ├── tests/                 # pytest backend tests
│   │   ├── Procfile               # Deployment start command
│   │   ├── requirements.txt
│   │   └── run.py
│   ├── public/images/             # Curated local catalog images
│   ├── src/                       # React application
│   ├── .env.example               # Provider credential template
│   └── package.json
└── README.md
```

## Requirements

- Node.js and npm
- Python 3.9 or newer
- Flask
- Flask-CORS
- Gunicorn
- Pillow
- pytest
- A TMDB API read access token for movie and show search
- Spotify client credentials for artist search

## Configuration

Create `web-project/.env` using `web-project/.env.example`:

```env
TMDB_API_TOKEN=your_tmdb_api_read_access_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
TASTE_COLLAGE_DATA_DIR=backend/instance
REACT_APP_API_BASE_URL=http://127.0.0.1:5001
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.example.com
```

The application still runs without these credentials, but external search will
show a configuration error and the curated local catalog will remain available.

Set `CORS_ALLOWED_ORIGINS` to the exact deployed frontend origin in production.
Do not leave the backend open to every origin.

Do not commit `.env`. It is ignored by Git.

## Run Locally

Open two terminal windows.

Start the Flask backend:

```bash
cd web-project/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
gunicorn app:app --bind 127.0.0.1:5001
```

Start the React frontend:

```bash
cd web-project
npm install
npm start
```

Open:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://127.0.0.1:5001](http://127.0.0.1:5001)

Restart the Flask backend after adding or changing provider credentials.

For local Flask debug mode only:

```bash
cd web-project/backend
. .venv/bin/activate
python run.py
```

For platforms that read a Procfile, `web-project/backend/Procfile` contains:

```Procfile
web: gunicorn app:app
```

## How It Works

1. React loads the local catalog from `GET /api/catalog`.
2. Without provider credentials, the user can choose from the curated local
   catalog.
3. With provider credentials, the user can search the current category:
   - `artist` searches Spotify.
   - `movie` searches TMDB movies.
   - `show` searches TMDB TV shows.
4. Provider images are fetched through `GET /api/image-proxy`.
5. Each confirmed selection is uploaded to
   `POST /upload-image/<category>`.
6. The first two uploads return `202` with the remaining categories.
7. The third upload generates and returns the final PNG collage.
8. Starting over creates a new local upload session so previous source images
   are not reused accidentally.

## Backend Architecture

- `routes.py` preserves the public API shape and maps failures to useful JSON
  responses.
- `providers.py` owns Spotify/TMDB requests and converts authentication, rate
  limit, network, and malformed JSON failures into provider-specific errors.
- `image_proxy.py` validates that proxied artwork comes from approved HTTPS
  hosts before downloading it.
- `collage.py` contains the current deterministic Pillow pipeline: center crop
  each source image, paste movie/show into diagonal regions, paste the artist
  into the center circle, then draw seams and the outer border.
- `catalog.py` seeds the SQLite catalog with curated local choices and removes
  older placeholder rows when the backend starts.
- `storage.py` keeps upload path and remaining-category logic isolated from
  Flask request handling.
- `app.__init__` exposes `app`, the WSGI application object used by gunicorn.

## Local Catalog

The no-API-key experience is intentionally usable. The bundled catalog uses
local poster-style artwork in `web-project/public/images`:

| Category | Choices |
| --- | --- |
| Artist | The Weeknd, Olivia Rodrigo, Drake |
| Movie | `2001: A Space Odyssey`, `The Shawshank Redemption`, `The Godfather` |
| Show | `Planet Earth`, `Avatar: The Last Airbender`, `The Wire` |

These bundled images are original local assets for the demo catalog, not live
provider artwork. Search results from Spotify/TMDB still use proxied provider
images when credentials are configured.

The current collage algorithm still uses center cropping. The next visual phase
should add a separate crop-analysis module that scores candidate crops before
`collage.py` pastes images into the layout.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/catalog` | Return curated local catalog choices |
| `GET` | `/api/search/<category>?q=<query>` | Search TMDB or Spotify |
| `GET` | `/api/image-proxy?url=<image-url>` | Proxy approved provider images |
| `GET` | `/catalog-images/<filename>` | Serve local catalog images |
| `POST` | `/upload-image/<category>?user_id=<id>` | Save a choice and generate the collage |

## Tests

Run the backend test suite:

```bash
cd web-project/backend
. .venv/bin/activate
pytest
```

Run the React test suite:

```bash
cd web-project
npm test -- --watchAll=false
```

Create a production build:

```bash
cd web-project
npm run build
```

Check the Flask backend syntax:

```bash
python3 -m py_compile web-project/backend/run.py web-project/backend/app/*.py
```

## Deployment Notes

- Do not commit `node_modules`, Python virtual environments, `.env`, SQLite
  databases, generated collages, or Python cache files. The root `.gitignore`
  and `web-project/.gitignore` cover these paths.
- `web-project/backend/Procfile` uses `web: gunicorn app:app`.
- Set `CORS_ALLOWED_ORIGINS` to the exact deployed frontend origin.
- Set `REACT_APP_API_BASE_URL` to the deployed backend URL when building the
  frontend.
- Keep Spotify and TMDB credentials only in the backend environment.

## Current Limitations

- Live external searches require your own TMDB and Spotify credentials.
- Generated images are stored locally and are not associated with user
  accounts.
- The Flask development server is intended for local development only.
- Intelligent crop scoring, text/logo awareness, and layout scoring are planned
  for later phases and are not implemented yet.
