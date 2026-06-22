# Taste Collage

Taste Collage is a React and Flask application that lets a user choose an
artist, movie, and TV show, then combines the three selected images into one
portrait collage.

The final image follows the design in `Project Concepts`: the artist appears in
a center circle, while the movie and show fill diagonal background regions.

## Features

- Search movie posters and TV show posters through TMDB.
- Search artists and artist images through Spotify.
- Use one local fallback image for each category when external providers are
  not configured.
- Store local catalog metadata in SQLite.
- Proxy external images through Flask to avoid browser CORS problems.
- Generate a `540 x 840` PNG collage with Pillow.
- Keep API credentials on the backend.

## Project Structure

```text
Personal-Project/
├── Project Concepts/              # Original collage design
├── web-project/
│   ├── backend/venv/app.py        # Flask API and Pillow image generator
│   ├── public/images/             # Local fallback images
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
- Pillow
- A TMDB API read access token for movie and show search
- Spotify client credentials for artist search

## Configuration

Create `web-project/.env` using `web-project/.env.example`:

```env
TMDB_API_TOKEN=your_tmdb_api_read_access_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

The application still runs without these credentials, but external search will
show a configuration error and only the local fallback choices will be
available.

Do not commit `.env`. It is ignored by Git.

## Run Locally

Open two terminal windows.

Start the Flask backend:

```bash
cd web-project/backend/venv
./bin/python -c "from app import app; app.run(debug=False, port=5001)"
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

## How It Works

1. React loads the local catalog from `GET /api/catalog`.
2. The user can search the current category:
   - `artist` searches Spotify.
   - `movie` searches TMDB movies.
   - `show` searches TMDB TV shows.
3. Provider images are fetched through `GET /api/image-proxy`.
4. Each confirmed selection is uploaded to
   `POST /upload-image/<category>`.
5. The first two uploads return `202` with the remaining categories.
6. The third upload generates and returns the final PNG collage.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/catalog` | Return local fallback choices |
| `GET` | `/api/search/<category>?q=<query>` | Search TMDB or Spotify |
| `GET` | `/api/image-proxy?url=<image-url>` | Proxy approved provider images |
| `GET` | `/catalog-images/<filename>` | Serve local catalog images |
| `POST` | `/upload-image/<category>?user_id=<id>` | Save a choice and generate the collage |

## Tests

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
python3 -m py_compile web-project/backend/venv/app.py
```

## Current Limitations

- Live external searches require your own TMDB and Spotify credentials.
- The local catalog includes only one fallback item per category.
- Generated images are stored locally and are not associated with user
  accounts.
- The Flask development server is intended for local development only.
