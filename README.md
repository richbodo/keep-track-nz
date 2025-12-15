# Keep Track NZ - NZ Government News Tracker

## Project info

Starting with a simple site that displays goverment news.  Initial version vibe coded with and hosted on lovable.

**URL**: https://keeptrack.nz

## Deployment (GitHub Pages)

The app is configured to deploy to GitHub Pages using a `gh-pages` branch. Client-side routing uses a `HashRouter` to avoid 404 errors on refresh and the Vite base path is set to `/keep-track-nz/` to ensure assets resolve correctly from the Pages URL.

### Steps

1. Push changes to `main` (or trigger the workflow manually).
2. GitHub Actions workflow `.github/workflows/deploy.yml` will run `npm ci` and `npm run build`, then publish the `dist/` directory to the `gh-pages` branch.
3. In the repository settings, enable GitHub Pages to serve from the `gh-pages` branch (the action will keep that branch updated with the latest build).


