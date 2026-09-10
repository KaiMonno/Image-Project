# Deploying to Render

This deploys both pieces of the app from one [render.yaml](render.yaml) Blueprint:
a free Python web service for the Flask backend, and a free static site for
the React frontend.

## Prerequisites

- The repo is pushed to GitHub (already true — `KaiMonno/Image-Project`).
- A Render account connected to that GitHub account (you've used Render before, so this is probably already done).
- Optional: a TMDB API read-access token and Spotify app client ID/secret, if you want live artist/movie/show search instead of just the local catalog.

## 1. Create the Blueprint

1. In the Render dashboard, click **New > Blueprint**.
2. Select the `Image-Project` repo (grant Render access to it if this is the first time).
3. Render reads `render.yaml` from the repo root and shows two services it's about to create:
   - `kaimonno-taste-collage-api` (web service)
   - `kaimonno-taste-collage-web` (static site)
4. **If either name is already taken** by someone else on Render (these are global `*.onrender.com` subdomains), Render will ask you to rename it. If you rename either one, note the new name — you'll need to fix the cross-referenced URLs in step 3 below.
5. Render will prompt you for the three secret environment variables marked `sync: false` in `render.yaml`:
   - `TMDB_API_TOKEN`
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`

   These are optional — leave them blank if you don't have them yet. Without them, `/api/search/...` returns a `provider_not_configured` error and the app falls back to the local catalog, which still works fully. You can add them later from each service's **Environment** tab in the Render dashboard (that doesn't require touching this file) and then manually redeploy.
6. Click **Apply** to create and deploy both services.

## 2. Wait for both builds to finish

- The backend build runs `pip install -r requirements.txt` then starts `gunicorn wsgi:app`.
- The frontend build runs `npm install && npm run build`, publishing the `build/` folder.

Both are visible with live logs in the Render dashboard. The static site typically finishes first.

## 3. If a service name changed

`render.yaml` predicts each service's public URL from its name (e.g. `kaimonno-taste-collage-api` → `https://kaimonno-taste-collage-api.onrender.com`) and hardcodes that URL into the *other* service's environment:

- The API's `CORS_ALLOWED_ORIGINS` points at the frontend's predicted URL.
- The frontend's `REACT_APP_API_BASE_URL` points at the backend's predicted URL.

If Render renamed either service in step 1, these will be wrong. Fix them in the Render dashboard:

1. Open the renamed service (or the *other* service, whichever env var needs updating) → **Environment**.
2. Update `CORS_ALLOWED_ORIGINS` (on the API service) or `REACT_APP_API_BASE_URL` (on the static site) to the actual URL shown at the top of each service's dashboard page.
3. Save. The API just needs a restart (env vars are read at runtime). The static site needs a full **Manual Deploy** (its env var is baked into the JS bundle at build time — a restart alone won't pick up the change).

If neither name collided, skip this step entirely.

## 4. Verify it works

1. Open the frontend's URL (shown on its Render dashboard page, e.g. `https://kaimonno-taste-collage-web.onrender.com`).
2. The first request to the backend after it's been idle will be slow (see "Cold starts" below) — give it 30-60 seconds if the catalog seems stuck on "Loading options...".
3. Once loaded, walk through picking an artist, movie, and show and confirm a collage image comes back.
4. If something fails, check the API service's **Logs** tab in Render first — CORS errors, provider config errors, and upload failures all log there.

## Cold starts (free tier tradeoff)

Render's free web services spin down after 15 minutes of inactivity. The first request after that wakes it back up, which takes roughly 30-60 seconds — the frontend will just show "Loading options..." during that window since `/api/catalog` is the first call it makes. The static site itself (the React app) never sleeps — only the API does.

This is inherent to the free tier; there's no code-level fix. If it bothers you enough to want it gone, the options are: upgrade the API service to a paid instance type (no sleep), or set up a free external uptime pinger (e.g. UptimeRobot) hitting `GET /` on the API every 10 minutes to keep it warm — a common workaround, not something this repo needs to configure.

## Ephemeral storage — expected, not a bug

Neither service has a persistent disk attached, so anything the backend writes to `web-project/backend/instance/` (the SQLite catalog and processed images) is wiped on every restart or redeploy. This is fine for how the app actually works:

- The SQLite catalog is fully re-seeded from `catalogSeed.json` on every startup anyway (see `init_database()`), so losing it on restart is a no-op.
- Uploaded/combined images are only ever handed back to the browser directly in the HTTP response (see `ImageService.js`'s `URL.createObjectURL`) — nothing depends on them still being on the server later. The `IMAGE_RETENTION_HOURS` cleanup job exists for a long-running process, but restarts already clear everything for free.

## Updating the deployed app later

Render auto-deploys on every push to `main` by default (configurable per service under **Settings**). To change an env var (e.g. add TMDB/Spotify credentials later), edit it in that service's **Environment** tab — remember the frontend needs a **Manual Deploy** to pick up a changed `REACT_APP_API_BASE_URL`, while the API just needs a restart.

## Custom domain later

You chose a free `onrender.com` subdomain for now. If you want a custom domain later, it's a **Settings > Custom Domain** addition on the static site's Render dashboard page plus a DNS record at your domain registrar — no changes to this repo's config are needed for that.
